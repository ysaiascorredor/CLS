#!/usr/bin/env python3
"""
Debug team response structure
"""

import requests
import json
import sys

def main():
    base_url = "https://constr-safety.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 DEBUG: Team Response Structure")
    print("=" * 50)
    
    # Login
    login_data = {
        "email": "ysaias.corredor@gmail.com",
        "password": "Clave.01"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    data = response.json()
    owner_token = data.get("access_token")
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Get team data
    team_response = requests.get(f"{api_url}/organization/team", headers=headers, timeout=10)
    
    if team_response.status_code == 200:
        team_data = team_response.json()
        
        print("Full team response:")
        print(json.dumps(team_data, indent=2, default=str))
        
        print("\nTeam members structure:")
        team_members = team_data.get("team_members", [])
        for i, member in enumerate(team_members):
            print(f"Member {i+1}:")
            print(f"  Raw data: {member}")
            print(f"  Keys: {list(member.keys()) if isinstance(member, dict) else 'Not a dict'}")
            print()
    else:
        print(f"Error: {team_response.status_code}")
        print(team_response.text)

if __name__ == "__main__":
    main()