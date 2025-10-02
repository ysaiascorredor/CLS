#!/usr/bin/env python3
"""
Script to create the owner user in the database
"""
import requests
import json

def create_owner_user():
    """Create the owner user account"""
    api_url = "https://safeinspect-2.preview.emergentagent.com/api"
    
    print("🔧 Creating Owner User Account")
    print("=" * 40)
    
    # Try to register the owner user
    register_data = {
        "email": "ysaias.corredor@clsolution.net",
        "name": "Ysaias Corredor",
        "password": "Clave.01"
    }
    
    print(f"📧 Creating user: {register_data['email']}")
    print(f"👤 Name: {register_data['name']}")
    print(f"🔑 Password: {register_data['password']}")
    print()
    
    try:
        # Try registration
        response = requests.post(f"{api_url}/auth/register", 
                               json=register_data, timeout=10)
        
        print(f"📊 Registration Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User registration successful!")
            print(f"📄 Response data: {json.dumps(data, indent=2, default=str)}")
            
            # Now try to login
            print("\n🔐 Testing login after registration...")
            login_data = {
                "email": "ysaias.corredor@clsolution.net",
                "password": "Clave.01"
            }
            
            login_response = requests.post(f"{api_url}/auth/login", 
                                         json=login_data, timeout=10)
            
            print(f"📊 Login Response Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                print("✅ Login successful after registration!")
                print(f"📄 Login response: {json.dumps(login_data, indent=2, default=str)}")
                
                # Update user to admin role and enterprise plan
                if "access_token" in login_data:
                    token = login_data["access_token"]
                    user_id = login_data["user"]["id"]
                    
                    print(f"\n🔧 Updating user to admin role and enterprise plan...")
                    print(f"👤 User ID: {user_id}")
                    
                    # This would need to be done through admin endpoint or database directly
                    print("⚠️  Note: User role and plan updates need to be done through admin interface")
                    
            else:
                print("❌ Login failed after registration!")
                try:
                    error_data = login_response.json()
                    print(f"📄 Login error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"📄 Raw login response: {login_response.text}")
                    
        else:
            print("❌ User registration failed!")
            try:
                error_data = response.json()
                print(f"📄 Registration error: {json.dumps(error_data, indent=2)}")
                
                # Check if user already exists
                if "already registered" in error_data.get("detail", "").lower():
                    print("\n🔍 User already exists, testing login...")
                    login_data = {
                        "email": "ysaias.corredor@clsolution.net",
                        "password": "Clave.01"
                    }
                    
                    login_response = requests.post(f"{api_url}/auth/login", 
                                                 json=login_data, timeout=10)
                    
                    print(f"📊 Existing User Login Status: {login_response.status_code}")
                    
                    if login_response.status_code == 200:
                        print("✅ Existing user login successful!")
                        login_result = login_response.json()
                        print(f"📄 Login data: {json.dumps(login_result, indent=2, default=str)}")
                    else:
                        print("❌ Existing user login failed - password may be different!")
                        
            except:
                print(f"📄 Raw registration response: {response.text}")
        
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")

if __name__ == "__main__":
    create_owner_user()