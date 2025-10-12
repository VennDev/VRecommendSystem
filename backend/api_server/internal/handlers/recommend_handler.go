package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
	redisClient "github.com/venndev/vrecommendation/pkg/redis"
)

func Recommend(c fiber.Ctx) error {
	userId := c.Query("user_id")
	modelId := c.Query("model_id")
	n := c.Query("n", "10")

	if userId == "" || modelId == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "user_id and model_id are required query parameters",
		})
	}

	cacheKey := fmt.Sprintf("recommend:%s:%s:%s", userId, modelId, n)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	redis := redisClient.GetRedisClient()
	if redis != nil {
		cachedData, err := redis.Get(ctx, cacheKey)
		if err == nil && cachedData != "" {
			global.Logger.Info(fmt.Sprintf("Cache hit for key: %s", cacheKey))

			var result map[string]interface{}
			if err := json.Unmarshal([]byte(cachedData), &result); err == nil {
				return c.JSON(result)
			}
		}
	}

	aiServerUrl := fmt.Sprintf("http://localhost:9999/api/v1/recommend/%s/%s/%s", userId, modelId, n)

	req, err := http.NewRequestWithContext(ctx, "GET", aiServerUrl, nil)
	if err != nil {
		global.Logger.Error("Failed to create request to AI server", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to create request to AI server",
		})
	}

	token := c.Get("Authorization")
	if token != "" {
		req.Header.Set("Authorization", token)
	}

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		global.Logger.Error("Failed to fetch recommendations from AI server", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to fetch recommendations from AI server",
		})
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		global.Logger.Error("Failed to read AI server response", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to read AI server response",
		})
	}

	if resp.StatusCode != http.StatusOK {
		return c.Status(resp.StatusCode).JSON(fiber.Map{
			"error": string(body),
		})
	}

	if redis != nil {
		cacheCtx, cacheCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cacheCancel()

		if err := redis.Set(cacheCtx, cacheKey, string(body), 5*time.Minute); err != nil {
			global.Logger.Error("Failed to cache recommendation", err)
		} else {
			global.Logger.Info(fmt.Sprintf("Cached recommendation for key: %s", cacheKey))
		}
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to parse AI server response",
		})
	}

	return c.JSON(result)
}
