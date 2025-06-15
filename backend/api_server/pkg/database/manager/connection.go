package manager

import (
	"database/sql"
	"fmt"
	"sync"

	"github.com/venndev/vrecommendation/pkg/configs"
	"github.com/venndev/vrecommendation/pkg/factory"
	"github.com/venndev/vrecommendation/pkg/interfaces"
)

type ConnectionManager struct {
	provider interfaces.DatabaseProvider
	config   *configs.DatabaseConfigResult
	mu       sync.RWMutex
	isInit   bool
}

var (
	instance *ConnectionManager
	once     sync.Once
)

func GetConnectionManager() *ConnectionManager {
	once.Do(func() {
		instance = &ConnectionManager{
			isInit: false,
		}
	})
	return instance
}

func (cm *ConnectionManager) Initialize(config *configs.DatabaseConfigResult) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if config == nil {
		return fmt.Errorf("database configuration cannot be nil")
	}

	// Close existing connection if any
	if cm.provider != nil {
		if err := cm.provider.Close(); err != nil {
			return fmt.Errorf("failed to close existing connection: %w", err)
		}
	}

	// Create factory and validate configuration
	providerFactory := factory.NewDatabaseProviderFactory(config)
	if err := providerFactory.ValidateConfig(); err != nil {
		return fmt.Errorf("invalid database configuration: %w", err)
	}

	// Create new provider
	provider, err := providerFactory.CreateProvider()
	if err != nil {
		return fmt.Errorf("failed to create database provider: %w", err)
	}

	// Connect to database
	if err := provider.Connect(); err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Update instance state
	cm.provider = provider
	cm.config = config
	cm.isInit = true

	return nil
}

func (cm *ConnectionManager) GetDB() *sql.DB {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.isInit || cm.provider == nil {
		return nil
	}
	return cm.provider.GetConnection()
}

func (cm *ConnectionManager) GetProvider() interfaces.DatabaseProvider {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.provider
}

func (cm *ConnectionManager) GetConfig() *configs.DatabaseConfigResult {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.config
}

func (cm *ConnectionManager) IsInitialized() bool {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.isInit
}

func (cm *ConnectionManager) Close() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.provider != nil {
		err := cm.provider.Close()
		cm.provider = nil
		cm.config = nil
		cm.isInit = false
		return err
	}
	return nil
}

func (cm *ConnectionManager) Ping() error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.isInit || cm.provider == nil {
		return fmt.Errorf("database connection not initialized")
	}
	return cm.provider.Ping()
}

func (cm *ConnectionManager) Reconnect() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.config == nil {
		return fmt.Errorf("no configuration available for reconnection")
	}

	// Close existing connection
	if cm.provider != nil {
		cm.provider.Close()
	}

	// Create new provider
	providerFactory := factory.NewDatabaseProviderFactory(cm.config)
	provider, err := providerFactory.CreateProvider()
	if err != nil {
		return fmt.Errorf("failed to create provider for reconnection: %w", err)
	}

	// Connect to database
	if err := provider.Connect(); err != nil {
		return fmt.Errorf("failed to reconnect to database: %w", err)
	}

	cm.provider = provider
	return nil
}