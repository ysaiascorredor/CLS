#!/usr/bin/env python3
"""
Quick test of admin endpoints with admin credentials
"""
import requests
import json

def test_admin_endpoints():
    base_url = "https://safetyscan-5.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔐 Testing Admin Endpoints with Admin Credentials")
    print("=" * 60)
    
    # Login with admin credentials
    login_data = {
        "email": "admin@csaaudit.com",
        "password": "admin123"
    }
    
    print("Step 1: Admin Login...")
    response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        return
    
    data = response.json()
    admin_token = data.get("access_token")
    user_data = data.get("user", {})
    
    print(f"✅ Admin login successful")
    print(f"   Role: {user_data.get('role')}")
    print(f"   Email: {user_data.get('email')}")
    
    if not admin_token:
        print("❌ No admin token received")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test admin dashboard
    print("\nStep 2: Testing GET /api/admin/dashboard...")
    response = requests.get(f"{api_url}/admin/dashboard", headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Admin Dashboard - Status: {response.status_code}")
        print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        print(f"   Data length: {len(data) if data else 0}")
    else:
        print(f"❌ Admin Dashboard - Status: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
        except:
            print(f"   Response: {response.text[:200]}")
    
    # Test admin users
    print("\nStep 3: Testing GET /api/admin/users...")
    response = requests.get(f"{api_url}/admin/users", headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Admin Users - Status: {response.status_code}")
        if isinstance(data, list):
            print(f"   Users count: {len(data)}")
            if data:
                first_user = data[0]
                print(f"   First user fields: {list(first_user.keys())}")
                print(f"   No password exposed: {'password_hash' not in first_user}")
        elif isinstance(data, dict):
            print(f"   Response keys: {list(data.keys())}")
    else:
        print(f"❌ Admin Users - Status: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
        except:
            print(f"   Response: {response.text[:200]}")
    
    print("\n" + "=" * 60)
    print("Admin endpoint testing complete!")

if __name__ == "__main__":
    test_admin_endpoints()