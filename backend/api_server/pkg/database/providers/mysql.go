package providers

import (
	"database/sql"
	"fmt"

	_ "github.com/go-sql-driver/mysql"
	"github.com/venndev/vrecommendation/pkg/configs"
)

type MySQLProvider struct {
	config *configs.DatabaseConfigResult
	db     *sql.DB
}

func NewMySQLProvider(config *configs.DatabaseConfigResult) *MySQLProvider {
	return &MySQLProvider{
		config: config,
	}
}

func (m *MySQLProvider) Connect() error {
	if m.config == nil {
		return fmt.Errorf("database configuration is nil")
	}

	if m.config.URL == "" {
		return fmt.Errorf("database URL is empty")
	}

	db, err := sql.Open("mysql", m.config.URL)
	if err != nil {
		return fmt.Errorf("failed to connect to MySQL: %w", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(m.config.MaxOpenConns)
	db.SetMaxIdleConns(m.config.MaxIdleConns)
	db.SetConnMaxLifetime(m.config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(m.config.ConnMaxIdleTime)

	// Test connection
	if err := db.Ping(); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping MySQL database: %w", err)
	}

	m.db = db
	return nil
}

func (m *MySQLProvider) GetConnection() *sql.DB {
	return m.db
}

func (m *MySQLProvider) Close() error {
	if m.db != nil {
		err := m.db.Close()
		m.db = nil
		return err
	}
	return nil
}

func (m *MySQLProvider) Ping() error {
	if m.db == nil {
		return fmt.Errorf("MySQL database connection not established")
	}
	return m.db.Ping()
}

func (m *MySQLProvider) GetType() string {
	return "mysql"
}