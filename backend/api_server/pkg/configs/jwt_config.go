package configs

import (
	"os"
	"strconv"
)

type JWTConfigResult struct {
	SecretKey                      string
	RefreshKey                     string
	SecretKeyExpirationMinsCount   int
	RefreshKeyExpirationHoursCount int
}

func JWTConfig() *JWTConfigResult {
	secretKey := os.Getenv("JWT_SECRET_KEY")
	refreshKey := os.Getenv("JWT_REFRESH_KEY")
	secretKeyExpirationMinsCount, error := strconv.Atoi(os.Getenv("JWT_SECRET_KEY_EXPIRATION_MINS_COUNT"))
	if error != nil {
		panic("Failed to parse JWT_SECRET_KEY_EXPIRATION_MINS_COUNT: " + error.Error())
	}
	refreshKeyExpirationHoursCount, error := strconv.Atoi(os.Getenv("JWT_REFRESH_KEY_EXPIRATION_HOURS_COUNT"))
	if error != nil {
		panic("Failed to parse JWT_REFRESH_KEY_EXPIRATION_HOURS_COUNT: " + error.Error())
	}
	return &JWTConfigResult{
		SecretKey:                      secretKey,
		RefreshKey:                     refreshKey,
		SecretKeyExpirationMinsCount:   secretKeyExpirationMinsCount,
		RefreshKeyExpirationHoursCount: refreshKeyExpirationHoursCount,
	}
}
