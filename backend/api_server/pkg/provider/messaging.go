package provider

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/messaging"
	"github.com/venndev/vrecommendation/pkg/messaging/kafka"
)

func GetMessageBroker() messaging.MessageBroker {
	return global.MessageBroker
}

func GetKafkaManager() (*kafka.Manager, error) {
	return kafka.NewManager()
}

func GetProducer() messaging.MessageProducer {
	return global.MessageBroker.GetProducer()
}

func GetConsumer(groupID string) messaging.MessageConsumer {
	return global.MessageBroker.GetConsumer(groupID)
}
