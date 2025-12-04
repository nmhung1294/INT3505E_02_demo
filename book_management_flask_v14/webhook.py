"""
Webhook notification module for sending notifications to external services
"""

import requests
import json
import threading
from datetime import datetime
from .logging_config import get_logger

logger = get_logger()

class WebhookNotifier:
    """
    Handles sending webhook notifications asynchronously
    """

    def __init__(self, webhook_urls=None):
        """
        Initialize webhook notifier

        Args:
            webhook_urls: List of webhook URLs to send notifications to
        """
        self.webhook_urls = webhook_urls or []
        self.session = requests.Session()

    def add_webhook_url(self, url):
        """Add a webhook URL"""
        if url not in self.webhook_urls:
            self.webhook_urls.append(url)
            logger.info(f"Added webhook URL: {url}")

    def remove_webhook_url(self, url):
        """Remove a webhook URL"""
        if url in self.webhook_urls:
            self.webhook_urls.remove(url)
            logger.info(f"Removed webhook URL: {url}")

    def send_notification(self, event_type, data, sync=False):
        """
        Send notification to all webhook URLs

        Args:
            event_type: Type of event (e.g., 'book_borrowed', 'error', 'user_registered')
            data: Event data dictionary
            sync: If True, send synchronously; otherwise asynchronously
        """
        if not self.webhook_urls:
            return

        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'service': 'book_management_api',
            'version': 'v14',
            'data': data
        }

        if sync:
            self._send_payload(payload)
        else:
            # Send asynchronously to avoid blocking
            thread = threading.Thread(target=self._send_payload, args=(payload,))
            thread.daemon = True
            thread.start()

    def _send_payload(self, payload):
        """Send payload to all webhook URLs"""
        for url in self.webhook_urls:
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=5  # 5 second timeout
                )
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully to {url} for event {payload['event_type']}")
                else:
                    logger.warning(f"Webhook failed to {url}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"Webhook error to {url}: {str(e)}")

# Global webhook notifier instance
webhook_notifier = WebhookNotifier()

def get_webhook_notifier():
    """Get the global webhook notifier instance"""
    return webhook_notifier

def send_webhook_notification(event_type, data, sync=False):
    """
    Convenience function to send webhook notification

    Args:
        event_type: Type of event
        data: Event data
        sync: Send synchronously (default False)
    """
    webhook_notifier.send_notification(event_type, data, sync)

# Event types constants
EVENT_BOOK_BORROWED = 'book_borrowed'
EVENT_BOOK_RETURNED = 'book_returned'
EVENT_USER_REGISTERED = 'user_registered'
EVENT_AUTH_ATTEMPT = 'auth_attempt'
EVENT_ERROR = 'error'
EVENT_SYSTEM_HEALTH = 'system_health'
