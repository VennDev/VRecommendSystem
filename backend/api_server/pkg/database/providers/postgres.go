package providers

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/pkg/configs"
)

type PostgreSQLProvider struct {
	config *configs.DatabaseConfigResult
	db     *sql.DB
}

func NewPostgreSQLProvider(config *configs.DatabaseConfigResult) *PostgreSQLProvider {
	return &PostgreSQLProvider{
		config: config,
	}
}

func (p *PostgreSQLProvider) Connect() error {
	if p.config == nil {
		return fmt.Errorf("database configuration is nil")
	}

	if p.config.URL == "" {
		return fmt.Errorf("database URL is empty")
	}

	db, err := sql.Open("postgres", p.config.URL)
	if err != nil {
		return fmt.Errorf("failed to connect to PostgreSQL: %w", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(p.config.MaxOpenConns)
	db.SetMaxIdleConns(p.config.MaxIdleConns)
	db.SetConnMaxLifetime(p.config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(p.config.ConnMaxIdleTime)

	// Test connection
	if err := db.Ping(); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping PostgreSQL database: %w", err)
	}

	p.db = db
	return nil
}

func (p *PostgreSQLProvider) GetConnection() *sql.DB {
	return p.db
}

func (p *PostgreSQLProvider) Close() error {
	if p.db != nil {
		err := p.db.Close()
		p.db = nil
		return err
	}
	return nil
}

func (p *PostgreSQLProvider) Ping() error {
	if p.db == nil {
		return fmt.Errorf("PostgreSQL database connection not established")
	}
	return p.db.Ping()
}

func (p *PostgreSQLProvider) GetType() string {
	return "postgres"
}