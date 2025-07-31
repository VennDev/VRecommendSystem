package database

import (
	"context"
	"fmt"
	"github.com/venndev/vrecommendation/global"
)

type Manager interface {
	Close() error
	Ping(ctx context.Context) error
	IsConnected() bool
}

type DatabaseManager struct {
	sql   SQLManager
	nosql NoSQLManager
}

func NewDatabaseManager() (*DatabaseManager, error) {
	dm := &DatabaseManager{}

	if global.Config.Database.Type != "" {
		sqlMgr, err := NewSQLManager(global.Config.Database)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize SQL manager: %w", err)
		}
		dm.sql = sqlMgr
	}

	return dm, nil
}

func NewInteractionsDatabaseManager() (*DatabaseManager, error) {
	dm := &DatabaseManager{}

	dbType := global.Config.Database.Type

	if dbType == "mongodb" {
		mongoMgr, err := NewMongoManager(global.Config.Database)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize MongoDB manager: %w", err)
		}
		dm.nosql = mongoMgr
	} else {
		sqlMgr, err := NewSQLManager(global.Config.Database)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize SQL manager: %w", err)
		}
		dm.sql = sqlMgr
	}

	return dm, nil
}

func (dm *DatabaseManager) GetSQL() SQLManager {
	return dm.sql
}

func (dm *DatabaseManager) GetNoSQL() NoSQLManager {
	return dm.nosql
}

func (dm *DatabaseManager) Close() error {
	var errors []error

	if dm.sql != nil {
		if err := dm.sql.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close SQL database: %w", err))
		}
	}

	if dm.nosql != nil {
		if err := dm.nosql.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close NoSQL database: %w", err))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("database close errors: %v", errors)
	}
	return nil
}

func (dm *DatabaseManager) Ping(ctx context.Context) error {
	if dm.sql != nil {
		if err := dm.sql.Ping(ctx); err != nil {
			return fmt.Errorf("SQL database ping failed: %w", err)
		}
	}

	if dm.nosql != nil {
		if err := dm.nosql.Ping(ctx); err != nil {
			return fmt.Errorf("NoSQL database ping failed: %w", err)
		}
	}

	return nil
}

func (dm *DatabaseManager) IsConnected() bool {
	if dm.sql != nil && dm.sql.IsConnected() {
		return true
	}
	if dm.nosql != nil && dm.nosql.IsConnected() {
		return true
	}
	return false
}
