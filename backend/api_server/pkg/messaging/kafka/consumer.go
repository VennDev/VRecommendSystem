package kafka

import (
	"context"
	"errors"
	"fmt"
	"github.com/confluentinc/confluent-kafka-go/kafka"
	"time"

	"github.com/venndev/vrecommendation/pkg/messaging"
	"github.com/venndev/vrecommendation/pkg/setting"
)

type Consumer struct {
	consumer *kafka.Consumer
	config   setting.Config
	groupID  string
	manager  *Manager
}

func NewConsumer(config setting.Config, groupID string) (*Consumer, error) {
	manager := &Manager{config: config}
	kafkaConfig := manager.buildConsumerConfig(groupID)

	consumer, err := kafka.NewConsumer(&kafkaConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create kafka consumer: %w", err)
	}

	return &Consumer{
		consumer: consumer,
		config:   config,
		groupID:  groupID,
		manager:  manager,
	}, nil
}

func (c *Consumer) Subscribe(topics []string) error {
	fullTopics := make([]string, len(topics))
	for i, topic := range topics {
		fullTopics[i] = c.manager.buildTopicName(topic)
	}

	return c.consumer.SubscribeTopics(fullTopics, nil)
}

func (c *Consumer) Consume(ctx context.Context) (<-chan messaging.Message, <-chan error) {
	msgChan := make(chan messaging.Message, 100)
	errChan := make(chan error, 10)

	go func() {
		defer close(msgChan)
		defer close(errChan)

		for {
			select {
			case <-ctx.Done():
				return
			default:
				msg, err := c.consumer.ReadMessage(time.Duration(c.config.Consumer.FetchMaxWaitMs) * time.Millisecond)
				if err != nil {
					var kafkaErr kafka.Error
					if errors.As(err, &kafkaErr) {
						switch kafkaErr.Code() {
						case kafka.ErrTimedOut:
							continue
						case kafka.ErrPartitionEOF:
							continue
						default:
							select {
							case errChan <- fmt.Errorf("consumer error: %w", err):
							case <-ctx.Done():
								return
							}
							continue
						}
					}
					continue
				}

				message := messaging.Message{
					Topic:     *msg.TopicPartition.Topic,
					Key:       msg.Key,
					Value:     msg.Value,
					Partition: int(msg.TopicPartition.Partition),
					Offset:    int64(msg.TopicPartition.Offset),
					Headers:   convertHeaders(msg.Headers),
					Timestamp: msg.Timestamp,
				}

				select {
				case msgChan <- message:
				case <-ctx.Done():
					return
				}
			}
		}
	}()

	return msgChan, errChan
}

func (c *Consumer) Commit(ctx context.Context, message messaging.Message) error {
	_, err := c.consumer.CommitMessage(&kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &message.Topic,
			Partition: int32(message.Partition),
			Offset:    kafka.Offset(message.Offset + 1),
		},
	})
	return err
}

func (c *Consumer) CommitOffset(ctx context.Context, topic string, partition int, offset int64) error {
	fullTopicName := c.manager.buildTopicName(topic)
	_, err := c.consumer.CommitOffsets([]kafka.TopicPartition{
		{
			Topic:     &fullTopicName,
			Partition: int32(partition),
			Offset:    kafka.Offset(offset + 1),
		},
	})
	return err
}

func (c *Consumer) Close() error {
	return c.consumer.Close()
}

func (c *Consumer) GetConsumerGroupMetadata() (*kafka.ConsumerGroupMetadata, error) {
	metadata, err := c.consumer.GetConsumerGroupMetadata()
	return metadata, err
}

func (c *Consumer) Pause(partitions []kafka.TopicPartition) error {
	return c.consumer.Pause(partitions)
}

func (c *Consumer) Resume(partitions []kafka.TopicPartition) error {
	return c.consumer.Resume(partitions)
}

func (c *Consumer) GetWatermarkOffsets(topic string, partition int32) (low, high int64, err error) {
	fullTopicName := c.manager.buildTopicName(topic)
	return c.consumer.QueryWatermarkOffsets(fullTopicName, partition, 5000)
}

func convertHeaders(headers []kafka.Header) map[string][]byte {
	result := make(map[string][]byte)
	for _, header := range headers {
		result[header.Key] = header.Value
	}
	return result
}
