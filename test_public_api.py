"""
Test Public API Endpoints
Tests deployed API with JSON requests/responses
"""
import httpx
import json
import sys

def test_public_api(base_url: str):
    """Test all public API endpoints"""
    
    print("\n" + "="*70)
    print(f"🌐 Testing Public API: {base_url}")
    print("="*70 + "\n")
    
    try:
        # Test 1: Root Endpoint
        print("1️⃣  Testing Root Endpoint (GET /)")
        print("-" * 70)
        response = httpx.get(f"{base_url}/", timeout=30.0)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Response:\n{json.dumps(response.json(), indent=2)}\n")
        
        # Test 2: Health Check
        print("2️⃣  Testing Health Endpoint (GET /health)")
        print("-" * 70)
        response = httpx.get(f"{base_url}/health", timeout=30.0)
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"📊 Status: {data['status']}")
        print(f"⏱️  Uptime: {data['uptime_human']}")
        print(f"👥 Customers Loaded: {data['customers_loaded']}")
        print(f"💳 Transactions Loaded: {data['transactions_loaded']}")
        print(f"🌍 Environment: {data.get('environment', 'N/A')}\n")
        
        # Test 3: Metrics
        print("3️⃣  Testing Metrics Endpoint (GET /metrics)")
        print("-" * 70)
        response = httpx.get(f"{base_url}/metrics", timeout=30.0)
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"📊 Total Customers: {data['total_customers']}")
        print(f"📈 Segment Distribution:")
        for segment, count in data['segment_distribution'].items():
            print(f"   - {segment}: {count}")
        print()
        
        # Test 4: Analyze Customer (JSON Request/Response)
        print("4️⃣  Testing Analyze Endpoint (POST /analyze)")
        print("-" * 70)
        
        # JSON Request
        request_data = {
            "customer_id": "CUST000001",
            "include_history": False
        }
        
        print(f"📤 Request (JSON):\n{json.dumps(request_data, indent=2)}")
        
        response = httpx.post(
            f"{base_url}/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # JSON Response
            data = response.json()
            print(f"\n📥 Response (JSON):")
            print(json.dumps(data, indent=2))
            print(f"\n🎯 Key Insights:")
            print(f"   - Customer: {data['customer_id']}")
            print(f"   - Segment: {data['segment']}")
            print(f"   - Retention: {data['predicted_retention']:.2%}")
            print(f"   - Churn Risk: {data['churn_risk']}")
            print(f"   - Recommended Reward: {data['recommended_reward']}")
            print(f"   - Confidence: {data.get('confidence', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
        
        print("\n" + "="*70)
        print("✅ All Tests Completed Successfully!")
        print("="*70 + "\n")
        
        return True
        
    except httpx.ConnectError:
        print(f"\n❌ ERROR: Cannot connect to {base_url}")
        print("   Make sure the API server is running!")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def print_curl_examples(base_url: str):
    """Print curl command examples"""
    print("\n" + "="*70)
    print("📚 CURL Command Examples")
    print("="*70 + "\n")
    
    print("1️⃣  Health Check:")
    print(f"   curl {base_url}/health\n")
    
    print("2️⃣  Get Metrics:")
    print(f"   curl {base_url}/metrics\n")
    
    print("3️⃣  Analyze Customer (JSON):")
    print(f'   curl -X POST {base_url}/analyze \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"customer_id": "CUST000001"}}\'')
    
    print("\n" + "="*70 + "\n")


def print_python_example(base_url: str):
    """Print Python integration example"""
    print("\n" + "="*70)
    print("🐍 Python Integration Example")
    print("="*70 + "\n")
    
    example_code = f'''import requests
import json

# API Base URL
BASE_URL = "{base_url}"

# Example 1: Analyze a customer
def analyze_customer(customer_id):
    response = requests.post(
        f"{{BASE_URL}}/analyze",
        json={{"customer_id": customer_id}},
        headers={{"Content-Type": "application/json"}}
    )
    return response.json()

# Example 2: Get health status
def get_health():
    response = requests.get(f"{{BASE_URL}}/health")
    return response.json()

# Usage
result = analyze_customer("CUST000001")
print(f"Recommended Reward: {{result['recommended_reward']}}")
print(f"Retention Probability: {{result['predicted_retention']:.2%}}")
'''
    
    print(example_code)
    print("="*70 + "\n")


if __name__ == "__main__":
    # Default to localhost, or accept URL as argument
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip('/')
    else:
        BASE_URL = "http://127.0.0.1:8000"
    
    print("\n🚀 API Public Endpoint Tester")
    print(f"Base URL: {BASE_URL}\n")
    
    # Run tests
    success = test_public_api(BASE_URL)
    
    if success:
        # Show integration examples
        print_curl_examples(BASE_URL)
        print_python_example(BASE_URL)
        
        print("💡 TIP: To test with your deployed URL, run:")
        print(f"   python {__file__} https://your-api-url.com\n")
