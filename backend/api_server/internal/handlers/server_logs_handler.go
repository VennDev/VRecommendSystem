package handlers

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/gofiber/fiber/v3"
)

type ServerLogEntry struct {
	Timestamp string `json:"timestamp"`
	Level     string `json:"level"`
	Message   string `json:"message"`
	Server    string `json:"server"`
	Raw       string `json:"raw"`
}

const serverLogsBaseDir = "logs"

func parseLogLine(line, serverName string) ServerLogEntry {
	line = strings.TrimSpace(line)
	if line == "" {
		return ServerLogEntry{}
	}

	entry := ServerLogEntry{
		Server:    serverName,
		Raw:       line,
		Timestamp: time.Now().Format(time.RFC3339),
		Level:     "INFO",
		Message:   line,
	}

	var jsonLog map[string]interface{}
	if err := json.Unmarshal([]byte(line), &jsonLog); err == nil {
		if ts, ok := jsonLog["timestamp"].(string); ok {
			entry.Timestamp = ts
		} else if ts, ok := jsonLog["time"].(string); ok {
			entry.Timestamp = ts
		} else if ts, ok := jsonLog["@timestamp"].(string); ok {
			entry.Timestamp = ts
		}

		if level, ok := jsonLog["level"].(string); ok {
			entry.Level = strings.ToUpper(level)
		} else if level, ok := jsonLog["severity"].(string); ok {
			entry.Level = strings.ToUpper(level)
		}

		if msg, ok := jsonLog["message"].(string); ok {
			entry.Message = msg
		} else if msg, ok := jsonLog["msg"].(string); ok {
			entry.Message = msg
		} else {
			prettyJSON, _ := json.Marshal(jsonLog)
			entry.Message = string(prettyJSON)
		}
	} else {
		parts := strings.SplitN(line, " ", 4)

		if len(parts) >= 3 {
			if _, err := time.Parse(time.RFC3339, parts[0]); err == nil {
				entry.Timestamp = parts[0]

				levelStr := strings.ToUpper(strings.Trim(parts[1], "[]"))
				if levelStr == "ERROR" || levelStr == "WARN" || levelStr == "WARNING" ||
				   levelStr == "INFO" || levelStr == "DEBUG" {
					entry.Level = levelStr
					if len(parts) >= 3 {
						entry.Message = strings.Join(parts[2:], " ")
					}
				} else {
					entry.Message = strings.Join(parts[1:], " ")
				}
			} else if strings.HasPrefix(parts[0], "[") {
				levelStr := strings.ToUpper(strings.Trim(parts[0], "[]"))
				if levelStr == "ERROR" || levelStr == "WARN" || levelStr == "WARNING" ||
				   levelStr == "INFO" || levelStr == "DEBUG" {
					entry.Level = levelStr
					entry.Message = strings.Join(parts[1:], " ")
				}
			}
		}
	}

	if entry.Level == "WARN" {
		entry.Level = "WARNING"
	}

	return entry
}

func readServerLogFile(filePath, serverName string, limit int) ([]ServerLogEntry, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var lines []string
	scanner := bufio.NewScanner(file)

	const maxCapacity = 1024 * 1024
	buf := make([]byte, maxCapacity)
	scanner.Buffer(buf, maxCapacity)

	for scanner.Scan() {
		line := scanner.Text()
		if strings.TrimSpace(line) != "" {
			lines = append(lines, line)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	if len(lines) > limit {
		lines = lines[len(lines)-limit:]
	}

	var entries []ServerLogEntry
	for _, line := range lines {
		entry := parseLogLine(line, serverName)
		if entry.Message != "" {
			entries = append(entries, entry)
		}
	}

	return entries, nil
}

func GetServerLogs(c fiber.Ctx) error {
	limitStr := c.Query("limit", "100")
	var limit int
	if _, err := fmt.Sscanf(limitStr, "%d", &limit); err != nil || limit <= 0 {
		limit = 100
	}
	if limit > 1000 {
		limit = 1000
	}

	server := c.Query("server", "all")

	var allLogs []ServerLogEntry

	if server == "all" || server == "api_server" {
		apiLogPath := filepath.Join(serverLogsBaseDir, "api_server.log")
		if logs, err := readServerLogFile(apiLogPath, "api_server", limit); err == nil {
			allLogs = append(allLogs, logs...)
		}
	}

	if server == "all" || server == "ai_server" {
		aiLogPath := filepath.Join(serverLogsBaseDir, "ai_server.log")
		if logs, err := readServerLogFile(aiLogPath, "ai_server", limit); err == nil {
			allLogs = append(allLogs, logs...)
		}
	}

	sort.Slice(allLogs, func(i, j int) bool {
		ti, _ := time.Parse(time.RFC3339, allLogs[i].Timestamp)
		tj, _ := time.Parse(time.RFC3339, allLogs[j].Timestamp)
		return ti.After(tj)
	})

	if len(allLogs) > limit {
		allLogs = allLogs[:limit]
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    allLogs,
		"count":   len(allLogs),
	})
}
