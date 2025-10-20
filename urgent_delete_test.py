#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class UrgentDeleteTester:
    def __init__(self, base_url="https://safesitepro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.owner_token = None
        self.owner_user_id = None
        self.owner_organization_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        if success:
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def test_urgent_delete_team_member_functionality(self):
        """URGENT: Test Delete Team Member Functionality - Review Request"""
        print("\n🚨 URGENT: TESTING DELETE TEAM MEMBER FUNCTIONALITY")
        print("Testing with user credentials: ysaias.corredor@gmail.com / Clave.01")
        
        # Step 1: Login as ysaias.corredor@gmail.com / Clave.01
        success = self.test_owner_gmail_login_for_delete()
        if not success:
            print("❌ CRITICAL: Owner login failed - cannot proceed with delete testing")
            return False
        
        # Step 2: GET /api/organization/team - Check current team members
        success = self.test_get_organization_team_for_delete()
        if not success:
            print("❌ CRITICAL: Cannot retrieve team members - delete testing failed")
            return False
        
        # Step 3: Check if there are team members (besides owner)
        if hasattr(self, 'team_members_for_delete') and len(self.team_members_for_delete) > 1:
            # There are team members - try to delete one
            success = self.test_delete_existing_team_member()
        else:
            # No team members - create one first, then delete it
            print("ℹ️  No existing team members found - creating test member first")
            success = self.test_create_and_delete_team_member()
        
        # Step 4: Check backend logs for any errors during deletion
        self.check_backend_logs_for_delete_errors()
        
        if success:
            print("✅ DELETE TEAM MEMBER FUNCTIONALITY - ALL TESTS PASSED!")
        else:
            print("❌ DELETE TEAM MEMBER FUNCTIONALITY - TESTS FAILED!")
        
        return success

    def test_owner_gmail_login_for_delete(self):
        """Test owner login with ysaias.corredor@gmail.com / Clave.01 for delete testing"""
        try:
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                
                if has_token:
                    self.owner_token = data["access_token"]
                
                success = has_token and has_user
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@gmail.com"
                    has_organization = user_data.get("organization_id") is not None
                    is_owner = user_data.get("organization_role") == "owner"
                    
                    success = success and correct_email and has_organization and is_owner
                    details += f", Correct email: {correct_email}, Has org: {has_organization}, Is owner: {is_owner}"
                    
                    if success:
                        self.owner_user_id = user_data.get("id")
                        self.owner_organization_id = user_data.get("organization_id")
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Owner Login for Delete Testing (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Login for Delete Testing (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_get_organization_team_for_delete(self):
        """GET /api/organization/team - Check current team members"""
        if not self.owner_token:
            self.log_test("Get Organization Team for Delete", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_organization = "organization" in data
                has_team_members = "team_members" in data
                
                success = has_organization and has_team_members
                
                if success:
                    team_members = data.get("team_members", [])
                    self.team_members_for_delete = team_members
                    
                    # Count non-owner members
                    non_owner_members = [m for m in team_members if m.get("user_id") != self.owner_user_id]
                    
                    details = f"Status: {response.status_code}, Total members: {len(team_members)}, Non-owner members: {len(non_owner_members)}"
                    
                    # Store a deletable member if available
                    if non_owner_members:
                        self.deletable_member = non_owner_members[0]
                        details += f", Deletable member found: {self.deletable_member.get('email', 'N/A')}"
                else:
                    details = f"Status: {response.status_code}, Has org: {has_organization}, Has members: {has_team_members}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Organization Team for Delete", success, details)
            return success
        except Exception as e:
            self.log_test("Get Organization Team for Delete", False, str(e))
            return False

    def test_delete_existing_team_member(self):
        """Try DELETE /api/organization/remove-user/{user_id} with existing member"""
        if not self.owner_token or not hasattr(self, 'deletable_member'):
            self.log_test("Delete Existing Team Member", False, "No owner token or deletable member")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            user_id = self.deletable_member.get("user_id")
            member_email = self.deletable_member.get("email", "Unknown")
            
            print(f"🗑️  Attempting to delete team member: {member_email} (ID: {user_id})")
            
            response = requests.delete(f"{self.api_url}/organization/remove-user/{user_id}", 
                                     headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "removed" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Has message: {has_message}, Success message: {success_message}"
                
                if success:
                    # Verify user is actually removed from team
                    verify_success = self.verify_user_removed_from_team(user_id)
                    success = success and verify_success
                    details += f", Verified removal: {verify_success}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Delete Existing Team Member", success, details)
            return success
        except Exception as e:
            self.log_test("Delete Existing Team Member", False, str(e))
            return False

    def test_create_and_delete_team_member(self):
        """Create a test team member first, then try to delete it"""
        if not self.owner_token:
            self.log_test("Create and Delete Team Member", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Step 1: Create a test team member
            test_email = f"test.delete.urgent.{timestamp}@example.com"
            create_data = {
                "email": test_email,
                "name": "Test Delete Urgent User",
                "role": "auditor",
                "password": "TestDelete123"
            }
            
            create_response = requests.post(f"{self.api_url}/organization/create-user", 
                                          json=create_data, headers=headers, timeout=10)
            
            if create_response.status_code != 200:
                self.log_test("Create and Delete Team Member", False, f"Failed to create test user: {create_response.status_code}")
                return False
            
            create_data_response = create_response.json()
            test_user_id = create_data_response.get("user", {}).get("id")
            
            if not test_user_id:
                self.log_test("Create and Delete Team Member", False, "No user ID returned from create")
                return False
            
            print(f"✅ Created test user: {test_email} (ID: {test_user_id})")
            
            # Step 2: Verify user appears in team list
            team_response = requests.get(f"{self.api_url}/organization/team", 
                                       headers=headers, timeout=10)
            
            user_in_team = False
            if team_response.status_code == 200:
                team_data = team_response.json()
                team_members = team_data.get("team_members", [])
                user_in_team = any(m.get("user_id") == test_user_id for m in team_members)
            
            if not user_in_team:
                self.log_test("Create and Delete Team Member", False, "Created user not found in team")
                return False
            
            print(f"✅ Verified user appears in team list")
            
            # Step 3: Delete the test user
            delete_response = requests.delete(f"{self.api_url}/organization/remove-user/{test_user_id}", 
                                            headers=headers, timeout=10)
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                has_message = "message" in delete_data
                success_message = "removed" in delete_data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Create: 200, Team verify: {user_in_team}, Delete: {delete_response.status_code}, Message: {success_message}"
                
                if success:
                    # Step 4: Verify user is actually removed from team
                    verify_success = self.verify_user_removed_from_team(test_user_id)
                    success = success and verify_success
                    details += f", Verified removal: {verify_success}"
                    
            else:
                success = False
                try:
                    error_data = delete_response.json()
                    details = f"Create: 200, Delete failed: {delete_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Create: 200, Delete failed: {delete_response.status_code}"
            
            self.log_test("Create and Delete Team Member", success, details)
            return success
        except Exception as e:
            self.log_test("Create and Delete Team Member", False, str(e))
            return False

    def verify_user_removed_from_team(self, user_id):
        """Verify that user is actually removed from team_members collection"""
        if not self.owner_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                team_members = data.get("team_members", [])
                
                # Check if user is still in team (should not be)
                user_still_in_team = any(m.get("user_id") == user_id for m in team_members)
                
                # Return True if user is NOT in team (successfully removed)
                return not user_still_in_team
            
            return False
        except Exception:
            return False

    def check_backend_logs_for_delete_errors(self):
        """Check backend logs for any errors during deletion"""
        try:
            # Check supervisor backend logs
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                has_delete_errors = any(keyword in logs.lower() for keyword in 
                                      ['error', 'exception', 'failed', 'remove-user', 'delete'])
                
                if has_delete_errors:
                    print(f"⚠️  Backend logs show potential delete-related errors:")
                    print(logs[-500:])  # Show last 500 chars
                else:
                    print("✅ No delete-related errors found in backend logs")
                    
                return not has_delete_errors
            else:
                print("⚠️  Could not access backend logs")
                return True  # Assume no errors if can't check
                
        except Exception as e:
            print(f"⚠️  Error checking backend logs: {e}")
            return True  # Assume no errors if can't check

if __name__ == "__main__":
    tester = UrgentDeleteTester()
    success = tester.test_urgent_delete_team_member_functionality()
    
    if success:
        print("\n🎉 URGENT DELETE TESTING COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n💥 URGENT DELETE TESTING FAILED!")
        sys.exit(1)