import requests
import json
from datetime import datetime, timezone

# Advanced test for logs endpoint pagination
base_url = "http://localhost:5000"

def test_advanced_pagination():
    print("Testing advanced pagination scenarios...")
    
    try:
        # Test 1: Different page sizes
        print("\n=== Testing different page sizes ===")
        for limit in [2, 5, 10]:
            response = requests.get(f"{base_url}/api/logs?limit={limit}&page=1")
            if response.status_code == 200:
                data = response.json()
                print(f"Limit {limit}: Got {len(data['logs'])} logs, Total: {data['pagination']['total']}, Pages: {data['pagination']['total_pages']}")
        
        # Test 2: Navigate through pages
        print("\n=== Testing page navigation ===")
        limit = 3
        for page in [1, 2, 3]:
            response = requests.get(f"{base_url}/api/logs?limit={limit}&page={page}")
            if response.status_code == 200:
                data = response.json()
                pagination = data['pagination']
                print(f"Page {page}: {len(data['logs'])} logs, Skip: {pagination['skip']}, Has more: {pagination['has_more']}")
                if data['logs']:
                    print(f"  First log timestamp: {data['logs'][0]['timestamp']}")
        
        # Test 3: Skip parameter vs Page parameter
        print("\n=== Testing skip vs page parameters ===")
        # Using skip directly
        response = requests.get(f"{base_url}/api/logs?limit=5&skip=10")
        if response.status_code == 200:
            data = response.json()
            print(f"Skip 10: Page {data['pagination']['page']}, Skip {data['pagination']['skip']}")
        
        # Using page (should calculate skip automatically)
        response = requests.get(f"{base_url}/api/logs?limit=5&page=3")
        if response.status_code == 200:
            data = response.json()
            print(f"Page 3: Page {data['pagination']['page']}, Skip {data['pagination']['skip']}")
        
        # Test 4: Filter by log level with pagination
        print("\n=== Testing log level filtering with pagination ===")
        for level in ['INFO', 'ERROR', 'DEBUG']:
            response = requests.get(f"{base_url}/api/logs?level={level}&limit=5&page=1")
            if response.status_code == 200:
                data = response.json()
                print(f"Level {level}: {len(data['logs'])} logs, Total: {data['pagination']['total']}")
                if data['logs']:
                    levels = [log['level'] for log in data['logs']]
                    print(f"  Actual levels: {set(levels)}")
        
        # Test 5: Date filtering
        print("\n=== Testing date filtering ===")
        # Get current time and use it as 'before' parameter
        now = datetime.now(timezone.utc).isoformat()
        response = requests.get(f"{base_url}/api/logs?before={now}&limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"Before {now[:19]}: {len(data['logs'])} logs")
        
        # Test 6: Edge cases
        print("\n=== Testing edge cases ===")
        
        # Very large page number
        response = requests.get(f"{base_url}/api/logs?limit=5&page=1000")
        if response.status_code == 200:
            data = response.json()
            print(f"Page 1000: {len(data['logs'])} logs, Has more: {data['pagination']['has_more']}")
        
        # Zero limit (should use default)
        response = requests.get(f"{base_url}/api/logs?limit=0")
        if response.status_code == 200:
            data = response.json()
            print(f"Limit 0: Got {len(data['logs'])} logs (should use default)")
        
        # Negative page (should handle gracefully)
        response = requests.get(f"{base_url}/api/logs?page=-1")
        print(f"Negative page response status: {response.status_code}")
        
        print("\n=== Testing complete! ===")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_advanced_pagination() 