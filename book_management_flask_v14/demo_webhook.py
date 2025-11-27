"""
Demo script specifically for testing webhook functionality

This script demonstrates:
1. Managing webhooks via API
2. Triggering events that send webhook notifications
3. Testing webhook delivery
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_payload_example(event_type, sample_data):
    """Print example webhook payload"""
    payload = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'event_type': event_type,
        'service': 'book_management_api',
        'version': 'v14',
        'data': sample_data
    }
    print(json.dumps(payload, indent=2))

def demo_webhook_management():
    """Demonstrate webhook management"""
    
    print_section("1. Webhook Management API")
    
    # Get current webhooks
    print("GET /webhooks - View configured webhooks")
    response = requests.get(f"{BASE_URL}/webhooks")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Add a test webhook (webhook.site is great for testing)
    print("POST /webhooks - Add a webhook URL")
    print("TIP: Get your own URL at https://webhook.site\n")
    webhook_url = "https://webhook.site/test-book-management"
    webhook_data = {"url": webhook_url}
    response = requests.post(f"{BASE_URL}/webhooks", json=webhook_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Get webhooks again to verify
    print("GET /webhooks - Verify webhook was added")
    response = requests.get(f"{BASE_URL}/webhooks")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test webhook
    print("POST /webhooks/test - Send test notification")
    response = requests.post(f"{BASE_URL}/webhooks/test")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    print("Expected webhook payload for test:")
    print_payload_example('system_health', {
        'message': 'Test webhook notification',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    
def demo_webhook_events():
    """Demonstrate webhook events by triggering them"""
    
    print_section("2. Webhook Events - Real Notifications")
    
    print("Let's trigger actual events that send webhook notifications...\n")
    
    # Register a user (triggers user_registered webhook)
    print("EVENT 1: User Registration")
    print("-" * 70)
    user_email = f"webhook_test_{int(time.time())}@example.com"
    user_data = {
        "name": "Webhook Test User",
        "email": user_email
    }
    
    print(f"POST /api/auth/register - Register user: {user_email}")
    response = requests.post(f"{API_URL}/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        user_id = response.json().get('id')
        print(f"User created with ID: {user_id}\n")
        
        print("Expected webhook payload:")
        print_payload_example('user_registered', {
            'user_id': user_id,
            'user_name': 'Webhook Test User',
            'user_email': user_email
        })
        
        # Login to get token
        print(f"\nPOST /api/auth/login - Login as {user_email}")
        login_response = requests.post(f"{API_URL}/auth/login", json={"email": user_email})
        if login_response.status_code == 200:
            cookies = login_response.cookies
            
            # Create book and copy for borrowing test
            print("\n" + "="*70)
            print("EVENT 2: Book Borrowed")
            print("-" * 70)
            
            # Create book title
            book_data = {
                "title": "Webhooks in Practice",
                "author": "Test Author",
                "publisher": "Demo Publisher",
                "year": 2025
            }
            book_response = requests.post(f"{API_URL}/book_titles", json=book_data, cookies=cookies)
            
            if book_response.status_code == 201:
                book_id = book_response.json().get('id')
                
                # Create book copy
                copy_data = {
                    "book_title_id": book_id,
                    "barcode": f"WEBHOOK{int(time.time())}",
                    "available": True
                }
                copy_response = requests.post(f"{API_URL}/book_copies", json=copy_data, cookies=cookies)
                
                if copy_response.status_code == 201:
                    copy_id = copy_response.json().get('id')
                    
                    # Borrow the book
                    due_date = (datetime.now() + timedelta(days=14)).isoformat()
                    borrow_data = {
                        "book_copy_id": copy_id,
                        "due_date": due_date
                    }
                    
                    print(f"POST /api/borrowings - Borrow book copy {copy_id}")
                    borrow_response = requests.post(f"{API_URL}/borrowings", json=borrow_data, cookies=cookies)
                    print(f"Status: {borrow_response.status_code}")
                    
                    if borrow_response.status_code == 201:
                        borrowing_id = borrow_response.json().get('id')
                        print(f"Book borrowed! Borrowing ID: {borrowing_id}\n")
                        
                        print("Expected webhook payload:")
                        print_payload_example('book_borrowed', {
                            'borrowing_id': borrowing_id,
                            'user_id': user_id,
                            'user_name': 'Webhook Test User',
                            'user_email': user_email,
                            'book_copy_id': copy_id,
                            'book_title': 'Webhooks in Practice',
                            'book_author': 'Test Author',
                            'borrow_date': datetime.now().isoformat(),
                            'due_date': due_date
                        })
                        
                        # Return the book
                        print("\n" + "="*70)
                        print("EVENT 3: Book Returned")
                        print("-" * 70)
                        
                        time.sleep(1)  # Small delay
                        
                        print(f"POST /api/borrowings/{borrowing_id}/return - Return book")
                        return_response = requests.post(f"{API_URL}/borrowings/{borrowing_id}/return", cookies=cookies)
                        print(f"Status: {return_response.status_code}")
                        
                        if return_response.status_code == 200:
                            print("Book returned successfully!\n")
                            
                            print("Expected webhook payload:")
                            print_payload_example('book_returned', {
                                'borrowing_id': borrowing_id,
                                'user_id': user_id,
                                'user_name': 'Webhook Test User',
                                'user_email': user_email,
                                'book_copy_id': copy_id,
                                'book_title': 'Webhooks in Practice',
                                'book_author': 'Test Author',
                                'borrow_date': datetime.now().isoformat(),
                                'return_date': datetime.now().isoformat(),
                                'due_date': due_date,
                                'fine': 0.0,
                                'overdue_days': 0
                            })

def demo_webhook_integration():
    """Show webhook integration examples"""
    
    print_section("3. Webhook Integration Examples")
    
    print("You can integrate webhooks with various services:\n")
    
    print("🔔 SLACK")
    print("  URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
    print("  Use: Team notifications for book activities\n")
    
    print("💬 DISCORD")
    print("  URL: https://discord.com/api/webhooks/YOUR/WEBHOOK")
    print("  Use: Bot notifications in Discord channels\n")
    
    print("📊 CUSTOM DASHBOARD")
    print("  URL: https://your-dashboard.com/api/webhook")
    print("  Use: Real-time dashboard updates\n")
    
    print("🚨 MONITORING TOOLS")
    print("  Examples: PagerDuty, Opsgenie, DataDog")
    print("  Use: Alert on specific events\n")
    
    print("🧪 TESTING")
    print("  URL: https://webhook.site")
    print("  Use: Test and debug webhook payloads\n")
    
    print("-" * 70)
    print("\nTo add your webhook:")
    print('  curl -X POST http://localhost:5000/webhooks \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"url": "YOUR_WEBHOOK_URL"}\'')

def demo_webhook_cleanup():
    """Remove test webhook"""
    
    print_section("4. Cleanup (Optional)")
    
    print("To remove the test webhook:\n")
    webhook_url = "https://webhook.site/test-book-management"
    print(f"DELETE /webhooks/{webhook_url}")
    
    # Note: This will fail if URL encoding is needed
    # response = requests.delete(f"{BASE_URL}/webhooks/{webhook_url}")
    # print(f"Status: {response.status_code}")
    
    print("\nOr remove all webhooks via API and restart application")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          Book Management System v14 - Webhook Demo                  ║
╚══════════════════════════════════════════════════════════════════════╝

This demo will:
✓ Show webhook management API
✓ Trigger events that send webhooks (user registration, borrowing, return)
✓ Display expected webhook payloads
✓ Provide integration examples

Prerequisites:
✓ Flask application running on http://localhost:5000
✓ (Optional) Get a test URL from https://webhook.site

Press Ctrl+C to cancel, or Enter to continue...
    """)
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nDemo cancelled")
        return
    
    try:
        demo_webhook_management()
        demo_webhook_events()
        demo_webhook_integration()
        demo_webhook_cleanup()
        
        print_section("✅ Demo Complete!")
        print("""
Summary:
• Webhooks configured via API
• 3 events triggered (user_registered, book_borrowed, book_returned)
• All webhooks sent asynchronously (non-blocking)

Check your webhook.site URL to see the actual payloads!

For more information, see WEBHOOK.md
        """)
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        print("\nMake sure the Flask application is running:")
        print("  python -m book_management_flask_v14.run")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
