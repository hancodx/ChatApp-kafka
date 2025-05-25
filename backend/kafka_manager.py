from confluent_kafka import Producer, Consumer, KafkaException
from config import KAFKA_BROKER, BASE_TOPIC
import threading

class KafkaManager:
    def __init__(self, username):
        self.username = username
        self.running = False
        self.consumer_thread = None

    def send_message(self, target, message, is_group=False):
        """Envoie un message texte"""
        producer = Producer({"bootstrap.servers": KAFKA_BROKER})
        
        if not is_group:
            topic = f"{BASE_TOPIC}-{self.username}-{target}"
            full_message = f"{self.username}: {message}"
            producer.produce(topic, full_message.encode("utf-8"))
        else:
            topic = f"{BASE_TOPIC}-group-{target}"
            full_message = f"[{target}] {self.username}: {message}"
            producer.produce(topic, full_message.encode("utf-8"))
        
        producer.flush()

    def send_image(self, target, image_data, is_group=False):
        """Envoie une image via Kafka"""
        producer = Producer({"bootstrap.servers": KAFKA_BROKER})
        
        if not is_group:
            topic = f"{BASE_TOPIC}-{self.username}-{target}"
            message = f"IMAGE:{self.username}:{image_data}"
            producer.produce(topic, message.encode("utf-8"))
        else:
            topic = f"{BASE_TOPIC}-group-{target}"
            message = f"GROUP_IMAGE:[{target}] {self.username}:{image_data}"
            producer.produce(topic, message.encode("utf-8"))
        
        producer.flush()

    def start_consumer(self, target, is_group, callback):
        """Démarre le consommateur Kafka"""
        if self.consumer_thread and self.running:
            self.running = False
            self.consumer_thread.join()
        
        self.running = True
        self.consumer_thread = threading.Thread(
            target=self._consume_messages,
            args=(target, is_group, callback),
            daemon=True
        )
        self.consumer_thread.start()

    def _consume_messages(self, target, is_group, callback):
        """Reçoit les messages du contact ou du groupe"""
        if not is_group:
            topic = f"{BASE_TOPIC}-{target}-{self.username}"
        else:
            topic = f"{BASE_TOPIC}-group-{target}"
        
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": f"{self.username}-group",
            "auto.offset.reset": "latest"
        })
        consumer.subscribe([topic])
        
        while self.running:
            msg = consumer.poll(1.0)
            
            if msg and not msg.error():
                message = msg.value().decode("utf-8")
                callback(message)
        
        consumer.close()

    def stop_consumer(self):
        """Arrête le consommateur Kafka"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join()