"""
Amplitude service helper for sending server-side events
"""
import httpx
import os
from typing import Dict, Any, Optional


class AmplitudeService:
    def __init__(self):
        self.api_key = os.getenv("AMPLITUDE_API_KEY")
        self.api_url = "https://api2.amplitude.com/2/httpapi"
    
    def track(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        event_properties: Optional[Dict[str, Any]] = None,
        user_properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an event to Amplitude.
        Returns True if successful, False otherwise.
        """
        if not self.api_key:
            return False
        
        try:
            event = {
                "event_type": event_type,
                "event_properties": event_properties or {},
                "user_properties": user_properties or {},
            }
            
            if user_id:
                event["user_id"] = user_id
            
            payload = {
                "api_key": self.api_key,
                "events": [event]
            }
            
            with httpx.Client() as client:
                response = client.post(self.api_url, json=payload, timeout=5.0)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Amplitude tracking error: {e}")
            return False


# Global instance
amplitude_service = AmplitudeService()

