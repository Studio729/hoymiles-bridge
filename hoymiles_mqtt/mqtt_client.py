"""Enhanced MQTT client with persistent connection."""

import logging
import queue
import ssl
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

import paho.mqtt.client as mqtt_client

logger = logging.getLogger(__name__)


class EnhancedMqttClient:
    """MQTT client with persistent connection and message batching."""
    
    def __init__(
        self,
        broker: str,
        port: int,
        user: Optional[str] = None,
        password: Optional[str] = None,
        client_id: str = "hoymiles-mqtt",
        tls: bool = False,
        tls_insecure: bool = False,
        tls_ca_cert: Optional[Path] = None,
        keepalive: int = 60,
        qos: int = 1,
        max_queue_size: int = 1000,
    ):
        """Initialize MQTT client.
        
        Args:
            broker: MQTT broker address
            port: MQTT broker port
            user: Username for authentication
            password: Password for authentication
            client_id: MQTT client ID
            tls: Enable TLS
            tls_insecure: Allow insecure TLS (skip cert validation)
            tls_ca_cert: Path to CA certificate
            keepalive: Keepalive interval in seconds
            qos: Default QoS level
            max_queue_size: Maximum message queue size
        """
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.client_id = client_id
        self.tls = tls
        self.tls_insecure = tls_insecure
        self.tls_ca_cert = tls_ca_cert
        self.keepalive = keepalive
        self.qos = qos
        
        self.client: Optional[mqtt_client.Client] = None
        self.connected = False
        self.connection_lock = threading.Lock()
        
        # Message queue for batching
        self.message_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.publisher_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Statistics
        self.messages_sent = 0
        self.messages_failed = 0
        self.reconnect_count = 0
        self.last_error: Optional[str] = None
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize MQTT client with callbacks."""
        try:
            # Create client with unique client ID
            self.client = mqtt_client.Client(
                client_id=self.client_id,
                protocol=mqtt_client.MQTTv311,
                clean_session=True,
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            # Set authentication
            if self.user and self.password:
                self.client.username_pw_set(self.user, self.password)
            
            # Set TLS
            if self.tls:
                tls_context = ssl.create_default_context()
                
                if self.tls_ca_cert and self.tls_ca_cert.exists():
                    tls_context.load_verify_locations(str(self.tls_ca_cert))
                
                if self.tls_insecure:
                    logger.warning("TLS certificate verification disabled - DO NOT USE IN PRODUCTION")
                    tls_context.check_hostname = False
                    tls_context.verify_mode = ssl.CERT_NONE
                
                self.client.tls_set_context(tls_context)
            
            logger.info(f"MQTT client initialized for {self.broker}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback for when client connects to broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")
        else:
            self.connected = False
            error_msg = mqtt_client.connack_string(rc)
            logger.error(f"Failed to connect to MQTT broker: {error_msg} (code {rc})")
            self.last_error = error_msg
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback for when client disconnects from broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker (code {rc})")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid) -> None:
        """Callback for when message is published."""
        logger.debug(f"Message {mid} published successfully")
    
    def connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connection successful
        """
        with self.connection_lock:
            if self.connected:
                return True
            
            try:
                if self.client is None:
                    self._initialize_client()
                
                logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
                self.client.connect(self.broker, self.port, self.keepalive)
                self.client.loop_start()
                
                # Wait for connection (up to 10 seconds)
                for _ in range(100):
                    if self.connected:
                        return True
                    time.sleep(0.1)
                
                logger.error("Connection timeout")
                return False
                
            except Exception as e:
                logger.error(f"Failed to connect to MQTT broker: {e}")
                self.last_error = str(e)
                return False
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        with self.connection_lock:
            if self.client:
                logger.info("Disconnecting from MQTT broker...")
                self.client.loop_stop()
                self.client.disconnect()
                self.connected = False
    
    def start_publisher(self) -> None:
        """Start background publisher thread."""
        if self.publisher_thread and self.publisher_thread.is_alive():
            logger.warning("Publisher thread already running")
            return
        
        self.running = True
        self.publisher_thread = threading.Thread(target=self._publisher_loop, daemon=True)
        self.publisher_thread.start()
        logger.info("MQTT publisher thread started")
    
    def stop_publisher(self) -> None:
        """Stop background publisher thread."""
        self.running = False
        if self.publisher_thread:
            self.publisher_thread.join(timeout=5)
            logger.info("MQTT publisher thread stopped")
    
    def _publisher_loop(self) -> None:
        """Background loop for publishing queued messages."""
        while self.running:
            try:
                # Get message from queue with timeout
                try:
                    topic, payload, retain, qos = self.message_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Ensure we're connected
                if not self.connected:
                    if not self.connect():
                        # Re-queue message if can't connect
                        try:
                            self.message_queue.put((topic, payload, retain, qos), block=False)
                        except queue.Full:
                            logger.error("Message queue full, dropping message")
                            self.messages_failed += 1
                        time.sleep(5)
                        continue
                
                # Publish message
                try:
                    result = self.client.publish(topic, payload, qos=qos, retain=retain)
                    
                    if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
                        self.messages_sent += 1
                        logger.debug(f"Queued message published to {topic}")
                    else:
                        logger.error(f"Failed to publish message to {topic}: {result.rc}")
                        self.messages_failed += 1
                        
                except Exception as e:
                    logger.error(f"Error publishing message: {e}")
                    self.messages_failed += 1
                
                self.message_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in publisher loop: {e}")
                time.sleep(1)
    
    def publish(self, topic: str, payload: str, retain: bool = False, qos: Optional[int] = None) -> bool:
        """Publish message to MQTT broker.
        
        Args:
            topic: MQTT topic
            payload: Message payload
            retain: Whether to retain message
            qos: QoS level (uses default if not specified)
            
        Returns:
            True if message queued successfully
        """
        if qos is None:
            qos = self.qos
        
        try:
            self.message_queue.put((topic, payload, retain, qos), block=False)
            return True
        except queue.Full:
            logger.error("Message queue full, cannot publish")
            self.messages_failed += 1
            return False
    
    def publish_batch(self, messages: list[Tuple[str, str, bool]]) -> int:
        """Publish multiple messages.
        
        Args:
            messages: List of (topic, payload, retain) tuples
            
        Returns:
            Number of messages successfully queued
        """
        queued = 0
        for topic, payload, retain in messages:
            if self.publish(topic, payload, retain):
                queued += 1
        return queued
    
    def get_statistics(self) -> dict:
        """Get client statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'connected': self.connected,
            'messages_sent': self.messages_sent,
            'messages_failed': self.messages_failed,
            'reconnect_count': self.reconnect_count,
            'queue_size': self.message_queue.qsize(),
            'last_error': self.last_error,
            'broker': f"{self.broker}:{self.port}",
        }
    
    def flush(self, timeout: float = 5.0) -> bool:
        """Wait for all queued messages to be published.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all messages published
        """
        try:
            self.message_queue.join()
            return True
        except Exception as e:
            logger.error(f"Error flushing message queue: {e}")
            return False

