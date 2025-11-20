"""
API Versioning Examples
Demonstrates how to use v1 (deprecated) and v2 (current) APIs
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# ============================================
# EXAMPLE 1: Detecting Deprecation
# ============================================

def example_detect_deprecation():
    """
    Example: How to detect when you're using a deprecated API
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Detecting Deprecated API Usage")
    print("="*70)
    
    # Get authentication token first
    # (In production, you'd have this from your login flow)
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "test@example.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    
    # Call v1 API (deprecated)
    print("\nCalling v1 API: GET /api/book_copies")
    response = requests.get(f"{BASE_URL}/api/book_copies", cookies=cookies)
    
    # Check for deprecation headers
    if response.headers.get('Deprecation') == 'true':
        print("\nDEPRECATION WARNING DETECTED!")
        print(f"  Sunset Date: {response.headers.get('Sunset')}")
        print(f"  Replacement: {response.headers.get('Link')}")
        print(f"  Warning: {response.headers.get('Warning')}")
        print("\nACTION REQUIRED: Migrate to v2 API")
    
    print("\ TIP: Set up monitoring to alert on deprecation headers!")

# ============================================
# EXAMPLE 2: Migrating from v1 to v2
# ============================================

def example_migration():
    """
    Example: Side-by-side comparison of v1 vs v2
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Migrating from v1 to v2")
    print("="*70)
    
    # Setup
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "test@example.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    
    # v1 way (deprecated)
    print("\nOLD WAY (v1 - Deprecated):")
    print("   GET /api/book_copies")
    response_v1 = requests.get(f"{BASE_URL}/api/book_copies", cookies=cookies)
    data_v1 = response_v1.json()
    
    print("\n   Response structure:")
    print(f"   - Root keys: {list(data_v1.keys())}")
    if data_v1.get('items'):
        print(f"   - Item keys: {list(data_v1['items'][0].keys())}")
    
    # v2 way (current)
    print("\nNEW WAY (v2 - Current):")
    print("   GET /api/v2/book-copies")
    response_v2 = requests.get(f"{BASE_URL}/api/v2/book-copies", cookies=cookies)
    data_v2 = response_v2.json()
    
    print("\n   Response structure:")
    print(f"   - Root keys: {list(data_v2.keys())}")
    if data_v2.get('data'):
        print(f"   - Item keys: {list(data_v2['data'][0].keys())}")
        print(f"   - Has embedded book title: {'bookTitle' in data_v2['data'][0]}")
        print(f"   - Has borrowing status: {'borrowingStatus' in data_v2['data'][0]}")

# ============================================
# EXAMPLE 3: Using v2 Enhanced Features
# ============================================

def example_v2_features():
    """
    Example: How to use v2's new features
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Using v2 Enhanced Features")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "test@example.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    
    # Feature 1: Advanced filtering
    print("\nFeature 1: Advanced Filtering")
    print("   GET /api/v2/book-copies?available=true&condition=Good")
    response = requests.get(
        f"{BASE_URL}/api/v2/book-copies?available=true&condition=Good",
        cookies=cookies
    )
    print(f"   Status: {response.status_code}")
    print(f"   Found {len(response.json().get('data', []))} available books in good condition")
    
    # Feature 2: Get single resource
    print("\nFeature 2: Get Single Resource")
    print("   GET /api/v2/book-copies/1")
    response = requests.get(f"{BASE_URL}/api/v2/book-copies/1", cookies=cookies)
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   Retrieved book copy:")
        print(f"      - Barcode: {data.get('barcode')}")
        print(f"      - Book: {data.get('bookTitle', {}).get('title')}")
        print(f"      - Status: {'Borrowed' if data['borrowingStatus']['isBorrowed'] else 'Available'}")
    
    # Feature 3: PATCH for partial updates
    print("\nFeature 3: Partial Update (PATCH)")
    print("   PATCH /api/v2/book-copies/1")
    response = requests.patch(
        f"{BASE_URL}/api/v2/book-copies/1",
        json={"condition": "Good"},
        cookies=cookies
    )
    if response.status_code == 200:
        print("   Updated successfully")
        updated_data = response.json()['data']
        print(f"   New condition: {updated_data.get('condition')}")

# ============================================
# EXAMPLE 4: Embedded Data Benefits
# ============================================

def example_embedded_data():
    """
    Example: How v2 embedded data reduces API calls
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Embedded Data Benefits")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "test@example.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    
    # v1 approach: Need multiple calls
    print("\nv1 Approach (Deprecated):")
    print("   Step 1: Get book copies")
    response = requests.get(f"{BASE_URL}/api/book_copies?size=3", cookies=cookies)
    copies_v1 = response.json()['items']
    
    print(f"   Step 2: Get book title for each copy ({len(copies_v1)} API calls)")
    for copy in copies_v1:
        response = requests.get(
            f"{BASE_URL}/api/book_titles/{copy['book_title_id']}", 
            cookies=cookies
        )
        title = response.json()
        print(f"      - Copy {copy['barcode']}: {title.get('title')}")
    
    print(f"\n Total API calls: {1 + len(copies_v1)}")
    
    # v2 approach: Single call
    print("\nv2 Approach (Current):")
    print("   Step 1: Get book copies (with embedded titles)")
    response = requests.get(f"{BASE_URL}/api/v2/book-copies?size=3", cookies=cookies)
    copies_v2 = response.json()['data']
    
    for copy in copies_v2:
        book_title = copy.get('bookTitle', {})
        print(f"      - Copy {copy['barcode']}: {book_title.get('title')}")
    
    print(f"\n Total API calls: 1")
    print(f"   Reduced API calls by {len(copies_v1)}x!")

# ============================================
# EXAMPLE 5: Error Handling
# ============================================

def example_error_handling():
    """
    Example: Enhanced error handling in v2
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Enhanced Error Handling in v2")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "test@example.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    
    # Try to create book copy with missing fields
    print("\nTest: Create book copy with missing required field")
    print("   POST /api/v2/book-copies")
    print("   Body: {\"barcode\": \"TEST\"}")  # Missing bookTitleId
    
    response = requests.post(
        f"{BASE_URL}/api/v2/book-copies",
        json={"barcode": "TEST"},
        cookies=cookies
    )
    
    if response.status_code == 400:
        error = response.json()['error']
        print(f"\n   Got structured error response:")
        print(f"   - Error code: {error['code']}")
        print(f"   - Message: {error['message']}")
        print(f"   - Details: {json.dumps(error.get('details', {}), indent=6)}")
        print("\n   v2 provides actionable error information!")

# ============================================
# EXAMPLE 6: Production Monitoring
# ============================================

def example_monitoring_wrapper():
    """
    Example: Wrapper function for production monitoring
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Production Monitoring Pattern")
    print("="*70)
    
    print("\ Recommended pattern for production:")
    
    code = '''
class ApiClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.deprecation_count = 0
    
    def request(self, method, path, **kwargs):
        """Wrapper that monitors for deprecation"""
        url = f"{self.base_url}{path}"
        cookies = {'auth_token': self.token}
        
        response = requests.request(method, url, cookies=cookies, **kwargs)
        
        # Check for deprecation
        if response.headers.get('Deprecation') == 'true':
            self.deprecation_count += 1
            
            # Log to monitoring system
            print(f"DEPRECATION WARNING:")
            print(f"   Path: {path}")
            print(f"   Sunset: {response.headers.get('Sunset')}")
            print(f"   Replacement: {response.headers.get('Link')}")
            
            # Send alert if threshold exceeded
            if self.deprecation_count > 100:
                self.send_alert(f"High deprecation usage: {self.deprecation_count} calls")
        
        return response
    
    def send_alert(self, message):
        """Send alert to monitoring system (implement as needed)"""
        print(f"🚨 ALERT: {message}")

# Usage
client = ApiClient("http://localhost:5000", "your-token")
response = client.request("GET", "/api/book_copies")
'''
    
    print(code)

# ============================================
# EXAMPLE 7: Feature Flag Migration
# ============================================

def example_feature_flag():
    """
    Example: Using feature flags for safe migration
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Feature Flag Pattern for Safe Migration")
    print("="*70)
    
    print("\ Recommended pattern for gradual rollout:")
    
    code = '''
class FeatureFlags:
    USE_API_V2 = True  # Toggle this for rollback
    
class BookCopyService:
    def get_book_copies(self, filters=None):
        if FeatureFlags.USE_API_V2:
            # Use v2 API
            response = requests.get(
                f"{BASE_URL}/api/v2/book-copies",
                params=filters,
                cookies=cookies
            )
            data = response.json()
            return data['data']
        else:
            # Fallback to v1 (deprecated)
            response = requests.get(
                f"{BASE_URL}/api/book_copies",
                params=filters,
                cookies=cookies
            )
            data = response.json()
            return data['items']

# Benefits:
# Can quickly rollback if issues found
# Gradual rollout (10% → 50% → 100%)
# A/B testing possible
# Monitoring both versions simultaneously
'''
    
    print(code)

# ============================================
# MAIN
# ============================================

def run_all_examples():
    """Run all examples"""
    print("\n")
    print("" + "="*68)
    print(" API VERSIONING EXAMPLES")
    print(" Practical examples for developers")
    print("" + "="*68)
    
    try:
        example_detect_deprecation()
        example_migration()
        example_v2_features()
        example_embedded_data()
        example_error_handling()
        example_monitoring_wrapper()
        example_feature_flag()
        
        print("\n" + "="*70)
        print("All examples completed!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Review API_VERSIONING.md for complete guide")
        print("  2. Run test_api_versioning.py for automated tests")
        print("  3. Start migrating your code to v2")
        print("  4. Set up deprecation monitoring in production")
        print("\nRemember: v1 sunset date is June 1, 2026")
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        print("   Make sure the server is running on http://localhost:5000")

if __name__ == "__main__":
    run_all_examples()
