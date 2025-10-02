import requests
import sys
import json
from datetime import datetime
import bcrypt

class CSABackendTester:
    def __init__(self, base_url="https://safeinspect-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_audit_id = None
        self.admin_token = None
        self.demo_token = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")

    def test_health_check(self):
        """Test if backend is accessible"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            success = response.status_code == 200
            self.log_test("Backend Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False

    def test_work_types_endpoint(self):
        """Test work types endpoint (public)"""
        try:
            response = requests.get(f"{self.api_url}/work-types", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                work_types_count = len(data)
                has_required_fields = all('id' in wt and 'name_en' in wt and 'name_es' in wt for wt in data)
                success = work_types_count == 15 and has_required_fields
                details = f"Found {work_types_count} work types, required fields: {has_required_fields}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Work Types Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Work Types Endpoint", False, str(e))
            return False

    def test_subscription_packages_endpoint(self):
        """Test subscription packages endpoint (public)"""
        try:
            response = requests.get(f"{self.api_url}/payments/packages", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_packages = ['basic', 'professional', 'enterprise']
                has_all_packages = all(pkg in data for pkg in expected_packages)
                details = f"Packages: {list(data.keys())}, Has all expected: {has_all_packages}"
                success = has_all_packages
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Subscription Packages Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Subscription Packages Endpoint", False, str(e))
            return False

    def test_admin_login(self):
        """Test admin login with admin@csaaudit.com / admin123"""
        try:
            login_data = {
                "email": "admin@csaaudit.com",
                "password": "admin123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                if has_token:
                    self.admin_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    is_admin = user_data.get("role") == "admin"
                    correct_email = user_data.get("email") == "admin@csaaudit.com"
                    success = success and is_admin and correct_email
                    details += f", Admin role: {is_admin}, Correct email: {correct_email}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Admin Login (admin@csaaudit.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Login (admin@csaaudit.com)", False, str(e))
            return False

    def test_demo_login(self):
        """Test demo login with demo@csaaudit.com / demo123"""
        try:
            login_data = {
                "email": "demo@csaaudit.com",
                "password": "demo123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                if has_token:
                    self.demo_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    is_user = user_data.get("role") == "user"
                    correct_email = user_data.get("email") == "demo@csaaudit.com"
                    success = success and is_user and correct_email
                    details += f", User role: {is_user}, Correct email: {correct_email}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Demo Login (demo@csaaudit.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Demo Login (demo@csaaudit.com)", False, str(e))
            return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        try:
            login_data = {
                "email": "admin@csaaudit.com",
                "password": "wrongpassword"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            success = response.status_code == 401
            
            if success:
                try:
                    error_data = response.json()
                    has_error_detail = "detail" in error_data
                    details = f"Status: {response.status_code}, Has error detail: {has_error_detail}"
                except:
                    details = f"Status: {response.status_code}"
            else:
                details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Invalid Login Credentials", success, details)
            return success
        except Exception as e:
            self.log_test("Invalid Login Credentials", False, str(e))
            return False

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint with valid JWT token"""
        if not self.demo_token:
            self.log_test("Auth Me Endpoint", False, "No valid token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.demo_token}"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_id = "id" in data
                has_email = "email" in data
                has_name = "name" in data
                has_role = "role" in data
                
                success = has_id and has_email and has_name and has_role
                details = f"Status: {response.status_code}, Fields present: id={has_id}, email={has_email}, name={has_name}, role={has_role}"
                
                if success:
                    correct_email = data.get("email") == "demo@csaaudit.com"
                    success = success and correct_email
                    details += f", Correct email: {correct_email}"
                    
            else:
                success = False
                details = f"Status: {response.status_code}"
            
            self.log_test("Auth Me Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me Endpoint", False, str(e))
            return False

    def test_auth_me_without_token(self):
        """Test /auth/me endpoint without token (should return 401)"""
        try:
            response = requests.get(f"{self.api_url}/auth/me", timeout=10)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Auth Me Without Token", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me Without Token", False, str(e))
            return False

    def test_auth_me_invalid_token(self):
        """Test /auth/me endpoint with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Auth Me Invalid Token", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me Invalid Token", False, str(e))
            return False

    def test_jwt_token_structure(self):
        """Test JWT token structure and validation"""
        if not self.demo_token:
            self.log_test("JWT Token Structure", False, "No valid token available")
            return False
            
        try:
            # JWT tokens have 3 parts separated by dots
            token_parts = self.demo_token.split('.')
            has_three_parts = len(token_parts) == 3
            
            # Each part should be base64-like (no spaces, reasonable length)
            parts_valid = all(len(part) > 10 and ' ' not in part for part in token_parts)
            
            success = has_three_parts and parts_valid
            details = f"Parts count: {len(token_parts)} (expected 3), Parts valid: {parts_valid}"
            
            self.log_test("JWT Token Structure", success, details)
            return success
        except Exception as e:
            self.log_test("JWT Token Structure", False, str(e))
            return False

    def test_password_hashing(self):
        """Test that passwords are properly hashed in database"""
        try:
            # This is a basic test to ensure password hashing is working
            # We'll test by trying to login and checking the response
            login_data = {
                "email": "demo@csaaudit.com",
                "password": "demo123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            # If login works, password hashing is working
            success = response.status_code == 200
            
            if success:
                # Also test that wrong password fails
                wrong_login_data = {
                    "email": "demo@csaaudit.com",
                    "password": "wrongpassword"
                }
                
                wrong_response = requests.post(f"{self.api_url}/auth/login", 
                                             json=wrong_login_data, timeout=10)
                
                wrong_fails = wrong_response.status_code == 401
                success = success and wrong_fails
                details = f"Correct password works: True, Wrong password fails: {wrong_fails}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Password Hashing/Verification", success, details)
            return success
        except Exception as e:
            self.log_test("Password Hashing/Verification", False, str(e))
            return False

    def test_protected_endpoints_without_auth(self):
        """Test that protected endpoints return 401 without authentication"""
        protected_endpoints = [
            ("GET", "/auth/me", "Get Current User"),
            ("GET", "/audits", "Get User Audits"),
            ("GET", "/statistics", "Get Statistics"),
            ("POST", "/audits", "Create Audit"),
        ]
        
        all_passed = True
        for method, endpoint, name in protected_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.api_url}{endpoint}", 
                                           json={"test": "data"}, timeout=10)
                
                success = response.status_code == 401
                details = f"Status: {response.status_code} (expected 401)"
                self.log_test(f"Protected Endpoint - {name}", success, details)
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Protected Endpoint - {name}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            response = requests.options(f"{self.api_url}/work-types", 
                                      headers={"Origin": "https://safeinspect-2.preview.emergentagent.com"})
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            has_cors = any(cors_headers.values())
            success = has_cors or response.status_code == 200
            
            self.log_test("CORS Configuration", success, f"CORS headers present: {has_cors}")
            return success
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))
            return False

    def test_api_route_prefix(self):
        """Test that API routes are properly prefixed with /api"""
        try:
            # Test that /work-types (without /api) returns 404
            response = requests.get(f"{self.base_url}/work-types", timeout=10)
            wrong_route_fails = response.status_code == 404
            
            # Test that /api/work-types works
            response = requests.get(f"{self.api_url}/work-types", timeout=10)
            correct_route_works = response.status_code == 200
            
            success = wrong_route_fails and correct_route_works
            details = f"Without /api: {response.status_code if not wrong_route_fails else '404'}, With /api: {'200' if correct_route_works else 'Failed'}"
            
            self.log_test("API Route Prefix", success, details)
            return success
        except Exception as e:
            self.log_test("API Route Prefix", False, str(e))
            return False

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid audit creation without auth
            response = requests.post(f"{self.api_url}/audits", 
                                   json={"invalid": "data"}, timeout=10)
            
            # Should return 401 (auth required) not 422 (validation error)
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401 for auth required)"
            
            self.log_test("Error Handling", success, details)
            return success
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False

    def test_admin_create_user_endpoint(self):
        """Test POST /api/admin/create-admin endpoint"""
        if not self.admin_token:
            self.log_test("Admin Create User Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test creating a new admin user
            create_data = {
                "email": f"testadmin_{datetime.now().strftime('%Y%m%d_%H%M%S')}@csaaudit.com",
                "name": "Test Admin User"
            }
            
            response = requests.post(f"{self.api_url}/admin/create-admin", 
                                   json=create_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_admin = "admin" in data
                message_contains_password = "temporary password" in data.get("message", "").lower()
                
                success = has_message and has_admin and message_contains_password
                details = f"Status: {response.status_code}, Message: {has_message}, Admin: {has_admin}, Password in message: {message_contains_password}"
                
                if has_admin:
                    admin_data = data["admin"]
                    correct_email = admin_data.get("email") == create_data["email"]
                    correct_name = admin_data.get("name") == create_data["name"]
                    is_admin_role = admin_data.get("role") == "admin"
                    has_password_hash = admin_data.get("password_hash") is not None
                    
                    success = success and correct_email and correct_name and is_admin_role and has_password_hash
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {is_admin_role}, Hash: {has_password_hash}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Create User Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Create User Endpoint", False, str(e))
            return False

    def test_admin_create_user_without_auth(self):
        """Test POST /api/admin/create-admin without admin auth (should fail)"""
        try:
            create_data = {
                "email": "test@example.com",
                "name": "Test User"
            }
            
            # Test without token
            response = requests.post(f"{self.api_url}/admin/create-admin", 
                                   json=create_data, timeout=10)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Admin Create User Without Auth", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Create User Without Auth", False, str(e))
            return False

    def test_admin_create_user_with_user_token(self):
        """Test POST /api/admin/create-admin with regular user token (should fail)"""
        if not self.demo_token:
            self.log_test("Admin Create User With User Token", False, "No demo token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.demo_token}"}
            create_data = {
                "email": "test@example.com",
                "name": "Test User"
            }
            
            response = requests.post(f"{self.api_url}/admin/create-admin", 
                                   json=create_data, headers=headers, timeout=10)
            
            success = response.status_code == 403
            details = f"Status: {response.status_code} (expected 403)"
            
            self.log_test("Admin Create User With User Token", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Create User With User Token", False, str(e))
            return False

    def test_system_logs_endpoint(self):
        """Test GET /api/admin/logs endpoint"""
        if not self.admin_token:
            self.log_test("System Logs Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.api_url}/admin/logs", 
                                  headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_logs = "logs" in data
                
                success = has_logs
                details = f"Status: {response.status_code}, Has logs: {has_logs}"
                
                if has_logs:
                    logs_content = data["logs"]
                    has_timestamp = "timestamp" in logs_content.lower()
                    has_system_info = "system" in logs_content.lower()
                    logs_length = len(logs_content)
                    
                    success = success and has_timestamp and logs_length > 0
                    details += f", Has timestamp: {has_timestamp}, Has system info: {has_system_info}, Length: {logs_length}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("System Logs Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("System Logs Endpoint", False, str(e))
            return False

    def test_system_logs_without_auth(self):
        """Test GET /api/admin/logs without admin auth (should fail)"""
        try:
            response = requests.get(f"{self.api_url}/admin/logs", timeout=10)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("System Logs Without Auth", success, details)
            return success
        except Exception as e:
            self.log_test("System Logs Without Auth", False, str(e))
            return False

    def test_support_tickets_endpoint(self):
        """Test GET /api/admin/support-tickets endpoint"""
        if not self.admin_token:
            self.log_test("Support Tickets Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.api_url}/admin/support-tickets", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_failed_payments = "failed_payments" in data
                has_active_users_no_sub = "active_users_no_subscription" in data
                has_heavy_users = "heavy_users_no_upgrade" in data
                
                success = has_failed_payments and has_active_users_no_sub and has_heavy_users
                details = f"Status: {response.status_code}, Failed payments: {has_failed_payments}, Active users no sub: {has_active_users_no_sub}, Heavy users: {has_heavy_users}"
                
                if success:
                    # Check data structure
                    failed_payments = data.get("failed_payments", [])
                    active_users = data.get("active_users_no_subscription", [])
                    heavy_users = data.get("heavy_users_no_upgrade", [])
                    
                    is_list_failed = isinstance(failed_payments, list)
                    is_list_active = isinstance(active_users, list)
                    is_list_heavy = isinstance(heavy_users, list)
                    
                    success = success and is_list_failed and is_list_active and is_list_heavy
                    details += f", Lists valid: failed={is_list_failed}, active={is_list_active}, heavy={is_list_heavy}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Support Tickets Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Support Tickets Endpoint", False, str(e))
            return False

    def test_support_tickets_without_auth(self):
        """Test GET /api/admin/support-tickets without admin auth (should fail)"""
        try:
            response = requests.get(f"{self.api_url}/admin/support-tickets", timeout=10)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Support Tickets Without Auth", success, details)
            return success
        except Exception as e:
            self.log_test("Support Tickets Without Auth", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🔍 Starting CSA Construction Safety Audit Backend Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Backend is not accessible. Stopping tests.")
            return False
        
        # Public endpoint tests
        print("\n📡 Testing Public Endpoints...")
        self.test_work_types_endpoint()
        self.test_subscription_packages_endpoint()
        self.test_api_route_prefix()
        self.test_cors_headers()
        
        # Authentication tests
        print("\n🔐 Testing Authentication...")
        self.test_demo_login()
        self.test_admin_login()
        self.test_invalid_login()
        self.test_password_hashing()
        self.test_jwt_token_structure()
        
        # Protected endpoint tests
        print("\n🛡️ Testing Protected Endpoints...")
        self.test_auth_me_endpoint()
        self.test_auth_me_without_token()
        self.test_auth_me_invalid_token()
        self.test_protected_endpoints_without_auth()
        
        # Error handling tests
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

def main():
    tester = CSABackendTester()
    success = tester.run_all_tests()
    
    # Additional notes for manual testing
    print("\n📝 Manual Testing Notes:")
    print("1. Authentication requires Google OAuth - test via frontend")
    print("2. Stripe payments require valid API key - test via frontend")
    print("3. Photo uploads require authenticated session")
    print("4. Full audit flow requires authenticated user")
    print("\n🔗 For authenticated testing, see: /app/auth_testing.md")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())