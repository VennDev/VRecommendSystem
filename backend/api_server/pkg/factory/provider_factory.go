package factory

import (
	"fmt"
	"strings"

	"github.com/venndev/vrecommendation/pkg/configs"
	"github.com/venndev/vrecommendation/pkg/database/providers"
	"github.com/venndev/vrecommendation/pkg/interfaces"
)

type DatabaseProviderFactory struct {
	config *configs.DatabaseConfigResult
}

func NewDatabaseProviderFactory(config *configs.DatabaseConfigResult) *DatabaseProviderFactory {
	return &DatabaseProviderFactory{
		config: config,
	}
}

func (f *DatabaseProviderFactory) CreateProvider() (interfaces.DatabaseProvider, error) {
	if f.config == nil {
		return nil, fmt.Errorf("database configuration is nil")
	}

	if f.config.URL == "" {
		return nil, fmt.Errorf("database URL is empty")
	}

	dbType := strings.ToLower(strings.TrimSpace(f.config.Type))
	
	switch dbType {
	case "mysql":
		return providers.NewMySQLProvider(f.config), nil
	case "postgres", "postgresql":
		return providers.NewPostgreSQLProvider(f.config), nil
	default:
		return nil, fmt.Errorf("unsupported database type: %s. Supported types: mysql, postgres", f.config.Type)
	}
}

func (f *DatabaseProviderFactory) GetSupportedTypes() []string {
	return []string{"mysql", "postgres", "postgresql"}
}

func (f *DatabaseProviderFactory) ValidateConfig() error {
	if f.config == nil {
		return fmt.Errorf("database configuration is nil")
	}

	if f.config.Type == "" {
		return fmt.Errorf("database type is required")
	}

	if f.config.URL == "" {
		return fmt.Errorf("database URL is required")
	}

	supportedTypes := f.GetSupportedTypes()
	dbType := strings.ToLower(strings.TrimSpace(f.config.Type))
	
	for _, supportedType := range supportedTypes {
		if dbType == supportedType {
			return nil
		}
	}

	return fmt.Errorf("unsupported database type: %s. Supported types: %v", f.config.Type, supportedTypes)
}