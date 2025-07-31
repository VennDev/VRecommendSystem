package provider

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/database"
)

func GetDB() (*database.DatabaseManager, error) {
	return database.NewDatabaseManager()
}

func GetInteractionsDB() (*database.DatabaseManager, error) {
	return database.NewInteractionsDatabaseManager()
}

func GetSQLDB() (database.SQLManager, error) {
	factory := database.NewFactory()
	return factory.CreateSQLManager(global.Config.Database)
}

func GetMongoDB() (database.NoSQLManager, error) {
	factory := database.NewFactory()
	return factory.CreateNoSQLManager(global.Config.Database)
}
