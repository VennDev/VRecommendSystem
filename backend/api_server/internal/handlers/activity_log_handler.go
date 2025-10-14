package handlers

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/gofiber/fiber/v3"
)

type ActivityLogEntry struct {
	ID           string                 `json:"id"`
	UserID       string                 `json:"user_id"`
	UserEmail    string                 `json:"user_email"`
	Action       string                 `json:"action"`
	ResourceType string                 `json:"resource_type,omitempty"`
	ResourceID   string                 `json:"resource_id,omitempty"`
	Details      map[string]interface{} `json:"details"`
	UserAgent    string                 `json:"user_agent"`
	IPAddress    string                 `json:"ip_address,omitempty"`
	CreatedAt    string                 `json:"created_at"`
}

type LogFileData struct {
	Date string              `json:"date"`
	Logs []ActivityLogEntry  `json:"logs"`
}

const logsBaseDir = "user_logs"

func getLogFilePath(userID, date string) string {
	userDir := filepath.Join(logsBaseDir, userID)
	return filepath.Join(userDir, fmt.Sprintf("%s.json", date))
}

func ensureUserLogDir(userID string) error {
	userDir := filepath.Join(logsBaseDir, userID)
	return os.MkdirAll(userDir, 0755)
}

func readLogFile(filePath string) ([]ActivityLogEntry, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return []ActivityLogEntry{}, nil
		}
		return nil, err
	}

	var logFile LogFileData
	if err := json.Unmarshal(data, &logFile); err != nil {
		return nil, err
	}

	return logFile.Logs, nil
}

func writeLogFile(filePath, date string, logs []ActivityLogEntry) error {
	logFile := LogFileData{
		Date: date,
		Logs: logs,
	}

	data, err := json.MarshalIndent(logFile, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filePath, data, 0644)
}

func CreateActivityLog(c fiber.Ctx) error {
	var logEntry ActivityLogEntry

	if err := c.Bind().JSON(&logEntry); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if logEntry.UserID == "" || logEntry.UserEmail == "" || logEntry.Action == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Missing required fields: user_id, user_email, action",
		})
	}

	now := time.Now()
	date := now.Format("2006-01-02")

	logEntry.ID = fmt.Sprintf("%d-%s", now.UnixNano(), logEntry.UserID)
	logEntry.CreatedAt = now.Format(time.RFC3339)
	logEntry.IPAddress = c.IP()

	if err := ensureUserLogDir(logEntry.UserID); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to create log directory",
		})
	}

	filePath := getLogFilePath(logEntry.UserID, date)

	logs, err := readLogFile(filePath)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read log file",
		})
	}

	logs = append(logs, logEntry)

	if err := writeLogFile(filePath, date, logs); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to write log file",
		})
	}

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"data":    logEntry,
	})
}

func GetUserActivityLogs(c fiber.Ctx) error {
	userID := c.Query("user_id")
	if userID == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "user_id query parameter is required",
		})
	}

	limitStr := c.Query("limit", "50")
	var limit int
	fmt.Sscanf(limitStr, "%d", &limit)
	if limit <= 0 {
		limit = 50
	}

	userDir := filepath.Join(logsBaseDir, userID)
	if _, err := os.Stat(userDir); os.IsNotExist(err) {
		return c.JSON(fiber.Map{
			"success": true,
			"data":    []ActivityLogEntry{},
		})
	}

	entries, err := os.ReadDir(userDir)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read user logs directory",
		})
	}

	var allLogs []ActivityLogEntry
	var fileNames []string

	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".json" {
			fileNames = append(fileNames, entry.Name())
		}
	}

	sort.Sort(sort.Reverse(sort.StringSlice(fileNames)))

	for _, fileName := range fileNames {
		filePath := filepath.Join(userDir, fileName)
		logs, err := readLogFile(filePath)
		if err != nil {
			continue
		}
		allLogs = append(allLogs, logs...)
	}

	sort.Slice(allLogs, func(i, j int) bool {
		return allLogs[i].CreatedAt > allLogs[j].CreatedAt
	})

	if len(allLogs) > limit {
		allLogs = allLogs[:limit]
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    allLogs,
	})
}

func GetAllRecentActivityLogs(c fiber.Ctx) error {
	limitStr := c.Query("limit", "50")
	var limit int
	fmt.Sscanf(limitStr, "%d", &limit)
	if limit <= 0 {
		limit = 50
	}

	if _, err := os.Stat(logsBaseDir); os.IsNotExist(err) {
		return c.JSON(fiber.Map{
			"success": true,
			"data":    []ActivityLogEntry{},
		})
	}

	userDirs, err := os.ReadDir(logsBaseDir)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read logs directory",
		})
	}

	var allLogs []ActivityLogEntry

	for _, userDir := range userDirs {
		if !userDir.IsDir() {
			continue
		}

		userPath := filepath.Join(logsBaseDir, userDir.Name())
		files, err := os.ReadDir(userPath)
		if err != nil {
			continue
		}

		var fileNames []string
		for _, file := range files {
			if !file.IsDir() && filepath.Ext(file.Name()) == ".json" {
				fileNames = append(fileNames, file.Name())
			}
		}

		sort.Sort(sort.Reverse(sort.StringSlice(fileNames)))

		for _, fileName := range fileNames {
			filePath := filepath.Join(userPath, fileName)
			logs, err := readLogFile(filePath)
			if err != nil {
				continue
			}
			allLogs = append(allLogs, logs...)
		}
	}

	sort.Slice(allLogs, func(i, j int) bool {
		return allLogs[i].CreatedAt > allLogs[j].CreatedAt
	})

	if len(allLogs) > limit {
		allLogs = allLogs[:limit]
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    allLogs,
	})
}

func GetActivityLogsByResource(c fiber.Ctx) error {
	resourceType := c.Query("resource_type")
	resourceID := c.Query("resource_id")

	if resourceType == "" || resourceID == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "resource_type and resource_id query parameters are required",
		})
	}

	limitStr := c.Query("limit", "20")
	var limit int
	fmt.Sscanf(limitStr, "%d", &limit)
	if limit <= 0 {
		limit = 20
	}

	if _, err := os.Stat(logsBaseDir); os.IsNotExist(err) {
		return c.JSON(fiber.Map{
			"success": true,
			"data":    []ActivityLogEntry{},
		})
	}

	userDirs, err := os.ReadDir(logsBaseDir)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read logs directory",
		})
	}

	var matchingLogs []ActivityLogEntry

	for _, userDir := range userDirs {
		if !userDir.IsDir() {
			continue
		}

		userPath := filepath.Join(logsBaseDir, userDir.Name())
		files, err := os.ReadDir(userPath)
		if err != nil {
			continue
		}

		for _, file := range files {
			if file.IsDir() || filepath.Ext(file.Name()) != ".json" {
				continue
			}

			filePath := filepath.Join(userPath, file.Name())
			logs, err := readLogFile(filePath)
			if err != nil {
				continue
			}

			for _, log := range logs {
				if log.ResourceType == resourceType && log.ResourceID == resourceID {
					matchingLogs = append(matchingLogs, log)
				}
			}
		}
	}

	sort.Slice(matchingLogs, func(i, j int) bool {
		return matchingLogs[i].CreatedAt > matchingLogs[j].CreatedAt
	})

	if len(matchingLogs) > limit {
		matchingLogs = matchingLogs[:limit]
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    matchingLogs,
	})
}

func ExportUserActivityLogs(c fiber.Ctx) error {
	userID := c.Query("user_id")
	if userID == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "user_id query parameter is required",
		})
	}

	userDir := filepath.Join(logsBaseDir, userID)
	if _, err := os.Stat(userDir); os.IsNotExist(err) {
		return c.JSON([]ActivityLogEntry{})
	}

	entries, err := os.ReadDir(userDir)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read user logs directory",
		})
	}

	var allLogs []ActivityLogEntry
	var fileNames []string

	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".json" {
			fileNames = append(fileNames, entry.Name())
		}
	}

	sort.Sort(sort.Reverse(sort.StringSlice(fileNames)))

	for _, fileName := range fileNames {
		filePath := filepath.Join(userDir, fileName)
		logs, err := readLogFile(filePath)
		if err != nil {
			continue
		}
		allLogs = append(allLogs, logs...)
	}

	sort.Slice(allLogs, func(i, j int) bool {
		return allLogs[i].CreatedAt > allLogs[j].CreatedAt
	})

	return c.JSON(allLogs)
}
