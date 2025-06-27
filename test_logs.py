import requests
import json
import time

# Test the logs endpoint with pagination
base_url = "http://localhost:5000"

def test_logs_endpoint():
    print("Testing logs endpoint with pagination...")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        # Test 1: Basic logs request
        print("\n1. Testing basic logs request...")
        response = requests.get(f"{base_url}/api/logs?limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            if 'logs' in data:
                print(f"Number of logs: {len(data['logs'])}")
            if 'pagination' in data:
                print(f"Pagination info: {data['pagination']}")
        else:
            print(f"Response: {response.text}")
        
        # Test 2: Pagination with page parameter
        print("\n2. Testing pagination with page parameter...")
        response = requests.get(f"{base_url}/api/logs?limit=3&page=1")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Page 1 - Number of logs: {len(data.get('logs', []))}")
            print(f"Pagination: {data.get('pagination', {})}")
        else:
            print(f"Response: {response.text}")
        
        # Test 3: Filter by log level
        print("\n3. Testing filter by log level...")
        response = requests.get(f"{base_url}/api/logs?level=INFO&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"INFO logs count: {len(data.get('logs', []))}")
            if data.get('logs'):
                print(f"First log level: {data['logs'][0].get('level')}")
        else:
            print(f"Response: {response.text}")
        
        # Test 4: Simple logs endpoint (backward compatibility)
        print("\n4. Testing simple logs endpoint...")
        response = requests.get(f"{base_url}/api/logs/simple?limit=3")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Simple format - Number of logs: {len(data)}")
            if data:
                print(f"First log keys: {list(data[0].keys())}")
        else:
            print(f"Response: {response.text}")
        
        # Test 5: Health check to ensure server is running
        print("\n5. Testing health check...")
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health status: {data.get('status')}")
            print(f"Database status: {data.get('database')}")
        else:
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_logs_endpoint() 