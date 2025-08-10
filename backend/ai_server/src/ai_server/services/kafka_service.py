import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from omegaconf import DictConfig
from ..messaging.kafka.consumer import Consumer
import threading
from queue import Queue, Empty
from collections import defaultdict, deque


@dataclass
class RecommendationRequest:
    """Data class for recommendation requests from API server"""
    user_id: str
    request_id: str
    context: Dict[str, Any]
    callback_url: Optional[str] = None
    max_recommendations: int = 10
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class UserEvent:
    """Data class for user interaction events"""
    user_id: str
    event_type: str
    item_id: str
    timestamp: datetime
    metadata: Dict[str, Any]
    weight: float = 1.0


class FeatureStore:
    """In-memory feature store for user interactions"""

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.logger = logging.getLogger(__name__)

        # Time windows for feature aggregation
        self.short_term = timedelta(hours=cfg.ai_server.feature_window.short_term_hours)
        self.medium_term = timedelta(days=cfg.ai_server.feature_window.medium_term_days)
        self.long_term = timedelta(days=cfg.ai_server.feature_window.long_term_days)

        # Storage for user events (user_id -> deque of events)
        self.user_events = defaultdict(lambda: deque(maxlen=10000))
        self.event_weights = cfg.event_types.event_weights

        self._lock = threading.RLock()

    def add_event(self, event: UserEvent):
        """Add user event to feature store"""
        with self._lock:
            # Set weight from config
            if event.event_type in self.event_weights:
                event.weight = self.event_weights[event.event_type]

            self.user_events[event.user_id].append(event)

    def get_user_features(self, user_id: str) -> Dict[str, Any]:
        """Extract features for a user"""
        with self._lock:
            events = list(self.user_events[user_id])

        if not events:
            return self._empty_features()

        now = datetime.now()
        features = {}

        # Filter events by time windows
        short_events = [e for e in events if now - e.timestamp <= self.short_term]
        medium_events = [e for e in events if now - e.timestamp <= self.medium_term]
        long_events = [e for e in events if now - e.timestamp <= self.long_term]

        # Aggregate features by time window
        features.update(self._aggregate_features(short_events, "short_term"))
        features.update(self._aggregate_features(medium_events, "medium_term"))
        features.update(self._aggregate_features(long_events, "long_term"))

        # Recent items
        features["recent_items"] = [e.item_id for e in short_events[-10:]]

        return features

    def _aggregate_features(self, events: List[UserEvent], window: str) -> Dict[str, Any]:
        """Aggregate features for a time window"""
        if not events:
            return {f"{window}_total_events": 0}

        features = {}
        event_counts = defaultdict(int)
        total_weight = 0

        for event in events:
            event_counts[event.event_type] += 1
            total_weight += event.weight

        features[f"{window}_total_events"] = len(events)
        features[f"{window}_total_weight"] = total_weight
        features[f"{window}_avg_weight"] = total_weight / len(events) if events else 0

        # Event type distribution
        for event_type, count in event_counts.items():
            features[f"{window}_{event_type}_count"] = count

        return features

    def _empty_features(self) -> Dict[str, Any]:
        """Return empty features for new users"""
        return {
            "short_term_total_events": 0,
            "medium_term_total_events": 0,
            "long_term_total_events": 0,
            "recent_items": []
        }


class MLRecommendationEngine:
    """Mock ML recommendation engine"""

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.logger = logging.getLogger(__name__)

    def generate_recommendations(self, user_features: Dict[str, Any],
                                 context: Dict[str, Any],
                                 max_items: int = 10) -> List[Dict[str, Any]]:
        """Generate recommendations based on user features and context"""

        # Mock recommendation logic
        # In production, this would call your ML model
        recommendations = []

        # Simple logic: recommend items based on recent interactions
        recent_items = user_features.get("recent_items", [])
        total_events = user_features.get("short_term_total_events", 0)

        # Generate mock recommendations
        for i in range(min(max_items, 20)):
            score = max(0.1, 1.0 - (i * 0.05))

            # Boost score based on user activity
            if total_events > 10:
                score += 0.2

            recommendations.append({
                "item_id": f"item_{i + 1000}",
                "score": score,
                "reason": f"Based on {total_events} recent interactions",
                "metadata": {
                    "category": "recommended",
                    "user_activity_level": "high" if total_events > 10 else "low"
                }
            })

        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        self.logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations[:max_items]


class KafkaService:
    """
    High-level Kafka service for AI recommendation system
    Handles message processing and ML integration
    """

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.consumer = Consumer(cfg)
        self.feature_store = FeatureStore(cfg)
        self.ml_engine = MLRecommendationEngine(cfg)

        # Processing queues
        self.recommendation_queue = Queue(maxsize=cfg.ai_server.processing.queue_size)
        self.event_queue = Queue(maxsize=cfg.ai_server.processing.queue_size)

        # Worker threads
        self.workers = []
        self.running = True

    def start(self):
        """Start the Kafka service"""
        self.logger.info("Starting Kafka AI Service...")

        # Connect to Kafka
        # if not self.consumer.connect():
        #     self.logger.error("Failed to connect to Kafka")
        #     return False

        # Set message handler
        self.consumer.set_message_handler(self._handle_message)

        # Start worker threads
        self._start_workers()

        # Start consuming messages
        try:
            self.consumer.consume_messages(timeout=1.0)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self.stop()

        return True

    def _start_workers(self):
        """Start worker threads for processing"""
        num_workers = self.cfg.ai_server.processing.worker_threads

        # Recommendation processing workers
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._recommendation_worker,
                name=f"RecommendationWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        # Event processing worker
        event_worker = threading.Thread(
            target=self._event_worker,
            name="EventWorker",
            daemon=True
        )
        event_worker.start()
        self.workers.append(event_worker)

        self.logger.info(f"Started {len(self.workers)} worker threads")

    def _handle_message(self, message: Dict[str, Any]):
        """Handle an incoming Kafka message"""
        topic = message['topic']

        try:
            if topic == self.cfg.topics.recommendation_requests:
                # Handle recommendation request
                self._handle_recommendation_request(message)
            else:
                # Handle user event
                self._handle_user_event(message)

        except Exception as e:
            self.logger.error(f"Error handling message from {topic}: {e}")

    def _handle_recommendation_request(self, message: Dict[str, Any]):
        """Handle recommendation request from API server"""
        try:
            data = message['value']

            request = RecommendationRequest(
                user_id=data['user_id'],
                request_id=data['request_id'],
                context=data.get('context', {}),
                callback_url=data.get('callback_url'),
                max_recommendations=data.get('max_recommendations', 10)
            )

            # Add to processing queue
            self.recommendation_queue.put(request, timeout=1.0)

        except Exception as e:
            self.logger.error(f"Error parsing recommendation request: {e}")

    def _handle_user_event(self, message: Dict[str, Any]):
        """Handle user interaction event"""
        try:
            data = message['value']
            topic = message['topic']

            # Extract an event type from topic name
            event_type = self._extract_event_type(topic)

            event = UserEvent(
                user_id=data['user_id'],
                event_type=event_type,
                item_id=data['item_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                metadata=data.get('metadata', {})
            )

            # Add to processing queue
            self.event_queue.put(event, timeout=1.0)

        except Exception as e:
            self.logger.error(f"Error parsing user event: {e}")

    def _extract_event_type(self, topic: str) -> str:
        """Extract an event type from topic name"""
        prefix = self.cfg.topics.prefix
        suffix = self.cfg.topics.suffix

        # Remove prefix and suffix
        event_type = topic.replace(prefix, '').replace(suffix, '')
        return event_type

    def _recommendation_worker(self):
        """Worker thread for processing recommendation requests"""
        self.logger.info(f"Started recommendation worker: {threading.current_thread().name}")

        while self.running:
            try:
                request = self.recommendation_queue.get(timeout=1.0)
                self._process_recommendation_request(request)
                self.recommendation_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in recommendation worker: {e}")

    def _event_worker(self):
        """Worker thread for processing user events"""
        self.logger.info("Started event processing worker")

        while self.running:
            try:
                event = self.event_queue.get(timeout=1.0)
                self.feature_store.add_event(event)
                self.event_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in event worker: {e}")

    def _process_recommendation_request(self, request: RecommendationRequest):
        """Process recommendation request"""
        start_time = time.time()

        try:
            # Get user features
            user_features = self.feature_store.get_user_features(request.user_id)

            # Generate recommendations
            recommendations = self.ml_engine.generate_recommendations(
                user_features=user_features,
                context=request.context,
                max_items=request.max_recommendations
            )

            # Prepare response
            response = {
                "request_id": request.request_id,
                "user_id": request.user_id,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }

            # Send response (mock - in production send to callback URL or response topic)
            self.logger.info(f"Generated recommendations for user {request.user_id}: "
                             f"{len(recommendations)} items in {response['processing_time_ms']}ms")

            # Here you would send response back to API server
            # self._send_response(response, request.callback_url)

        except Exception as e:
            self.logger.error(f"Error processing recommendation request: {e}")

    def stop(self):
        """Stop the service gracefully"""
        self.logger.info("Stopping Kafka AI Service...")
        self.running = False

        # Wait for queues to empty
        self.recommendation_queue.join()
        self.event_queue.join()

        # Stop consumer
        self.consumer.shutdown()

        # Wait for worker threads
        for worker in self.workers:
            worker.join(timeout=5.0)

        self.logger.info("Kafka AI Service stopped")
