package interfaces

import "database/sql"

type DatabaseProvider interface {
	Connect() error
	GetConnection() *sql.DB
	Close() error
	Ping() error
	GetType() string
}