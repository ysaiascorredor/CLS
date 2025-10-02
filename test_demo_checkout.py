#!/usr/bin/env python3
"""
Test script for demo checkout functionality
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8001/api"
TEST_USER = {
    "email": "demo@test.com",
    "name": "Demo User",
    "password": "testpass123"
}

def test_demo_checkout():
    print("🧪 Testing Demo Checkout Functionality")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    
    if register_response.status_code == 200:
        print("✅ User registered successfully")
        auth_data = register_response.json()
        access_token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
    elif register_response.status_code == 400 and "already registered" in register_response.text:
        print("ℹ️  User already exists, logging in...")
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        if login_response.status_code == 200:
            auth_data = login_response.json()
            access_token = auth_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print("✅ User logged in successfully")
        else:
            print(f"❌ Login failed: {login_response.text}")
            return
    else:
        print(f"❌ Registration failed: {register_response.text}")
        return
    
    # Step 2: Test demo checkout session creation
    print("\n2. Creating demo checkout session...")
    checkout_data = {
        "package_id": "basic",
        "origin_url": "http://localhost:3000"
    }
    
    checkout_response = requests.post(
        f"{BASE_URL}/payments/checkout/session",
        json=checkout_data,
        headers=headers
    )
    
    if checkout_response.status_code == 200:
        checkout_result = checkout_response.json()
        print("✅ Demo checkout session created successfully")
        print(f"   Session ID: {checkout_result.get('session_id')}")
        print(f"   Demo URL: {checkout_result.get('url')}")
        
        session_id = checkout_result.get('session_id')
        
        # Step 3: Check checkout status (should be demo mode)
        print("\n3. Checking checkout status...")
        status_response = requests.get(
            f"{BASE_URL}/payments/checkout/status/{session_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status_result = status_response.json()
            print("✅ Checkout status retrieved successfully")
            print(f"   Demo Mode: {status_result.get('demo_mode', False)}")
            print(f"   Payment Status: {status_result.get('payment_status')}")
        else:
            print(f"❌ Status check failed: {status_response.text}")
            return
        
        # Step 4: Complete demo payment
        print("\n4. Completing demo payment...")
        complete_response = requests.post(
            f"{BASE_URL}/payments/demo/complete/{session_id}",
            headers=headers
        )
        
        if complete_response.status_code == 200:
            complete_result = complete_response.json()
            print("✅ Demo payment completed successfully")
            print(f"   Subscription Plan: {complete_result.get('subscription_plan')}")
            print(f"   Expires At: {complete_result.get('expires_at')}")
        else:
            print(f"❌ Demo payment completion failed: {complete_response.text}")
            return
        
        # Step 5: Verify user subscription
        print("\n5. Verifying user subscription...")
        user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print("✅ User data retrieved successfully")
            print(f"   Subscription Plan: {user_data.get('subscription_plan')}")
            print(f"   Subscription Expires: {user_data.get('subscription_expires')}")
        else:
            print(f"❌ User data retrieval failed: {user_response.text}")
    
    else:
        print(f"❌ Checkout session creation failed: {checkout_response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo checkout test completed!")

if __name__ == "__main__":
    test_demo_checkout()