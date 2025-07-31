package database

import (
	"fmt"
	"github.com/venndev/vrecommendation/pkg/setting"
)

type Factory struct{}

func NewFactory() *Factory {
	return &Factory{}
}

func (f *Factory) CreateSQLManager(config setting.Database) (SQLManager, error) {
	switch config.Type {
	case "postgres", "postgresql", "mysql", "sqlite3", "sqlite":
		return NewSQLManager(config)
	default:
		return nil, fmt.Errorf("unsupported SQL database type: %s", config.Type)
	}
}

func (f *Factory) CreateNoSQLManager(config setting.Database) (NoSQLManager, error) {
	switch config.Type {
	case "mongodb":
		return NewMongoManager(config)
	default:
		return nil, fmt.Errorf("unsupported NoSQL database type: %s", config.Type)
	}
}

func (f *Factory) CreateManager(config setting.Database) (Manager, error) {
	switch config.Type {
	case "postgres", "postgresql", "mysql", "sqlite3", "sqlite":
		return f.CreateSQLManager(config)
	case "mongodb":
		return f.CreateNoSQLManager(config)
	default:
		return nil, fmt.Errorf("unsupported database type: %s", config.Type)
	}
}
