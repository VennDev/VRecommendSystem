package initialize

import (
	"fmt"
	vp "github.com/spf13/viper"
	"github.com/venndev/vrecommendation/global"
	"path/filepath"
	"sort"
)

func LoadConfig() error {
	viper := vp.New()
	configDir := "./config/"

	patterns := []string{"*.yml", "*.yaml"}
	var allFiles []string

	for _, pattern := range patterns {
		files, err := filepath.Glob(filepath.Join(configDir, pattern))
		if err != nil {
			return fmt.Errorf("failed to search for %s files: %w", pattern, err)
		}
		allFiles = append(allFiles, files...)
	}

	if len(allFiles) == 0 {
		return fmt.Errorf("no YAML files found in directory: %s", configDir)
	}

	sort.Strings(allFiles)

	viper.SetConfigFile(allFiles[0])
	if err := viper.ReadInConfig(); err != nil {
		return fmt.Errorf("failed to read config file %s: %w", allFiles[0], err)
	}

	fmt.Printf("Loaded primary config: %s\n", filepath.Base(allFiles[0]))

	var mergeErrors []string
	for i := 1; i < len(allFiles); i++ {
		viper.SetConfigFile(allFiles[i])
		if err := viper.MergeInConfig(); err != nil {
			errorMsg := fmt.Sprintf("failed to merge %s: %v", filepath.Base(allFiles[i]), err)
			mergeErrors = append(mergeErrors, errorMsg)
			fmt.Printf("Warning: %s\n", errorMsg)
		} else {
			fmt.Printf("Merged config: %s\n", filepath.Base(allFiles[i]))
		}
	}

	if err := viper.Unmarshal(&global.Config); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	if len(mergeErrors) > 0 {
		fmt.Printf("Some config files could not be merged: %d errors\n", len(mergeErrors))
	}

	return nil
}
