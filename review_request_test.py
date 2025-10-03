#!/usr/bin/env python3
"""
Review Request Test: Create test user for delete functionality testing
"""

import requests
import json
import sys

def main():
    base_url = "https://constr-safety.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🎯 REVIEW REQUEST: Delete User Functionality Setup")
    print("=" * 60)
    
    # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
    print("Step 1: Logging in with ysaias.corredor@gmail.com...")
    
    login_data = {
        "email": "ysaias.corredor@gmail.com",
        "password": "Clave.01"
    }
    
    try:
        response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        owner_token = data.get("access_token")
        user_data = data.get("user", {})
        
        print(f"✅ Login successful!")
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Organization ID: {user_data.get('organization_id')}")
        print(f"   Organization Role: {user_data.get('organization_role')}")
        
        if not owner_token:
            print("❌ No access token received")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Create test user with specific details
    print("\nStep 2: Creating test user...")
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    user_create_data = {
        "email": "test.delete.now@example.com",
        "name": "Test Delete Now User", 
        "role": "auditor",
        "password": "DeleteNow123"
    }
    
    try:
        create_response = requests.post(f"{api_url}/organization/create-user",
                                      json=user_create_data, headers=headers, timeout=10)
        
        print(f"Create user response status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            test_user_id = create_data.get("user", {}).get("id")
            
            print(f"✅ User created successfully!")
            print(f"   User ID: {test_user_id}")
            print(f"   Email: {user_create_data['email']}")
            print(f"   Name: {user_create_data['name']}")
            print(f"   Role: {user_create_data['role']}")
            
        elif create_response.status_code == 400:
            error_data = create_response.json()
            if "already exists" in error_data.get('detail', ''):
                print(f"⚠️  User already exists, continuing with verification...")
            else:
                print(f"❌ User creation failed: {error_data.get('detail', 'Unknown error')}")
                return False
        else:
            try:
                error_data = create_response.json()
                print(f"❌ User creation failed: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"❌ User creation failed: {create_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False
    
    # Step 3: Verify user appears in team list
    print("\nStep 3: Verifying user appears in team list...")
    
    try:
        team_response = requests.get(f"{api_url}/organization/team",
                                   headers=headers, timeout=10)
        
        print(f"Team response status: {team_response.status_code}")
        
        if team_response.status_code == 200:
            team_data = team_response.json()
            team_members = team_data.get("team_members", [])
            
            print(f"Total team members: {len(team_members)}")
            
            # Look for our test user
            test_user_found = False
            for i, member in enumerate(team_members):
                print(f"   Member {i+1}: {member.get('email', 'N/A')} - {member.get('name', 'N/A')} - {member.get('role', 'N/A')}")
                if member.get("email") == "test.delete.now@example.com":
                    test_user_found = True
            
            if test_user_found:
                print(f"✅ Test user found in team list!")
                print(f"\n🎉 REVIEW REQUEST COMPLETED SUCCESSFULLY:")
                print(f"   - Owner login: ysaias.corredor@gmail.com ✅")
                print(f"   - Test user created: test.delete.now@example.com ✅") 
                print(f"   - User appears in team list ✅")
                print(f"   - Total team members: {len(team_members)}")
                print(f"   - Ready for frontend delete button testing")
                return True
            else:
                print(f"❌ Test user NOT found in team list")
                print(f"Available team members:")
                for member in team_members:
                    print(f"   - {member.get('email', 'N/A')}")
                return False
                
        else:
            try:
                error_data = team_response.json()
                print(f"❌ Team list retrieval failed: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"❌ Team list retrieval failed: {team_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Team verification error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)