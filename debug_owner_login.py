#!/usr/bin/env python3
"""
Debug script to check owner login issue
"""
import requests
import json
import bcrypt

def test_owner_login_debug():
    """Debug the owner login issue"""
    api_url = "https://safetyscan-5.preview.emergentagent.com/api"
    
    print("🔍 Debugging Owner Login Issue")
    print("=" * 50)
    
    # Test the exact credentials
    login_data = {
        "email": "ysaias.corredor@clsolution.net",
        "password": "Clave.01"
    }
    
    print(f"📧 Testing email: {login_data['email']}")
    print(f"🔑 Testing password: {login_data['password']}")
    print()
    
    try:
        response = requests.post(f"{api_url}/auth/login", 
                               json=login_data, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"📄 Response data: {json.dumps(data, indent=2, default=str)}")
        else:
            print("❌ Login failed!")
            try:
                error_data = response.json()
                print(f"📄 Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw response: {response.text}")
        
        print()
        
        # Test password hashing to see what the hash should be
        print("🔐 Password Hash Analysis:")
        test_password = "Clave.01"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(test_password.encode('utf-8'), salt)
        print(f"📝 Test hash for '{test_password}': {hashed.decode('utf-8')}")
        
        # Test verification
        verification = bcrypt.checkpw(test_password.encode('utf-8'), hashed)
        print(f"✅ Hash verification test: {verification}")
        
        print()
        
        # Test with different variations of the password
        print("🧪 Testing password variations:")
        variations = [
            "Clave.01",
            "clave.01", 
            "CLAVE.01",
            "Clave01",
            "Clave.1"
        ]
        
        for variation in variations:
            test_login = {
                "email": "ysaias.corredor@clsolution.net",
                "password": variation
            }
            
            var_response = requests.post(f"{api_url}/auth/login", 
                                       json=test_login, timeout=5)
            
            status = "✅ SUCCESS" if var_response.status_code == 200 else f"❌ FAILED ({var_response.status_code})"
            print(f"  '{variation}': {status}")
        
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_owner_login_debug()