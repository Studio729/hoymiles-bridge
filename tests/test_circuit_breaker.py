"""Tests for circuit breaker module."""

import time
import pytest

from hoymiles_smiles.circuit_breaker import CircuitBreaker, CircuitBreakerState


def test_circuit_breaker_initialization():
    """Test circuit breaker initialization."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60, name="test")
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_success():
    """Test circuit breaker with successful calls."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    
    def success_func():
        return "success"
    
    result = cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    
    def failing_func():
        raise Exception("Test failure")
    
    # First failure
    with pytest.raises(Exception):
        cb.call(failing_func)
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 1
    
    # Second failure
    with pytest.raises(Exception):
        cb.call(failing_func)
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 2
    
    # Third failure - should open
    with pytest.raises(Exception):
        cb.call(failing_func)
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.failure_count == 3


def test_circuit_breaker_rejects_when_open():
    """Test circuit breaker rejects calls when open."""
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    def failing_func():
        raise Exception("Test failure")
    
    # Trigger failures to open circuit
    with pytest.raises(Exception):
        cb.call(failing_func)
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    assert cb.state == CircuitBreakerState.OPEN
    
    # Call should be rejected
    result = cb.call(lambda: "test")
    assert result is None


def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery through half-open state."""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
    
    def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    with pytest.raises(Exception):
        cb.call(failing_func)
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    assert cb.state == CircuitBreakerState.OPEN
    
    # Wait for timeout
    time.sleep(0.2)
    
    # Successful call should close circuit
    result = cb.call(lambda: "success")
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_reset():
    """Test manual circuit breaker reset."""
    cb = CircuitBreaker(failure_threshold=2, timeout=60)
    
    def failing_func():
        raise Exception("Test failure")
    
    # Open the circuit
    with pytest.raises(Exception):
        cb.call(failing_func)
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    assert cb.state == CircuitBreakerState.OPEN
    
    # Manual reset
    cb.reset()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_status():
    """Test circuit breaker status reporting."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60, name="test_cb")
    
    status = cb.get_status()
    assert status['name'] == "test_cb"
    assert status['state'] == CircuitBreakerState.CLOSED.value
    assert status['failure_count'] == 0
    assert status['success_count'] == 0

