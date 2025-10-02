#!/usr/bin/env python3
"""
Focused test for organization endpoints - User reported issue
"""
import requests
import json

def test_organization_endpoints():
    base_url = "https://constr-safety.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🏢 FOCUSED ORGANIZATION ENDPOINT TESTING")
    print("=" * 50)
    
    # Step 1: Login with test user
    print("1. Logging in with test@csaaudit.com...")
    login_data = {
        "email": "test@csaaudit.com",
        "password": "test123"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False
        
    data = response.json()
    token = data["access_token"]
    user = data["user"]
    
    print(f"✅ Login successful")
    print(f"   User ID: {user.get('id')}")
    print(f"   Organization ID: {user.get('organization_id')}")
    print(f"   Organization Role: {user.get('organization_role')}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Test GET /api/organization/team
    print("\n2. Testing GET /api/organization/team...")
    response = requests.get(f"{api_url}/organization/team", headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Team endpoint successful")
        print(f"   Organization: {data.get('organization', {}).get('name', 'N/A')}")
        print(f"   Team members: {len(data.get('team_members', []))}")
        print(f"   Pending invitations: {len(data.get('pending_invitations', []))}")
        
        # Show team member details
        for i, member in enumerate(data.get('team_members', [])):
            user_info = member.get('user', {})
            print(f"   Member {i+1}: {user_info.get('name', 'N/A')} ({user_info.get('email', 'N/A')}) - Role: {member.get('role', 'N/A')}")
            
    else:
        print(f"❌ Team endpoint failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
        except:
            print(f"   Response: {response.text[:200]}")
        return False
    
    # Step 3: Test POST /api/organization/create (should fail since user already has org)
    print("\n3. Testing POST /api/organization/create (should fail)...")
    org_data = {"name": "Test Organization 2"}
    response = requests.post(f"{api_url}/organization/create", json=org_data, headers=headers, timeout=10)
    
    if response.status_code == 400:
        error = response.json()
        print("✅ Create organization correctly failed (user already has org)")
        print(f"   Error: {error.get('detail', 'Unknown error')}")
    else:
        print(f"❌ Create organization should have failed but got: {response.status_code}")
        return False
    
    # Step 4: Test user info again to confirm organization data
    print("\n4. Confirming user organization data...")
    response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
    
    if response.status_code == 200:
        user = response.json()
        print("✅ User data confirmed")
        print(f"   Organization ID: {user.get('organization_id')}")
        print(f"   Organization Role: {user.get('organization_role')}")
        print(f"   Subscription Plan: {user.get('subscription_plan')}")
    else:
        print(f"❌ Failed to get user data: {response.status_code}")
        return False
    
    print("\n🎉 ALL ORGANIZATION TESTS PASSED!")
    print("\n🔍 DIAGNOSIS:")
    print("   ✅ Backend organization endpoints are working correctly")
    print("   ✅ User has organization and can access team data")
    print("   ✅ Proper error handling for duplicate organization creation")
    print("   🔍 Issue is likely in FRONTEND not displaying organization data")
    print("   🔍 Frontend should check user.organization_id and show organization UI")
    
    return True

if __name__ == "__main__":
    test_organization_endpoints()