"""
Test script for Loyalty AI Agent Public API
Tests all endpoints deployed on Railway

Run with: python test_railway_api.py
"""

import json
from datetime import datetime

# API Base URL - Update this with your Railway deployment URL
BASE_URL = "https://web-production-37e1.up.railway.app"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_response(response):
    """Print formatted API response"""
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success!")
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ Failed!")
        print(f"Error: {response.text}")

def test_root():
    """Test root endpoint"""
    print_section("1. Testing Root Endpoint (GET /)")
    try:
        import requests
        response = requests.get(f"{BASE_URL}/", verify=False)
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    """Test health check endpoint"""
    print_section("2. Testing Health Check (GET /health)")
    try:
        import requests
        response = requests.get(f"{BASE_URL}/health", verify=False)
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_metrics():
    """Test metrics endpoint"""
    print_section("3. Testing Metrics (GET /metrics)")
    try:
        import requests
        response = requests.get(f"{BASE_URL}/metrics", verify=False)
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_analyze_customer():
    """Test analyze customer endpoint"""
    print_section("4. Testing Analyze Customer (POST /analyze)")
    try:
        import requests
        
        # Test basic analysis
        payload = {
            "customer_id": "CUST000001",
            "include_history": False
        }
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False
        )
        print_response(response)
        
        # Test with different customer
        print("\n--- Testing with CUST000050 ---")
        payload = {
            "customer_id": "CUST000050",
            "include_history": False
        }
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False
        )
        print_response(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_invalid_customer():
    """Test error handling with invalid customer"""
    print_section("5. Testing Error Handling (Invalid Customer)")
    try:
        import requests
        payload = {
            "customer_id": "CUST999999",  # Valid format but doesn't exist
            "include_history": False
        }
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False
        )
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}")

def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀"*35)
    print("  LOYALTY AI AGENT - PUBLIC API TEST SUITE")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀"*35)
    
    # Run all tests
    test_root()
    test_health()
    test_metrics()
    test_analyze_customer()
    test_invalid_customer()
    
    print("\n" + "="*70)
    print("  ✅ ALL TESTS COMPLETED!")
    print("="*70 + "\n")

if __name__ == "__main__":
    print("\nChecking for required packages...")
    try:
        import requests
        print("✅ requests library found")
    except ImportError:
        import subprocess
        import sys
        print("Installing requests library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        print("✅ requests library installed")
    
    # Disable SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Run the test suite
    run_all_tests()
