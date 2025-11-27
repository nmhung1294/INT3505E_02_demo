"""
Demo script to test logging and monitoring features in v14

This script demonstrates:
1. Making various API requests to generate logs and metrics
2. Viewing metrics endpoint
3. Checking log files
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def make_request(method, endpoint, **kwargs):
    """Make HTTP request and print response"""
    url = f"{API_URL}{endpoint}"
    print(f"{method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "PUT":
            response = requests.put(url, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, **kwargs)
        
        print(f"Status: {response.status_code}")
        if response.headers.get('Content-Type', '').startswith('application/json'):
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
        return response
    except Exception as e:
        print(f"Error: {e}\n")
        return None

def demo_monitoring():
    """Demonstrate monitoring features"""
    
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"GET /health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print_section("2. User Registration & Authentication")
    
    # Register a user
    user_data = {
        "name": "Test User",
        "email": f"test_{int(time.time())}@example.com"
    }
    make_request("POST", "/auth/register", json=user_data)
    
    # Login
    login_response = make_request("POST", "/auth/login", json={"email": user_data["email"]})
    if login_response:
        token = login_response.cookies.get('auth_token')
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        cookies = login_response.cookies
    else:
        print("Login failed, cannot continue with authenticated requests")
        return
    
    print_section("3. Book Operations (Generate Metrics)")
    
    # Get book titles (with caching)
    print("First request (cache miss):")
    make_request("GET", "/book_titles", cookies=cookies)
    
    time.sleep(0.5)
    
    print("Second request (cache hit):")
    make_request("GET", "/book_titles", cookies=cookies)
    
    # Create a book title
    book_data = {
        "title": "Monitoring in Action",
        "author": "Test Author",
        "publisher": "Test Publisher",
        "year": 2025
    }
    book_response = make_request("POST", "/book_titles", json=book_data, cookies=cookies)
    
    if book_response and book_response.status_code == 201:
        book_id = book_response.json().get('id')
        
        # Create a book copy
        copy_data = {
            "book_title_id": book_id,
            "barcode": f"TEST{int(time.time())}",
            "available": True
        }
        copy_response = make_request("POST", "/book_copies", json=copy_data, cookies=cookies)
        
        if copy_response and copy_response.status_code == 201:
            copy_id = copy_response.json().get('id')
            
            print_section("4. Borrowing Operations (Generate Business Metrics)")
            
            # Borrow a book
            due_date = (datetime.now() + timedelta(days=14)).isoformat()
            borrow_data = {
                "book_copy_id": copy_id,
                "due_date": due_date
            }
            borrow_response = make_request("POST", "/borrowings", json=borrow_data, cookies=cookies)
            
            if borrow_response and borrow_response.status_code == 201:
                borrowing_id = borrow_response.json().get('id')
                
                time.sleep(0.5)
                
                # Return the book
                make_request("POST", f"/borrowings/{borrowing_id}/return", cookies=cookies)
    
    print_section("5. Prometheus Metrics")
    
    print("GET /metrics")
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print("\nSample metrics (first 50 lines):")
    print("-" * 60)
    lines = response.text.split('\n')[:50]
    for line in lines:
        if line.strip() and not line.startswith('#'):
            print(line)
    print("-" * 60)
    print(f"\n(Total metrics lines: {len(response.text.split('\n'))})")
    
    print_section("6. Key Metrics Summary")
    
    metrics_text = response.text
    
    # Extract some key metrics
    key_metrics = [
        "http_requests_total",
        "http_request_duration_seconds",
        "cache_hits_total",
        "cache_misses_total",
        "books_borrowed_total",
        "books_returned_total",
        "user_registrations_total",
        "auth_attempts_total"
    ]
    
    for metric_name in key_metrics:
        lines = [line for line in metrics_text.split('\n') 
                if line.startswith(metric_name) and '{' in line]
        if lines:
            print(f"\n{metric_name}:")
            for line in lines[:3]:  # Show first 3 lines of each metric
                print(f"  {line}")
            if len(lines) > 3:
                print(f"  ... ({len(lines) - 3} more)")
    
    print_section("7. Log Files")
    
    print("Log files should be available at:")
    print("  - logs/book_management.log (all logs, JSON format)")
    print("  - logs/book_management_error.log (errors only, JSON format)")
    print("\nConsole output shows human-readable logs")
    print("\nSample log entry format:")
    print(json.dumps({
        "timestamp": "2025-11-20T10:15:30Z",
        "level": "INFO",
        "logger": "book_management",
        "message": "User logged in: test@example.com",
        "module": "api",
        "function": "login",
        "line": 235,
        "user_id": 1,
        "endpoint": "api.login"
    }, indent=2))
    
    print_section("8. Grafana Integration")
    
    print("To visualize these metrics in Grafana:")
    print("1. Install Prometheus and configure to scrape /metrics")
    print("2. Install Grafana and add Prometheus as data source")
    print("3. Create dashboards with queries like:")
    print("   - Request rate: rate(http_requests_total[5m])")
    print("   - Error rate: rate(http_errors_total[5m])")
    print("   - Cache hit rate: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))")
    print("   - Active borrowings: active_borrowings_total")
    
    print("\nSee LOGGING_MONITORING.md for complete setup instructions")
    
    print_section("Demo Complete!")
    print("Check the terminal console for log output")
    print("Check logs/ directory for JSON log files")
    print("Visit http://localhost:5000/metrics to see live metrics")

def demo_webhooks():
    """Demonstrate webhook features"""
    
    print_section("Webhook Management")
    
    # Get current webhooks
    print("GET /webhooks")
    response = requests.get(f"{BASE_URL}/webhooks")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Add a webhook (using webhook.site for testing)
    print("POST /webhooks")
    webhook_data = {"url": "https://webhook.site/test-endpoint"}
    response = requests.post(f"{BASE_URL}/webhooks", json=webhook_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Send test webhook
    print("POST /webhooks/test")
    response = requests.post(f"{BASE_URL}/webhooks/test")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    print("\nWebhook notifications are sent for:")
    print("  - book_borrowed: When a book is borrowed")
    print("  - book_returned: When a book is returned")
    print("  - user_registered: When a new user registers")
    print("  - system_health: Test notifications")
    print("\nAll webhooks are sent asynchronously (non-blocking)")
    print("Check your webhook.site URL to see the notifications!")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Book Management System v14 - Monitoring & Webhook Demo    ║
╚══════════════════════════════════════════════════════════════╝

This demo will:
- Make various API requests to generate logs and metrics
- Show how to view Prometheus metrics
- Demonstrate structured logging
- Test webhook notifications

Make sure the Flask application is running on http://localhost:5000
Press Ctrl+C to cancel, or Enter to continue...
    """)
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nDemo cancelled")
        exit(0)
    try:
        demo_webhooks()
        demo_monitoring()
    except Exception as e:
        print(f"\nError running demo: {e}")
        print("\nMake sure the Flask application is running:")
        print("  python -m book_management_flask_v14.run")
        
        
        
        
