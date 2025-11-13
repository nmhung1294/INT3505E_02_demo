"""
Quick Demo Script - API Versioning
Run this for a quick demonstration of v1 vs v2
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def demo():
    print("\n" + "="*70)
    print("🚀 API Versioning Quick Demo")
    print("="*70)
    
    # 1. Setup
    print("\n📝 Step 1: Creating test user and logging in...")
    try:
        requests.post(f"{BASE_URL}/api/auth/register", 
                     json={"name": "Demo User", "email": "demo@test.com"})
    except:
        pass
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                            json={"email": "demo@test.com"})
    token = response.cookies.get('auth_token')
    cookies = {'auth_token': token}
    print("   ✅ Logged in successfully")
    
    # 2. Create test book title
    print("\n📚 Step 2: Creating test book...")
    book_response = requests.post(
        f"{BASE_URL}/api/book_titles",
        json={
            "title": "API Design Patterns",
            "author": "John Doe",
            "publisher": "Tech Press",
            "year": 2025
        },
        cookies=cookies
    )
    
    if book_response.status_code == 201:
        book_id = book_response.json()['id']
        print(f"   ✅ Book created with ID: {book_id}")
    else:
        # Use existing
        books = requests.get(f"{BASE_URL}/api/book_titles", cookies=cookies)
        book_id = books.json()['items'][0]['id']
        print(f"   ✅ Using existing book with ID: {book_id}")
    
    # 3. Test v1 (Deprecated)
    print("\n" + "="*70)
    print("⚠️  Testing v1 API (DEPRECATED)")
    print("="*70)
    
    print("\n📞 POST /api/book_copies (v1)")
    v1_response = requests.post(
        f"{BASE_URL}/api/book_copies",
        json={
            "book_title_id": book_id,
            "barcode": "DEMO-V1-001",
            "condition": "Good"
        },
        cookies=cookies
    )
    
    print(f"   Status: {v1_response.status_code}")
    print(f"   Response: {json.dumps(v1_response.json(), indent=6)}")
    
    # Check deprecation headers
    print("\n🔍 Checking Deprecation Headers:")
    print(f"   Deprecation: {v1_response.headers.get('Deprecation')}")
    print(f"   Sunset: {v1_response.headers.get('Sunset')}")
    print(f"   Link: {v1_response.headers.get('Link')}")
    print(f"   Warning: {v1_response.headers.get('Warning')}")
    
    print("\n   ⚠️  NOTICE: This API is deprecated and will be removed!")
    
    # 4. Test v2 (Current)
    print("\n" + "="*70)
    print("✅ Testing v2 API (CURRENT)")
    print("="*70)
    
    print("\n📞 POST /api/v2/book-copies (v2)")
    v2_response = requests.post(
        f"{BASE_URL}/api/v2/book-copies",
        json={
            "bookTitleId": book_id,  # Note: camelCase!
            "barcode": "DEMO-V2-001",
            "condition": "Good"
        },
        cookies=cookies
    )
    
    print(f"   Status: {v2_response.status_code}")
    print(f"   Location: {v2_response.headers.get('Location')}")
    
    v2_data = v2_response.json()
    print(f"\n   Response (enhanced format):")
    print(f"   {json.dumps(v2_data, indent=6)[:800]}...")
    
    copy_id = v2_data['data']['id']
    
    # 5. Compare List endpoints
    print("\n" + "="*70)
    print("📊 Comparing List Endpoints")
    print("="*70)
    
    print("\n❌ v1: GET /api/book_copies")
    v1_list = requests.get(f"{BASE_URL}/api/book_copies?size=2", cookies=cookies)
    v1_list_data = v1_list.json()
    print(f"   Response keys: {list(v1_list_data.keys())}")
    print(f"   Item keys: {list(v1_list_data['items'][0].keys()) if v1_list_data.get('items') else 'None'}")
    print(f"   Has embedded book info? NO ❌")
    
    print("\n✅ v2: GET /api/v2/book-copies")
    v2_list = requests.get(f"{BASE_URL}/api/v2/book-copies?size=2", cookies=cookies)
    v2_list_data = v2_list.json()
    print(f"   Response keys: {list(v2_list_data.keys())}")
    if v2_list_data.get('data'):
        print(f"   Item keys: {list(v2_list_data['data'][0].keys())}")
        print(f"   Has embedded book info? YES ✅")
        print(f"   Book title: {v2_list_data['data'][0].get('bookTitle', {}).get('title')}")
    
    # 6. Test v2 filtering
    print("\n" + "="*70)
    print("🔍 Testing v2 Advanced Filtering (NEW)")
    print("="*70)
    
    print("\n📞 GET /api/v2/book-copies?available=true&condition=Good")
    filtered = requests.get(
        f"{BASE_URL}/api/v2/book-copies?available=true&condition=Good",
        cookies=cookies
    )
    print(f"   Status: {filtered.status_code}")
    print(f"   Found {len(filtered.json().get('data', []))} matching copies")
    
    # 7. Test v2 PATCH
    print("\n" + "="*70)
    print("✏️  Testing v2 PATCH (NEW)")
    print("="*70)
    
    print(f"\n📞 PATCH /api/v2/book-copies/{copy_id}")
    patch_response = requests.patch(
        f"{BASE_URL}/api/v2/book-copies/{copy_id}",
        json={"condition": "Damaged"},
        cookies=cookies
    )
    print(f"   Status: {patch_response.status_code}")
    print(f"   Updated condition: {patch_response.json()['data']['condition']}")
    
    # 8. Summary
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    print("\n✅ v2 Advantages:")
    print("   • Embedded book title info (fewer API calls)")
    print("   • Advanced filtering capabilities")
    print("   • PATCH support for partial updates")
    print("   • Structured error responses")
    print("   • Real-time borrowing status")
    print("   • RESTful design (kebab-case URLs)")
    
    print("\n⚠️  v1 Deprecation:")
    print("   • Sunset date: June 1, 2026")
    print("   • 7 months to migrate")
    print("   • Deprecation headers present")
    
    print("\n📚 Next Steps:")
    print("   1. Read API_VERSIONING.md for full guide")
    print("   2. Run test_api_versioning.py for detailed tests")
    print("   3. Try api_versioning_examples.py for more examples")
    print("   4. Use MIGRATION_CHECKLIST.md to track progress")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        demo()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("   Make sure the server is running on http://localhost:5000")
        print("   Run: python -m book_management_flask_v12.run")
