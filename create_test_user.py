#!/usr/bin/env python3
"""
Script to create the test user test@csaaudit.com with basic plan for upgrade testing
"""

import requests
import json
import bcrypt
from datetime import datetime, timezone, timedelta

def create_test_user():
    base_url = "https://safesitepro-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # First, login as admin
    print("🔐 Logging in as admin...")
    admin_login = {
        "email": "admin@csaaudit.com",
        "password": "admin123"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=admin_login, timeout=10)
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        return False
    
    admin_data = response.json()
    admin_token = admin_data["access_token"]
    print("✅ Admin login successful")
    
    # Create test user using registration endpoint
    print("👤 Creating test user...")
    test_user_data = {
        "email": "test@csaaudit.com",
        "name": "Test User",
        "password": "test123"
    }
    
    response = requests.post(f"{api_url}/auth/register", json=test_user_data, timeout=10)
    if response.status_code == 200:
        print("✅ Test user created successfully")
        user_data = response.json()
        test_user_id = user_data["user"]["id"]
        
        # Update user to have basic plan
        print("💳 Setting basic subscription plan...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Use admin endpoint to update user subscription
        update_data = {
            "subscription_plan": "basic",
            "subscription_expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "audits_used_this_month": 5  # Some usage to simulate real user
        }
        
        response = requests.put(f"{api_url}/admin/user/{test_user_id}", 
                              json=update_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Test user updated with basic plan")
            return True
        else:
            print(f"⚠️ Failed to update user plan: {response.status_code}")
            return True  # User created, just without plan
            
    elif response.status_code == 400:
        # User might already exist
        print("⚠️ Test user might already exist, trying to login...")
        login_data = {
            "email": "test@csaaudit.com",
            "password": "test123"
        }
        
        response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ Test user already exists and login works")
            return True
        else:
            print(f"❌ Test user exists but login failed: {response.status_code}")
            return False
    else:
        print(f"❌ Failed to create test user: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"Response: {response.text[:200]}")
        return False

if __name__ == "__main__":
    success = create_test_user()
    if success:
        print("\n🎉 Test user setup complete!")
        print("📧 Email: test@csaaudit.com")
        print("🔑 Password: test123")
        print("💳 Plan: basic (if successfully updated)")
    else:
        print("\n❌ Test user setup failed!")