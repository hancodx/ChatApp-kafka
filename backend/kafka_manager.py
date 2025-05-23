from confluent_kafka import Producer, Consumer, KafkaException
from config import KAFKA_BROKER, BASE_TOPIC
import threading
import logging

class KafkaManager:
    def __init__(self, username, message_callback):
        self.username = username
        self.message_callback = message_callback
        self.running = False
        self.consumer_thread = None
        self.logger = logging.getLogger(__name__)

    def send_message(self, target, message, is_group=False):
        """Envoie un message à un contact ou un groupe"""
        try:
            producer = Producer({
                'bootstrap.servers': KAFKA_BROKER,
                'message.timeout.ms': 3000
            })
            
            if not is_group:
                topic = f"{BASE_TOPIC}-{self.username}-{target}"
                full_message = f"{self.username}: {message}"
            else:
                topic = f"{BASE_TOPIC}-group-{target}"
                full_message = f"[{target}] {self.username}: {message}"
            
            producer.produce(topic, full_message.encode('utf-8'))
            producer.flush()
            self.logger.debug(f"Message sent to {topic}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise

    def start_consumer(self, target, is_group=False):
        """Démarre le consommateur pour un contact ou groupe spécifique"""
        if self.consumer_thread and self.running:
            self.stop_consumer()
        
        self.running = True
        self.consumer_thread = threading.Thread(
            target=self._consume_messages,
            args=(target, is_group),
            daemon=True
        )
        self.consumer_thread.start()

    def _consume_messages(self, target, is_group):
        """Méthode interne pour consommer les messages"""
        try:
            if is_group:
                topic = f"{BASE_TOPIC}-group-{target}"
            else:
                topic = f"{BASE_TOPIC}-{target}-{self.username}"
            
            consumer = Consumer({
                'bootstrap.servers': KAFKA_BROKER,
                'group.id': f"{self.username}-consumer",
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False
            })
            
            consumer.subscribe([topic])
            self.logger.info(f"Started consuming from {topic}")

            while self.running:
                msg = consumer.poll(1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        continue
                    else:
                        self.logger.error(f"Consumer error: {msg.error()}")
                        break
                
                message = msg.value().decode('utf-8')
                if not message.startswith(f"[{target}] {self.username}:") and not message.startswith(f"{self.username}:"):
                    self.message_callback(message)
            
            consumer.close()
            self.logger.info(f"Stopped consuming from {topic}")
        except Exception as e:
            self.logger.error(f"Error in consumer: {str(e)}")
            raise

    def stop_consumer(self):
        """Arrête proprement le consommateur"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
            self.consumer_thread = None

    def stop(self):
        """Nettoyage complet"""
        self.stop_consumer()