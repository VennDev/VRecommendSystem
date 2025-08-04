package kafka

import (
	"context"
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"go.uber.org/zap"
	"time"

	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/setting"
)

type Producer struct {
	producer *kafka.Producer
	config   *setting.Config
	manager  *Manager
}

func NewProducer(config *setting.Config) (*Producer, error) {
	manager := &Manager{config: config}
	kafkaConfig := manager.buildProducerConfig()

	producer, err := kafka.NewProducer(&kafkaConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create kafka producer: %w", err)
	}

	p := &Producer{
		producer: producer,
		config:   config,
		manager:  manager,
	}

	go p.handleDeliveryReports()

	return p, nil
}

func (p *Producer) SendMessage(ctx context.Context, topic string, key, value []byte) error {
	return p.SendMessageWithHeaders(ctx, topic, key, value, nil)
}

func (p *Producer) SendMessageAsync(ctx context.Context, topic string, key, value []byte) error {
	fullTopicName := p.manager.buildTopicName(topic)

	return p.producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &fullTopicName, Partition: kafka.PartitionAny},
		Key:            key,
		Value:          value,
		Headers:        p.buildDefaultHeaders(),
	}, nil)
}

func (p *Producer) SendMessageWithHeaders(ctx context.Context, topic string, key, value []byte, headers map[string][]byte) error {
	deliveryChan := make(chan kafka.Event, 1)
	defer close(deliveryChan)

	fullTopicName := p.manager.buildTopicName(topic)
	msgHeaders := p.buildDefaultHeaders()

	// Merge custom headers
	for k, v := range headers {
		msgHeaders = append(msgHeaders, kafka.Header{Key: k, Value: v})
	}

	err := p.producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &fullTopicName, Partition: kafka.PartitionAny},
		Key:            key,
		Value:          value,
		Headers:        msgHeaders,
	}, deliveryChan)

	if err != nil {
		return fmt.Errorf("failed to produce message: %w", err)
	}

	select {
	case e := <-deliveryChan:
		if msg, ok := e.(*kafka.Message); ok {
			if msg.TopicPartition.Error != nil {
				return fmt.Errorf("delivery failed: %w", msg.TopicPartition.Error)
			}
		}
	case <-ctx.Done():
		return ctx.Err()
	case <-time.After(time.Duration(p.config.Producer.DeliveryTimeoutMs) * time.Millisecond):
		return fmt.Errorf("delivery timeout")
	}

	return nil
}

func (p *Producer) Flush(timeoutMs int) int {
	return p.producer.Flush(timeoutMs)
}

func (p *Producer) Close() error {
	p.producer.Close()
	return nil
}

func (p *Producer) handleDeliveryReports() {
	for e := range p.producer.Events() {
		switch ev := e.(type) {
		case *kafka.Message:
			if ev.TopicPartition.Error != nil {
				global.Logger.Error("Message delivery failed",
					ev.TopicPartition.Error,
					zap.String("topic", *ev.TopicPartition.Topic),
					zap.Int32("partition", ev.TopicPartition.Partition),
				)
			} else {
				global.Logger.Debug("Message delivered",
					zap.String("topic", *ev.TopicPartition.Topic),
					zap.Int32("partition", ev.TopicPartition.Partition),
					zap.Any("offset", ev.TopicPartition.Offset),
				)
			}
		}
	}
}

func (p *Producer) buildDefaultHeaders() []kafka.Header {
	return []kafka.Header{
		{Key: "timestamp", Value: []byte(fmt.Sprintf("%d", time.Now().Unix()))},
		{Key: "producer_id", Value: []byte(p.config.Kafka.ClientID)},
		{Key: "environment", Value: []byte(p.config.Environment.Env)},
	}
}
