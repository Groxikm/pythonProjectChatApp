import requests
import json

# Test the join_group endpoint with invalid parameters
base_url = "http://localhost:5000"

def test_join_group_validation():
    print("Testing join_group endpoint validation...")
    
    # Test 1: undefined group_id
    print("\n1. Testing with undefined group_id...")
    response = requests.post(f"{base_url}/api/groups/undefined/members/507f1f77bcf86cd799439011")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: undefined user_id
    print("\n2. Testing with undefined user_id...")
    response = requests.post(f"{base_url}/api/groups/507f1f77bcf86cd799439011/members/undefined")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: invalid ObjectId format
    print("\n3. Testing with invalid ObjectId format...")
    response = requests.post(f"{base_url}/api/groups/invalid_id/members/507f1f77bcf86cd799439011")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: empty group_id
    print("\n4. Testing with empty group_id...")
    response = requests.post(f"{base_url}/api/groups//members/507f1f77bcf86cd799439011")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_join_group_validation() 