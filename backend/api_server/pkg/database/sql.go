package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/venndev/vrecommendation/pkg/setting"
	"github.com/xo/dburl"
)

type SQLManager interface {
	Manager
	GetDB() *sql.DB
	GetURL() *dburl.URL
	BeginTx(ctx context.Context) (*sql.Tx, error)
}

type sqlManager struct {
	db        *sql.DB
	url       *dburl.URL
	config    setting.Database
	connected bool
}

func NewSQLManager(config setting.Database) (SQLManager, error) {
	connectionStr, err := buildSQLConnectionString(config)
	if err != nil {
		return nil, fmt.Errorf("failed to build connection string: %w", err)
	}

	db, url, err := connectSQL(connectionStr)
	if err != nil {
		return nil, err
	}

	configureSQLConnectionPool(db, config)

	return &sqlManager{
		db:        db,
		url:       url,
		config:    config,
		connected: true,
	}, nil
}

func (sm *sqlManager) GetDB() *sql.DB {
	return sm.db
}

func (sm *sqlManager) GetURL() *dburl.URL {
	return sm.url
}

func (sm *sqlManager) BeginTx(ctx context.Context) (*sql.Tx, error) {
	return sm.db.BeginTx(ctx, nil)
}

func (sm *sqlManager) Close() error {
	if sm.db != nil {
		sm.connected = false
		return sm.db.Close()
	}
	return nil
}

func (sm *sqlManager) Ping(ctx context.Context) error {
	if sm.db == nil {
		return fmt.Errorf("database connection is nil")
	}
	return sm.db.PingContext(ctx)
}

func (sm *sqlManager) IsConnected() bool {
	return sm.connected && sm.db != nil
}

func connectSQL(connectionStr string) (*sql.DB, *dburl.URL, error) {
	u, err := dburl.Parse(connectionStr)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	db, err := sql.Open(u.Driver, connectionStr)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return db, u, nil
}

func configureSQLConnectionPool(db *sql.DB, config setting.Database) {
	if config.MaxIdleConns > 0 {
		db.SetMaxIdleConns(config.MaxIdleConns)
	}
	if config.MaxOpenConns > 0 {
		db.SetMaxOpenConns(config.MaxOpenConns)
	}
	if config.ConnMaxLifetime > 0 {
		db.SetConnMaxLifetime(config.ConnMaxLifetime)
	}
	if config.ConnMaxIdleTime > 0 {
		db.SetConnMaxIdleTime(config.ConnMaxIdleTime)
	}
}

func buildSQLConnectionString(config setting.Database) (string, error) {
	switch config.Type {
	case "postgres", "postgresql":
		return buildPostgreSQLConnectionString(config), nil
	case "mysql":
		return buildMySQLConnectionString(config), nil
	case "sqlite3", "sqlite":
		return buildSQLiteConnectionString(config), nil
	default:
		return "", fmt.Errorf("unsupported database type: %s", config.Type)
	}
}

func buildPostgreSQLConnectionString(config setting.Database) string {
	sslMode := "disable"
	if config.SSL {
		sslMode = "require"
	}

	return fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
		config.User, config.Password, config.Host, config.Port, config.Name, sslMode)
}

func buildMySQLConnectionString(config setting.Database) string {
	tls := "false"
	if config.SSL {
		tls = "true"
	}

	return fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?tls=%s&parseTime=true",
		config.User, config.Password, config.Host, config.Port, config.Name, tls)
}

func buildSQLiteConnectionString(config setting.Database) string {
	return config.Name
}
