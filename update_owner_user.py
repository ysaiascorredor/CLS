#!/usr/bin/env python3
"""
Script to update the owner user to admin role and enterprise plan
"""
import requests
import json
from datetime import datetime, timezone, timedelta

def update_owner_user():
    """Update the owner user to admin role and enterprise plan"""
    api_url = "https://constr-safety.preview.emergentagent.com/api"
    
    print("🔧 Updating Owner User Role and Plan")
    print("=" * 45)
    
    # First, login as admin to get admin token
    admin_login = {
        "email": "admin@csaaudit.com",
        "password": "admin123"
    }
    
    print("🔐 Getting admin token...")
    try:
        admin_response = requests.post(f"{api_url}/auth/login", 
                                     json=admin_login, timeout=10)
        
        if admin_response.status_code != 200:
            print("❌ Failed to get admin token!")
            return
            
        admin_data = admin_response.json()
        admin_token = admin_data["access_token"]
        print("✅ Admin token obtained")
        
        # Get owner user ID
        owner_login = {
            "email": "ysaias.corredor@clsolution.net",
            "password": "Clave.01"
        }
        
        owner_response = requests.post(f"{api_url}/auth/login", 
                                     json=owner_login, timeout=10)
        
        if owner_response.status_code != 200:
            print("❌ Failed to get owner user info!")
            return
            
        owner_data = owner_response.json()
        owner_user_id = owner_data["user"]["id"]
        print(f"👤 Owner user ID: {owner_user_id}")
        
        # Update user role and plan
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Calculate subscription expiry (1 year from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        update_data = {
            "role": "admin",
            "subscription_plan": "enterprise",
            "subscription_expires": expires_at.isoformat(),
            "audits_used_this_month": 0
        }
        
        print(f"🔄 Updating user with data: {json.dumps(update_data, indent=2, default=str)}")
        
        update_response = requests.put(f"{api_url}/admin/user/{owner_user_id}", 
                                     json=update_data, headers=headers, timeout=10)
        
        print(f"📊 Update Response Status: {update_response.status_code}")
        
        if update_response.status_code == 200:
            update_result = update_response.json()
            print("✅ User update successful!")
            print(f"📄 Update result: {json.dumps(update_result, indent=2)}")
            
            # Verify the update by logging in again
            print("\n🔍 Verifying update by logging in again...")
            verify_response = requests.post(f"{api_url}/auth/login", 
                                          json=owner_login, timeout=10)
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                user_info = verify_data["user"]
                
                print("✅ Verification successful!")
                print(f"📧 Email: {user_info['email']}")
                print(f"👤 Name: {user_info['name']}")
                print(f"🎭 Role: {user_info['role']}")
                print(f"💳 Plan: {user_info['subscription_plan']}")
                print(f"📅 Expires: {user_info['subscription_expires']}")
                print(f"🏢 Org ID: {user_info['organization_id']}")
                
                if user_info['role'] == 'admin' and user_info['subscription_plan'] == 'enterprise':
                    print("\n🎉 SUCCESS: Owner user is now admin with enterprise plan!")
                else:
                    print(f"\n⚠️  WARNING: Update may not have worked correctly")
                    print(f"   Expected: role=admin, plan=enterprise")
                    print(f"   Actual: role={user_info['role']}, plan={user_info['subscription_plan']}")
            else:
                print("❌ Verification login failed!")
                
        else:
            print("❌ User update failed!")
            try:
                error_data = update_response.json()
                print(f"📄 Update error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw update response: {update_response.text}")
        
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")

if __name__ == "__main__":
    update_owner_user()