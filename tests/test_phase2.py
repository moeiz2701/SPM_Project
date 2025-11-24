import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("\n" + "="*50)
    print("Testing Health Endpoint...")
    print("="*50)
    
    response = httpx.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Health check passed!")

def test_metrics():
    print("\n" + "="*50)
    print("Testing Metrics Endpoint...")
    print("="*50)
    
    response = httpx.get(f"{BASE_URL}/metrics")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Metrics endpoint passed!")

def test_analyze():
    print("\n" + "="*50)
    print("Testing Analyze Endpoint...")
    print("="*50)
    
    # Use actual customer ID format from generated data
    customer_data = {
        "customer_id": "CUST000001"
    }
    
    response = httpx.post(f"{BASE_URL}/analyze", json=customer_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    
    result = response.json()
    assert "customer_id" in result
    assert "recommended_reward" in result
    assert "predicted_retention" in result
    print("✅ Analyze endpoint passed!")

def test_cache():
    print("\n" + "="*50)
    print("Testing Cache Functionality...")
    print("="*50)
    
    # Use actual customer ID format from generated data
    customer_data = {
        "customer_id": "CUST000002"
    }
    
    # First request (should not be cached)
    response1 = httpx.post(f"{BASE_URL}/analyze", json=customer_data)
    result1 = response1.json()
    print(f"First Request - Customer: {result1.get('customer_id')}")
    print(f"First Request - Retention: {result1.get('predicted_retention')}")
    
    # Second request (should be cached)
    time.sleep(0.5)
    response2 = httpx.post(f"{BASE_URL}/analyze", json=customer_data)
    result2 = response2.json()
    print(f"Second Request - Customer: {result2.get('customer_id')}")
    print(f"Second Request - Retention: {result2.get('predicted_retention')}")
    
    assert result1["customer_id"] == result2["customer_id"]
    print("✅ Cache test passed!")

def test_registry():
    print("\n" + "="*50)
    print("Testing Root/Registry Info Endpoint...")
    print("="*50)
    
    # Test root endpoint which provides API info
    response = httpx.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result or "version" in result
    print("✅ Root endpoint passed!")
    
    # Test register endpoint (POST)
    print("\nTesting Register Endpoint...")
    register_data = {
        "supervisor_url": "http://supervisor.example.com:9000",
        "agent_metadata": {"test": "true"}
    }
    response = httpx.post(f"{BASE_URL}/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Register endpoint passed!")

if __name__ == "__main__":
    print("\n🚀 Starting API Tests...")
    print("Make sure the API server is running on http://127.0.0.1:8000")
    print("\nWaiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    try:
        test_health()
        test_metrics()
        test_analyze()
        test_cache()
        test_registry()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("="*50)
        
    except httpx.ConnectError:
        print("\n❌ ERROR: Cannot connect to API server!")
        print("Make sure the server is running with:")
        print("  python run_api.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")