"""
Lightweight circuit breaker for provider failures
Opens circuit after repeated failures, closes after timeout
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import time


class CircuitBreaker:
    """Circuit breaker for provider failures"""
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 60):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.circuits: Dict[str, Dict] = {}  # provider_name -> circuit state
    
    def is_open(self, provider_name: str) -> bool:
        """
        Check if circuit is open for provider
        
        Returns:
            True if circuit is open (provider should be skipped)
            False if circuit is closed (provider can be used)
        """
        if provider_name not in self.circuits:
            return False
        
        circuit = self.circuits[provider_name]
        
        # If circuit is closed, allow requests
        if circuit['state'] == 'closed':
            return False
        
        # If circuit is open, check if timeout has passed
        if circuit['state'] == 'open':
            elapsed = (datetime.now() - circuit['opened_at']).total_seconds()
            if elapsed >= self.timeout_seconds:
                # Timeout passed, try closing circuit (half-open state)
                circuit['state'] = 'half-open'
                circuit['half_open_at'] = datetime.now()
                return False  # Allow one request to test
        
        # Circuit is open or half-open (testing)
        return circuit['state'] == 'open'
    
    def record_success(self, provider_name: str):
        """Record successful request - close circuit if open"""
        if provider_name not in self.circuits:
            self.circuits[provider_name] = {
                'state': 'closed',
                'failures': 0,
                'opened_at': None,
            }
            return
        
        circuit = self.circuits[provider_name]
        
        # Reset on success
        circuit['state'] = 'closed'
        circuit['failures'] = 0
        circuit['opened_at'] = None
    
    def record_failure(self, provider_name: str):
        """Record failed request - open circuit if threshold reached"""
        if provider_name not in self.circuits:
            self.circuits[provider_name] = {
                'state': 'closed',
                'failures': 0,
                'opened_at': None,
            }
        
        circuit = self.circuits[provider_name]
        circuit['failures'] += 1
        
        # If half-open and failed, immediately open again
        if circuit['state'] == 'half-open':
            circuit['state'] = 'open'
            circuit['opened_at'] = datetime.now()
            return
        
        # If failures exceed threshold, open circuit
        if circuit['failures'] >= self.failure_threshold:
            circuit['state'] = 'open'
            circuit['opened_at'] = datetime.now()
            print(f"[CircuitBreaker] Circuit opened for {provider_name} after {circuit['failures']} failures")
    
    def get_state(self, provider_name: str) -> Dict:
        """Get current circuit state for debugging"""
        if provider_name not in self.circuits:
            return {
                'state': 'closed',
                'failures': 0,
                'opened_at': None,
            }
        
        circuit = self.circuits[provider_name]
        return {
            'state': circuit['state'],
            'failures': circuit['failures'],
            'opened_at': circuit.get('opened_at'),
            'elapsed_seconds': (datetime.now() - circuit['opened_at']).total_seconds() if circuit.get('opened_at') else None,
        }


# Global circuit breaker instance
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=60)

