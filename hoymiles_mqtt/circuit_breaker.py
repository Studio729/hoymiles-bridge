"""Circuit breaker and error recovery mechanisms."""

import logging
import time
from enum import Enum
from typing import Callable, Optional, TypeVar, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, name: str = "circuit"):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening
            timeout: Seconds before attempting recovery
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Optional[T]:
        """Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if circuit is open
            
        Raises:
            Exception: If function fails and circuit is closed/half-open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' attempting reset (half-open)")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting call")
                return None
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' recovered, closing")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
        else:
            self.failure_count = max(0, self.failure_count - 1)
            self.success_count += 1
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}' failed recovery, reopening")
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}' threshold reached "
                f"({self.failure_count} failures), opening circuit"
            )
            self.state = CircuitBreakerState.OPEN
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitBreakerState.OPEN
    
    def reset(self) -> None:
        """Manually reset circuit breaker."""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    def get_status(self) -> dict:
        """Get circuit breaker status.
        
        Returns:
            Status dictionary
        """
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'seconds_since_failure': int(time.time() - self.last_failure_time) if self.last_failure_time else None,
        }


class RetryStrategy:
    """Exponential backoff retry strategy."""
    
    def __init__(self, max_attempts: int = 3, max_backoff: int = 300,
                 min_wait: int = 1, max_wait: int = 60):
        """Initialize retry strategy.
        
        Args:
            max_attempts: Maximum retry attempts
            max_backoff: Maximum total backoff time
            min_wait: Minimum wait time between retries
            max_wait: Maximum wait time between retries
        """
        self.max_attempts = max_attempts
        self.max_backoff = max_backoff
        self.min_wait = min_wait
        self.max_wait = max_wait
    
    def create_decorator(self, exception_types: tuple = (Exception,)):
        """Create retry decorator with configured strategy.
        
        Args:
            exception_types: Tuple of exception types to retry on
            
        Returns:
            Retry decorator
        """
        return retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(min=self.min_wait, max=self.max_wait),
            retry=retry_if_exception_type(exception_types),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )


class ErrorRecoveryManager:
    """Manages error recovery for multiple services."""
    
    def __init__(self, config: Any):
        """Initialize error recovery manager.
        
        Args:
            config: Configuration object with error recovery settings
        """
        self.config = config
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_strategy = RetryStrategy(
            max_attempts=config.comm_retries + 1,
            max_backoff=getattr(config, 'max_backoff', 300),
            min_wait=1,
            max_wait=60,
        )
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service.
        
        Args:
            name: Service name
            
        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            threshold = getattr(self.config, 'circuit_breaker_threshold', 5)
            timeout = getattr(self.config, 'circuit_breaker_timeout', 60)
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=threshold,
                timeout=timeout,
                name=name,
            )
        return self.circuit_breakers[name]
    
    def execute_with_recovery(self, service_name: str, func: Callable[..., T],
                             *args: Any, **kwargs: Any) -> Optional[T]:
        """Execute function with circuit breaker and retry logic.
        
        Args:
            service_name: Name of service for circuit breaker
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if circuit breaker is open
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        def wrapped_func():
            if self.config.exponential_backoff:
                # Apply retry decorator
                decorated = self.retry_strategy.create_decorator()(func)
                return decorated(*args, **kwargs)
            else:
                # No retry, just execute
                return func(*args, **kwargs)
        
        try:
            return circuit_breaker.call(wrapped_func)
        except Exception as e:
            logger.error(f"Error in {service_name} after all retries: {e}")
            return None
    
    def get_all_status(self) -> dict:
        """Get status of all circuit breakers.
        
        Returns:
            Dictionary of circuit breaker statuses
        """
        return {
            name: cb.get_status()
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")

