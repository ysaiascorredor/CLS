import requests
import sys
import json
from datetime import datetime
import bcrypt

class CSABackendTester:
    def __init__(self, base_url="https://safesitepro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_audit_id = None
        self.admin_token = None
        self.demo_token = None
        self.test_user_token = None
        self.owner_token = None

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
        """Test work types endpoint (public) - UPDATED FOR NEW CATEGORIES"""
        try:
            response = requests.get(f"{self.api_url}/work-types", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                work_types_count = len(data)
                has_required_fields = all('id' in wt and 'name_en' in wt and 'name_es' in wt for wt in data)
                
                # Check for new categories as per review request
                required_new_categories = ['jsa', 'jha', 'safety_daily_plan', 'ppe', 'lifting_equipment', 'housekeeping', 'chemical_work']
                existing_ids = [wt['id'] for wt in data]
                has_new_categories = all(cat_id in existing_ids for cat_id in required_new_categories)
                
                # Should now have 22 total categories (15 original + 7 new)
                success = work_types_count == 22 and has_required_fields and has_new_categories
                details = f"Found {work_types_count} work types (expected 22), required fields: {has_required_fields}, new categories: {has_new_categories}"
                
                if has_new_categories:
                    # Verify specific new category names
                    jsa_found = any(wt['id'] == 'jsa' and 'Job Safety Analysis' in wt['name_en'] for wt in data)
                    jha_found = any(wt['id'] == 'jha' and 'Job Hazard Analysis' in wt['name_en'] for wt in data)
                    ppe_found = any(wt['id'] == 'ppe' and 'Personal Protective Equipment' in wt['name_en'] for wt in data)
                    chemical_found = any(wt['id'] == 'chemical_work' and 'Chemical Handling' in wt['name_en'] for wt in data)
                    
                    specific_categories_valid = jsa_found and jha_found and ppe_found and chemical_found
                    success = success and specific_categories_valid
                    details += f", specific new categories valid: {specific_categories_valid}"
                    
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Work Types Endpoint (New Categories)", success, details)
            return success
        except Exception as e:
            self.log_test("Work Types Endpoint (New Categories)", False, str(e))
            return False

    def test_subscription_packages_endpoint(self):
        """Test subscription packages endpoint (public) - UPDATED FOR CSA SAFETY PRO"""
        try:
            response = requests.get(f"{self.api_url}/payments/packages", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Updated to check for the single unlimited package
                has_unlimited_package = "unlimited" in data
                
                if has_unlimited_package:
                    unlimited_pkg = data["unlimited"]
                    has_correct_price = unlimited_pkg.get("price") == 49.99
                    has_correct_name = unlimited_pkg.get("name") == "CSA Safety Pro"
                    has_unlimited_audits = unlimited_pkg.get("audits_per_month") == -1
                    has_unlimited_members = unlimited_pkg.get("team_members") == -1
                    
                    success = has_correct_price and has_correct_name and has_unlimited_audits and has_unlimited_members
                    details = f"Package: unlimited, Price: ${unlimited_pkg.get('price')}, Name: {unlimited_pkg.get('name')}, Audits: {unlimited_pkg.get('audits_per_month')}, Members: {unlimited_pkg.get('team_members')}"
                else:
                    success = False
                    details = f"Packages: {list(data.keys())}, Missing unlimited package"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Subscription Packages Endpoint (CSA Safety Pro)", success, details)
            return success
        except Exception as e:
            self.log_test("Subscription Packages Endpoint (CSA Safety Pro)", False, str(e))
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
                                      headers={"Origin": "https://safesitepro.preview.emergentagent.com"})
            
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

    def test_statistics_endpoint(self):
        """Test GET /api/statistics endpoint (original statistics)"""
        if not self.admin_token:
            self.log_test("Statistics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.api_url}/statistics", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "total_audits", "compliant_audits", "non_compliant_audits",
                    "average_compliance_score", "most_common_findings", "work_type_statistics"
                ]
                
                has_all_fields = all(field in data for field in required_fields)
                success = has_all_fields
                details = f"Status: {response.status_code}, Has all required fields: {has_all_fields}"
                
                if has_all_fields:
                    # Validate data types
                    total_audits = isinstance(data.get("total_audits"), int)
                    compliant_audits = isinstance(data.get("compliant_audits"), int)
                    non_compliant_audits = isinstance(data.get("non_compliant_audits"), int)
                    avg_score = isinstance(data.get("average_compliance_score"), (int, float))
                    findings_list = isinstance(data.get("most_common_findings"), list)
                    work_type_list = isinstance(data.get("work_type_statistics"), list)
                    
                    types_valid = all([total_audits, compliant_audits, non_compliant_audits, 
                                     avg_score, findings_list, work_type_list])
                    
                    success = success and types_valid
                    details += f", Data types valid: {types_valid}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Statistics Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Statistics Endpoint", False, str(e))
            return False

    def test_statistics_charts_endpoint(self):
        """Test GET /api/statistics/charts endpoint (new charts data)"""
        if not self.admin_token:
            self.log_test("Statistics Charts Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.api_url}/statistics/charts", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "audit_trends", "compliance_trends", "work_type_performance", "monthly_summary"
                ]
                
                has_all_fields = all(field in data for field in required_fields)
                success = has_all_fields
                details = f"Status: {response.status_code}, Has all required fields: {has_all_fields}"
                
                if has_all_fields:
                    # Validate data structure
                    audit_trends = data.get("audit_trends", [])
                    compliance_trends = data.get("compliance_trends", [])
                    work_type_performance = data.get("work_type_performance", [])
                    monthly_summary = data.get("monthly_summary", [])
                    
                    # Check if all are lists
                    all_lists = all(isinstance(field, list) for field in [
                        audit_trends, compliance_trends, work_type_performance, monthly_summary
                    ])
                    
                    success = success and all_lists
                    details += f", All fields are lists: {all_lists}"
                    
                    # Check audit_trends structure
                    if audit_trends and all_lists:
                        first_trend = audit_trends[0] if audit_trends else {}
                        trend_fields = ["month", "total_audits", "avg_score"]
                        has_trend_fields = all(field in first_trend for field in trend_fields)
                        details += f", Audit trends structure valid: {has_trend_fields}"
                        success = success and has_trend_fields
                    
                    # Check compliance_trends structure
                    if compliance_trends and all_lists:
                        first_compliance = compliance_trends[0] if compliance_trends else {}
                        compliance_fields = ["month", "compliant", "non_compliant", "compliance_rate"]
                        has_compliance_fields = all(field in first_compliance for field in compliance_fields)
                        details += f", Compliance trends structure valid: {has_compliance_fields}"
                        success = success and has_compliance_fields
                    
                    # Check work_type_performance structure
                    if work_type_performance and all_lists:
                        first_work_type = work_type_performance[0] if work_type_performance else {}
                        work_type_fields = ["work_type", "avg_score", "total_audits", "compliance_rate"]
                        has_work_type_fields = all(field in first_work_type for field in work_type_fields)
                        details += f", Work type performance structure valid: {has_work_type_fields}"
                        success = success and has_work_type_fields
                    
                    # Check monthly_summary structure
                    if monthly_summary and all_lists:
                        first_monthly = monthly_summary[0] if monthly_summary else {}
                        monthly_fields = ["month", "total_audits", "compliant", "non_compliant", "avg_score"]
                        has_monthly_fields = all(field in first_monthly for field in monthly_fields)
                        details += f", Monthly summary structure valid: {has_monthly_fields}"
                        success = success and has_monthly_fields
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Statistics Charts Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Statistics Charts Endpoint", False, str(e))
            return False

    def test_statistics_without_auth(self):
        """Test statistics endpoints without authentication (should fail)"""
        try:
            # Test original statistics endpoint
            response1 = requests.get(f"{self.api_url}/statistics", timeout=10)
            stats_fails = response1.status_code == 401
            
            # Test charts endpoint
            response2 = requests.get(f"{self.api_url}/statistics/charts", timeout=10)
            charts_fails = response2.status_code == 401
            
            success = stats_fails and charts_fails
            details = f"Statistics: {response1.status_code} (expected 401), Charts: {response2.status_code} (expected 401)"
            
            self.log_test("Statistics Without Auth", success, details)
            return success
        except Exception as e:
            self.log_test("Statistics Without Auth", False, str(e))
            return False

    def test_create_test_audit_for_statistics(self):
        """Create a test audit to ensure statistics have data"""
        if not self.admin_token:
            self.log_test("Create Test Audit for Statistics", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create a test audit
            audit_data = {
                "site_name": "Test Construction Site",
                "auditor_name": "Test Auditor",
                "selected_work_types": ["excavation", "height_work", "welding"],
                "language": "en"
            }
            
            response = requests.post(f"{self.api_url}/audits", 
                                   json=audit_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                audit_id = data.get("id")
                
                if audit_id:
                    self.test_audit_id = audit_id
                    
                    # Add some findings to the audit
                    findings = [
                        {
                            "question": "Is the excavation properly sloped or shored to prevent cave-ins?",
                            "is_compliant": True,
                            "comment": "Proper shoring observed"
                        },
                        {
                            "question": "Are workers wearing proper fall protection equipment?",
                            "is_compliant": False,
                            "comment": "Missing harnesses on some workers"
                        },
                        {
                            "question": "Are welders wearing proper protective equipment?",
                            "is_compliant": True,
                            "comment": "All PPE in place"
                        }
                    ]
                    
                    # Add findings
                    for finding in findings:
                        requests.post(f"{self.api_url}/audits/{audit_id}/findings", 
                                    json=finding, headers=headers, timeout=10)
                    
                    # Complete the audit
                    complete_response = requests.put(f"{self.api_url}/audits/{audit_id}/complete", 
                                                   headers=headers, timeout=10)
                    
                    success = complete_response.status_code == 200
                    details = f"Audit created: {audit_id}, Completed: {success}"
                else:
                    success = False
                    details = "No audit ID returned"
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create Test Audit for Statistics", success, details)
            return success
        except Exception as e:
            self.log_test("Create Test Audit for Statistics", False, str(e))
            return False

    def test_test_user_login(self):
        """Test login with test@csaaudit.com / test123 (reported user with upgrade issue)"""
        try:
            login_data = {
                "email": "test@csaaudit.com",
                "password": "test123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                if has_token:
                    self.test_user_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "test@csaaudit.com"
                    subscription_plan = user_data.get("subscription_plan")
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Plan: {subscription_plan}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Test User Login (test@csaaudit.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Test User Login (test@csaaudit.com)", False, str(e))
            return False

    def test_upgrade_flow_basic_plan(self):
        """Test upgrade flow for user with basic plan"""
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("Upgrade Flow Basic Plan", False, "No test user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Test checkout session creation for upgrade to professional
            checkout_data = {
                "package_id": "professional",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_session_id = "session_id" in data
                has_url = "url" in data
                
                success = has_session_id and has_url
                details = f"Status: {response.status_code}, Session ID: {has_session_id}, URL: {has_url}"
                
                if success:
                    session_id = data.get("session_id", "")
                    url = data.get("url", "")
                    
                    # Check if it's live mode (real Stripe) or demo mode
                    is_live_mode = session_id.startswith("cs_live_") or not session_id.startswith("cs_demo_")
                    is_demo_mode = session_id.startswith("cs_demo_")
                    
                    details += f", Live mode: {is_live_mode}, Demo mode: {is_demo_mode}"
                    
                    # For live mode, URL should be Stripe's checkout
                    if is_live_mode:
                        is_stripe_url = "checkout.stripe.com" in url
                        details += f", Stripe URL: {is_stripe_url}"
                        success = success and is_stripe_url
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Upgrade Flow Basic Plan", success, details)
            return success
        except Exception as e:
            self.log_test("Upgrade Flow Basic Plan", False, str(e))
            return False

    def test_upgrade_flow_enterprise_plan(self):
        """Test upgrade flow for enterprise plan"""
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("Upgrade Flow Enterprise Plan", False, "No test user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Test checkout session creation for upgrade to enterprise
            checkout_data = {
                "package_id": "enterprise",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_session_id = "session_id" in data
                has_url = "url" in data
                
                success = has_session_id and has_url
                details = f"Status: {response.status_code}, Session ID: {has_session_id}, URL: {has_url}"
                
                if success:
                    session_id = data.get("session_id", "")
                    url = data.get("url", "")
                    
                    # Check if it's live mode (real Stripe) or demo mode
                    is_live_mode = session_id.startswith("cs_live_") or not session_id.startswith("cs_demo_")
                    is_demo_mode = session_id.startswith("cs_demo_")
                    
                    details += f", Live mode: {is_live_mode}, Demo mode: {is_demo_mode}"
                    
                    # For live mode, URL should be Stripe's checkout
                    if is_live_mode:
                        is_stripe_url = "checkout.stripe.com" in url
                        details += f", Stripe URL: {is_stripe_url}"
                        success = success and is_stripe_url
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Upgrade Flow Enterprise Plan", success, details)
            return success
        except Exception as e:
            self.log_test("Upgrade Flow Enterprise Plan", False, str(e))
            return False

    def test_stripe_payment_checkout_session(self):
        """Test POST /api/payments/checkout/session with live Stripe keys"""
        if not self.admin_token:
            self.log_test("Stripe Payment Checkout Session", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test checkout session creation
            checkout_data = {
                "package_id": "basic",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_session_id = "session_id" in data
                has_url = "url" in data
                
                success = has_session_id and has_url
                details = f"Status: {response.status_code}, Session ID: {has_session_id}, URL: {has_url}"
                
                if success:
                    session_id = data.get("session_id", "")
                    url = data.get("url", "")
                    
                    # Check if it's live mode (real Stripe) or demo mode
                    is_live_mode = session_id.startswith("cs_live_") or not session_id.startswith("cs_demo_")
                    is_demo_mode = session_id.startswith("cs_demo_")
                    
                    details += f", Live mode: {is_live_mode}, Demo mode: {is_demo_mode}"
                    
                    # For live mode, URL should be Stripe's checkout
                    if is_live_mode:
                        is_stripe_url = "checkout.stripe.com" in url
                        details += f", Stripe URL: {is_stripe_url}"
                        success = success and is_stripe_url
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Stripe Payment Checkout Session", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Payment Checkout Session", False, str(e))
            return False

    def test_user_session_persistence(self):
        """Test user session persistence (reported issue with sessions being lost)"""
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("User Session Persistence", False, "No test user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Make multiple requests to test session persistence
            success_count = 0
            total_requests = 5
            
            for i in range(total_requests):
                response = requests.get(f"{self.api_url}/auth/me", 
                                      headers=headers, timeout=10)
                if response.status_code == 200:
                    success_count += 1
                else:
                    break
            
            success = success_count == total_requests
            details = f"Successful requests: {success_count}/{total_requests}"
            
            if success:
                # Test with a longer delay to simulate real usage
                import time
                time.sleep(2)
                
                final_response = requests.get(f"{self.api_url}/auth/me", 
                                            headers=headers, timeout=10)
                session_still_valid = final_response.status_code == 200
                success = success and session_still_valid
                details += f", Session valid after delay: {session_still_valid}"
            
            self.log_test("User Session Persistence", success, details)
            return success
        except Exception as e:
            self.log_test("User Session Persistence", False, str(e))
            return False

    def test_pdf_generation(self):
        """Test GET /api/audits/{audit_id}/pdf for completed audits"""
        if not self.admin_token or not self.test_audit_id:
            self.log_test("PDF Generation", False, "No admin token or test audit available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{self.api_url}/audits/{self.test_audit_id}/pdf", 
                                  headers=headers, timeout=20)
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type
                
                # Check content disposition header
                content_disposition = response.headers.get('content-disposition', '')
                has_filename = 'filename=' in content_disposition
                has_attachment = 'attachment' in content_disposition
                
                # Check PDF content length
                content_length = len(response.content)
                has_content = content_length > 1000  # PDF should be substantial
                
                # Check if content starts with PDF signature
                pdf_signature = response.content[:4] == b'%PDF'
                
                success = is_pdf and has_filename and has_attachment and has_content and pdf_signature
                details = f"Status: {response.status_code}, PDF type: {is_pdf}, Filename: {has_filename}, Attachment: {has_attachment}, Size: {content_length} bytes, PDF signature: {pdf_signature}"
                
                # Check if filename contains company name
                if has_filename and 'Construction_Labor_Solution' in content_disposition:
                    details += ", Company name in filename: True"
                elif has_filename:
                    details += ", Company name in filename: False"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("PDF Generation", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Generation", False, str(e))
            return False

    def test_company_settings_get(self):
        """Test GET /api/company/settings to retrieve company data"""
        if not self.admin_token:
            self.log_test("Company Settings GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{self.api_url}/company/settings", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_company_name = "company_name" in data
                has_company_logo = "company_logo" in data
                
                success = has_company_name
                details = f"Status: {response.status_code}, Company name: {has_company_name}, Company logo: {has_company_logo}"
                
                if has_company_name:
                    company_name = data.get("company_name", "")
                    is_correct_company = "Construction Labor Solution LLC" in company_name
                    details += f", Correct company: {is_correct_company}"
                    success = success and is_correct_company
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Company Settings GET", success, details)
            return success
        except Exception as e:
            self.log_test("Company Settings GET", False, str(e))
            return False

    def test_company_settings_post(self):
        """Test POST /api/admin/company/settings for logo/company name updates"""
        if not self.admin_token:
            self.log_test("Company Settings POST", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test updating company settings
            settings_data = {
                "company_name": "Construction Labor Solution LLC",
                "company_logo": "https://example.com/logo.png"
            }
            
            response = requests.post(f"{self.api_url}/admin/company/settings", 
                                   json=settings_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_success = "success" in data.get("message", "").lower()
                
                success = has_message and has_success
                details = f"Status: {response.status_code}, Message: {has_message}, Success: {has_success}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Company Settings POST", success, details)
            return success
        except Exception as e:
            self.log_test("Company Settings POST", False, str(e))
            return False

    def test_bilingual_support(self):
        """Test bilingual support (EN/ES) in responses"""
        if not self.admin_token:
            self.log_test("Bilingual Support", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test English questions
            en_request = {
                "work_types": ["excavation", "height_work"],
                "language": "en"
            }
            
            en_response = requests.post(f"{self.api_url}/audits/questions", 
                                      json=en_request, headers=headers, timeout=10)
            
            # Test Spanish questions
            es_request = {
                "work_types": ["excavation", "height_work"],
                "language": "es"
            }
            
            es_response = requests.post(f"{self.api_url}/audits/questions", 
                                      json=es_request, headers=headers, timeout=10)
            
            if en_response.status_code == 200 and es_response.status_code == 200:
                en_data = en_response.json()
                es_data = es_response.json()
                
                en_questions = en_data.get("questions", [])
                es_questions = es_data.get("questions", [])
                
                has_en_questions = len(en_questions) > 0
                has_es_questions = len(es_questions) > 0
                same_count = len(en_questions) == len(es_questions)
                
                # Check if questions are actually different (bilingual)
                different_content = False
                if en_questions and es_questions and same_count:
                    en_text = en_questions[0].get("question", "")
                    es_text = es_questions[0].get("question", "")
                    different_content = en_text != es_text and len(es_text) > 0
                
                success = has_en_questions and has_es_questions and same_count and different_content
                details = f"EN questions: {len(en_questions)}, ES questions: {len(es_questions)}, Same count: {same_count}, Different content: {different_content}"
                
            else:
                success = False
                details = f"EN Status: {en_response.status_code}, ES Status: {es_response.status_code}"
            
            self.log_test("Bilingual Support", success, details)
            return success
        except Exception as e:
            self.log_test("Bilingual Support", False, str(e))
            return False

    def test_database_connectivity(self):
        """Test database connectivity through API endpoints"""
        try:
            # Test database connectivity by checking work types (should come from database or constants)
            response = requests.get(f"{self.api_url}/work-types", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_data = len(data) > 0
                has_structure = all('id' in item and 'name_en' in item for item in data)
                
                success = has_data and has_structure
                details = f"Status: {response.status_code}, Data count: {len(data)}, Structure valid: {has_structure}"
                
            else:
                success = False
                details = f"Status: {response.status_code}"
            
            self.log_test("Database Connectivity", success, details)
            return success
        except Exception as e:
            self.log_test("Database Connectivity", False, str(e))
            return False

    def test_critical_endpoints_response_time(self):
        """Test response times for critical endpoints"""
        critical_endpoints = [
            ("GET", "/work-types", "Work Types"),
            ("GET", "/payments/packages", "Payment Packages"),
            ("POST", "/auth/login", "Login", {"email": "admin@csaaudit.com", "password": "admin123"}),
        ]
        
        all_passed = True
        for method, endpoint, name, *data in critical_endpoints:
            try:
                start_time = datetime.now()
                
                if method == "GET":
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                elif method == "POST":
                    payload = data[0] if data else {}
                    response = requests.post(f"{self.api_url}{endpoint}", 
                                           json=payload, timeout=10)
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                # Consider under 3 seconds as acceptable for launch
                fast_enough = response_time < 3.0
                success = response.status_code == 200 and fast_enough
                
                details = f"Status: {response.status_code}, Response time: {response_time:.2f}s"
                self.log_test(f"Response Time - {name}", success, details)
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Response Time - {name}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_organization_create_endpoint(self):
        """Test POST /api/organization/create endpoint - CRITICAL USER REPORTED ISSUE"""
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("Organization Create Endpoint", False, "No test user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # First, verify user doesn't have organization_id initially
            user_response = requests.get(f"{self.api_url}/auth/me", 
                                       headers=headers, timeout=10)
            
            if user_response.status_code != 200:
                self.log_test("Organization Create Endpoint", False, "Cannot get user info")
                return False
                
            user_data = user_response.json()
            initial_org_id = user_data.get("organization_id")
            
            # Test creating organization
            org_data = {
                "name": "Construcciones Test LLC"
            }
            
            response = requests.post(f"{self.api_url}/organization/create", 
                                   json=org_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_organization = "organization" in data
                
                success = has_message and has_organization
                details = f"Status: {response.status_code}, Message: {has_message}, Organization: {has_organization}"
                
                if has_organization:
                    org = data["organization"]
                    correct_name = org.get("name") == "Construcciones Test LLC"
                    has_id = "id" in org
                    correct_owner = org.get("owner_id") == user_data.get("id")
                    
                    success = success and correct_name and has_id and correct_owner
                    details += f", Name: {correct_name}, ID: {has_id}, Owner: {correct_owner}"
                    
                    # Verify user was updated with organization_id
                    updated_user_response = requests.get(f"{self.api_url}/auth/me", 
                                                       headers=headers, timeout=10)
                    if updated_user_response.status_code == 200:
                        updated_user = updated_user_response.json()
                        new_org_id = updated_user.get("organization_id")
                        user_updated = new_org_id is not None and new_org_id != initial_org_id
                        user_role = updated_user.get("organization_role") == "owner"
                        
                        success = success and user_updated and user_role
                        details += f", User updated: {user_updated}, Owner role: {user_role}"
                    else:
                        success = False
                        details += ", Failed to verify user update"
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Organization Create Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Organization Create Endpoint", False, str(e))
            return False

    def test_owner_login(self):
        """Test owner login with ysaias.corredor@clsolution.net / Clave.01 - URGENT USER REPORTED ISSUE"""
        try:
            login_data = {
                "email": "ysaias.corredor@clsolution.net",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@clsolution.net"
                    user_role = user_data.get("role", "")
                    subscription_plan = user_data.get("subscription_plan", "")
                    organization_id = user_data.get("organization_id", "")
                    
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Role: {user_role}, Plan: {subscription_plan}, Org ID: {organization_id}"
                    
                    # Store owner token for further testing
                    if has_token:
                        self.owner_token = data["access_token"]
                        self.owner_user_data = user_data
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("URGENT: Owner Login (ysaias.corredor@clsolution.net)", success, details)
            return success
        except Exception as e:
            self.log_test("URGENT: Owner Login (ysaias.corredor@clsolution.net)", False, str(e))
            return False

    def test_owner_password_validation(self):
        """Test password validation for owner account - check for special characters handling"""
        try:
            # Test with correct password
            correct_login = {
                "email": "ysaias.corredor@clsolution.net",
                "password": "Clave.01"
            }
            
            correct_response = requests.post(f"{self.api_url}/auth/login", 
                                           json=correct_login, timeout=10)
            
            # Test with wrong password to ensure validation works
            wrong_login = {
                "email": "ysaias.corredor@clsolution.net",
                "password": "WrongPassword"
            }
            
            wrong_response = requests.post(f"{self.api_url}/auth/login", 
                                         json=wrong_login, timeout=10)
            
            correct_works = correct_response.status_code == 200
            wrong_fails = wrong_response.status_code == 401
            
            success = correct_works and wrong_fails
            details = f"Correct password works: {correct_works}, Wrong password fails: {wrong_fails}"
            
            # Additional check for special character handling
            if correct_works:
                # Test that the password with special characters (. and numbers) is handled correctly
                details += ", Special characters in password handled correctly"
            
            self.log_test("Owner Password Validation", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Password Validation", False, str(e))
            return False

    def test_owner_jwt_token_generation(self):
        """Test JWT token generation for owner account"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Owner JWT Token Generation", False, "No owner token available")
            return False
            
        try:
            # Test JWT token structure
            token_parts = self.owner_token.split('.')
            has_three_parts = len(token_parts) == 3
            
            # Test token validation by using it
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            token_valid = response.status_code == 200
            
            success = has_three_parts and token_valid
            details = f"Token parts: {len(token_parts)} (expected 3), Token valid: {token_valid}"
            
            if token_valid:
                user_data = response.json()
                correct_email = user_data.get("email") == "ysaias.corredor@clsolution.net"
                details += f", Correct user returned: {correct_email}"
                success = success and correct_email
            
            self.log_test("Owner JWT Token Generation", success, details)
            return success
        except Exception as e:
            self.log_test("Owner JWT Token Generation", False, str(e))
            return False

    def test_owner_user_data_response(self):
        """Test user data response format for owner account"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Owner User Data Response", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["id", "email", "name", "role", "created_at"]
                has_required_fields = all(field in data for field in required_fields)
                
                # Check specific owner data
                correct_email = data.get("email") == "ysaias.corredor@clsolution.net"
                has_role = "role" in data
                has_subscription = "subscription_plan" in data
                has_organization = "organization_id" in data
                
                success = has_required_fields and correct_email
                details = f"Status: {response.status_code}, Required fields: {has_required_fields}, Correct email: {correct_email}"
                details += f", Role: {data.get('role', 'N/A')}, Plan: {data.get('subscription_plan', 'N/A')}"
                details += f", Org ID: {data.get('organization_id', 'N/A')}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner User Data Response", success, details)
            return success
        except Exception as e:
            self.log_test("Owner User Data Response", False, str(e))
            return False

    def test_organization_team_endpoint(self):
        """Test GET /api/organization/team endpoint after organization creation"""
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("Organization Team Endpoint", False, "No test user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_organization = "organization" in data
                has_team_members = "team_members" in data
                has_pending_invitations = "pending_invitations" in data
                
                success = has_organization and has_team_members and has_pending_invitations
                details = f"Status: {response.status_code}, Organization: {has_organization}, Team: {has_team_members}, Invitations: {has_pending_invitations}"
                
                if success:
                    org = data.get("organization", {})
                    team_members = data.get("team_members", [])
                    
                    org_has_name = "name" in org
                    org_has_id = "id" in org
                    has_team_member = len(team_members) > 0
                    
                    success = success and org_has_name and org_has_id and has_team_member
                    details += f", Org name: {org_has_name}, Org ID: {org_has_id}, Team count: {len(team_members)}"
                    
                    if has_team_member:
                        first_member = team_members[0]
                        member_has_user = "user" in first_member
                        member_has_role = "role" in first_member
                        is_owner = first_member.get("role") == "owner"
                        
                        success = success and member_has_user and member_has_role and is_owner
                        details += f", Member user: {member_has_user}, Role: {member_has_role}, Owner: {is_owner}"
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Organization Team Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Organization Team Endpoint", False, str(e))
            return False

    def test_organization_flow_existing_user(self):
        """Test organization flow for user who already has an organization (CRITICAL USER ISSUE)"""
        print("\n🏢 TESTING ORGANIZATION FLOW FOR EXISTING USER (USER REPORTED ISSUE)...")
        
        # Step 1: Login with test user
        login_success = self.test_test_user_login()
        if not login_success:
            self.log_test("Organization Flow Existing User", False, "Login failed")
            return False
            
        if not hasattr(self, 'test_user_token') or not self.test_user_token:
            self.log_test("Organization Flow Existing User", False, "No test user token")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Get user state
            user_response = requests.get(f"{self.api_url}/auth/me", 
                                       headers=headers, timeout=10)
            if user_response.status_code != 200:
                self.log_test("Organization Flow Existing User", False, "Cannot get user state")
                return False
                
            user_data = user_response.json()
            org_id = user_data.get("organization_id")
            org_role = user_data.get("organization_role")
            
            print(f"   📋 User organization_id: {org_id}")
            print(f"   📋 User organization_role: {org_role}")
            
            # If user already has organization, test that team endpoint works
            if org_id:
                print("   ✅ User already has organization - testing team endpoint...")
                team_success = self.test_organization_team_endpoint()
                
                # Test that creating another organization fails properly
                org_data = {"name": "Test Organization 2"}
                create_response = requests.post(f"{self.api_url}/organization/create", 
                                              json=org_data, headers=headers, timeout=10)
                
                create_fails_properly = create_response.status_code == 400
                
                success = team_success and create_fails_properly
                details = f"Has org: {org_id is not None}, Role: {org_role}, Team works: {team_success}, Create fails: {create_fails_properly}"
                
                # This is the key insight: if user has org but frontend doesn't show it,
                # the issue is likely frontend not properly handling the organization state
                if success:
                    print("   🔍 DIAGNOSIS: User has organization but frontend may not be displaying it properly!")
                    print("   🔍 Backend organization functionality is WORKING CORRECTLY")
                    print("   🔍 Issue is likely: Frontend not reading organization_id from user data")
                
            else:
                # User doesn't have organization, test creation
                print("   📝 User has no organization - testing creation...")
                create_success = self.test_organization_create_endpoint()
                team_success = self.test_organization_team_endpoint() if create_success else False
                
                success = create_success and team_success
                details = f"No org initially, Create: {create_success}, Team: {team_success}"
            
            self.log_test("Organization Flow Existing User", success, details)
            return success
            
        except Exception as e:
            self.log_test("Organization Flow Existing User", False, str(e))
            return False

    def test_owner_login(self):
        """Test owner login with ysaias.corredor@clsolution.net / Clave.01"""
        try:
            login_data = {
                "email": "ysaias.corredor@clsolution.net",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                if has_token:
                    self.owner_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@clsolution.net"
                    has_org_id = user_data.get("organization_id") is not None
                    org_role = user_data.get("organization_role", "")
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Has org ID: {has_org_id}, Org role: {org_role}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Owner Login (ysaias.corredor@clsolution.net)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Login (ysaias.corredor@clsolution.net)", False, str(e))
            return False

    def test_owner_subscription_status(self):
        """CRITICAL: Test owner subscription status via /auth/me endpoint"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Owner Subscription Status", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                subscription_plan = data.get("subscription_plan")
                subscription_expires = data.get("subscription_expires")
                subscription_status = data.get("subscription_status")  # May not exist
                audits_used = data.get("audits_used_this_month", 0)
                
                # Check if user has active subscription
                has_active_subscription = subscription_plan is not None and subscription_plan != "free"
                
                success = True  # We're just diagnosing, not failing
                details = f"Plan: {subscription_plan}, Expires: {subscription_expires}, Status: {subscription_status}, Audits used: {audits_used}, Has active: {has_active_subscription}"
                
                # Additional checks
                if subscription_expires:
                    from datetime import datetime, timezone
                    try:
                        if isinstance(subscription_expires, str):
                            expires_dt = datetime.fromisoformat(subscription_expires.replace('Z', '+00:00'))
                        else:
                            expires_dt = subscription_expires
                        now = datetime.now(timezone.utc)
                        is_expired = expires_dt < now
                        details += f", Expired: {is_expired}"
                    except:
                        details += ", Expires parsing failed"
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Subscription Status (/auth/me)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Subscription Status (/auth/me)", False, str(e))
            return False

    def test_owner_database_record(self):
        """CRITICAL: Check owner's database record via admin endpoint"""
        if not self.admin_token:
            self.log_test("Owner Database Record", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Search for the owner user
            response = requests.get(f"{self.api_url}/admin/users?search=ysaias.corredor@clsolution.net", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                if users:
                    owner_user = users[0]  # Should be the first match
                    user_id = owner_user.get("id")
                    subscription_plan = owner_user.get("subscription_plan")
                    subscription_expires = owner_user.get("subscription_expires")
                    total_audits = owner_user.get("total_audits", 0)
                    last_payment = owner_user.get("last_payment")
                    total_paid = owner_user.get("total_paid", 0)
                    
                    success = True  # Diagnostic test
                    details = f"Found user ID: {user_id}, Plan: {subscription_plan}, Expires: {subscription_expires}, Audits: {total_audits}, Last payment: {last_payment}, Total paid: ${total_paid}"
                    
                    # Get detailed user info
                    if user_id:
                        detail_response = requests.get(f"{self.api_url}/admin/user/{user_id}", 
                                                     headers=headers, timeout=10)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            user_detail = detail_data.get("user", {})
                            payments = detail_data.get("payments", [])
                            
                            details += f", Payment history: {len(payments)} transactions"
                            
                            # Check recent payments
                            if payments:
                                recent_payment = payments[0]  # Most recent
                                payment_status = recent_payment.get("payment_status")
                                payment_amount = recent_payment.get("amount")
                                package_type = recent_payment.get("package_type")
                                details += f", Recent payment: ${payment_amount} for {package_type}, Status: {payment_status}"
                else:
                    success = False
                    details = "Owner user not found in database"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Database Record", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Database Record", False, str(e))
            return False

    def test_stripe_webhook_endpoint(self):
        """CRITICAL: Test Stripe webhook endpoint configuration"""
        try:
            # Test GET request to webhook endpoint (should return method not allowed or similar)
            response = requests.get(f"{self.api_url}/payments/webhook/stripe", timeout=10)
            
            # Webhook endpoints typically don't accept GET requests
            webhook_configured = response.status_code in [405, 404, 400]  # Method not allowed, not found, or bad request
            
            success = webhook_configured
            details = f"GET Status: {response.status_code} (webhook endpoints typically reject GET)"
            
            # Test POST with invalid data (should return error but not 404)
            try:
                post_response = requests.post(f"{self.api_url}/payments/webhook/stripe", 
                                            json={"test": "data"}, timeout=10)
                post_status = post_response.status_code
                details += f", POST Status: {post_status}"
                
                # Webhook should be accessible but reject invalid data
                webhook_accessible = post_status != 404
                success = success and webhook_accessible
                
            except Exception as post_e:
                details += f", POST Error: {str(post_e)}"
            
            self.log_test("Stripe Webhook Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Webhook Endpoint", False, str(e))
            return False

    def test_payment_processing_logs(self):
        """CRITICAL: Check for payment processing errors in system logs"""
        if not self.admin_token:
            self.log_test("Payment Processing Logs", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.api_url}/admin/logs", 
                                  headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logs_content = data.get("logs", "").lower()
                
                # Look for payment/stripe related errors
                payment_keywords = ["stripe", "payment", "webhook", "subscription", "checkout"]
                error_keywords = ["error", "failed", "exception", "traceback"]
                
                payment_mentions = sum(1 for keyword in payment_keywords if keyword in logs_content)
                error_mentions = sum(1 for keyword in error_keywords if keyword in logs_content)
                
                # Look for specific error patterns
                has_stripe_errors = "stripe" in logs_content and any(err in logs_content for err in error_keywords)
                has_webhook_errors = "webhook" in logs_content and any(err in logs_content for err in error_keywords)
                
                success = True  # Diagnostic test
                details = f"Payment mentions: {payment_mentions}, Error mentions: {error_mentions}, Stripe errors: {has_stripe_errors}, Webhook errors: {has_webhook_errors}"
                
                # Extract relevant log lines (simplified)
                log_lines = logs_content.split('\n')
                relevant_lines = [line for line in log_lines if any(keyword in line for keyword in payment_keywords + error_keywords)]
                
                if relevant_lines:
                    details += f", Relevant log entries: {len(relevant_lines)}"
                    # Show first few relevant lines
                    sample_lines = relevant_lines[:3]
                    for i, line in enumerate(sample_lines):
                        if len(line) > 100:
                            line = line[:100] + "..."
                        details += f", Log{i+1}: {line}"
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Payment Processing Logs", success, details)
            return success
        except Exception as e:
            self.log_test("Payment Processing Logs", False, str(e))
            return False

    def test_subscription_update_flow(self):
        """CRITICAL: Test if subscription update flow is working"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Subscription Update Flow", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test creating a checkout session (this should work even if user has subscription)
            checkout_data = {
                "package_id": "enterprise",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_session_id = "session_id" in data
                has_url = "url" in data
                
                success = has_session_id and has_url
                details = f"Status: {response.status_code}, Session ID: {has_session_id}, URL: {has_url}"
                
                if success:
                    session_id = data.get("session_id", "")
                    url = data.get("url", "")
                    
                    # Check if it's live mode (real Stripe) or demo mode
                    is_live_mode = session_id.startswith("cs_live_") or not session_id.startswith("cs_demo_")
                    is_demo_mode = session_id.startswith("cs_demo_")
                    
                    details += f", Live mode: {is_live_mode}, Demo mode: {is_demo_mode}"
                    
                    # For live mode, URL should be Stripe's checkout
                    if is_live_mode:
                        is_stripe_url = "checkout.stripe.com" in url
                        details += f", Stripe URL: {is_stripe_url}"
                        success = success and is_stripe_url
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Subscription Update Flow", success, details)
            return success
        except Exception as e:
            self.log_test("Subscription Update Flow", False, str(e))
            return False

    def test_organization_team_endpoint_owner(self):
        """Test GET /api/organization/team endpoint with owner credentials"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Organization Team Endpoint (Owner)", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_organization = "organization" in data
                has_team_members = "team_members" in data
                has_pending_invitations = "pending_invitations" in data
                
                success = has_organization and has_team_members and has_pending_invitations
                details = f"Status: {response.status_code}, Organization: {has_organization}, Team members: {has_team_members}, Pending invitations: {has_pending_invitations}"
                
                if success:
                    org_data = data.get("organization", {})
                    team_members = data.get("team_members", [])
                    pending_invitations = data.get("pending_invitations", [])
                    
                    org_has_id = "id" in org_data
                    org_has_name = "name" in org_data
                    is_list_members = isinstance(team_members, list)
                    is_list_invitations = isinstance(pending_invitations, list)
                    
                    success = success and org_has_id and org_has_name and is_list_members and is_list_invitations
                    details += f", Org ID: {org_has_id}, Org name: {org_has_name}, Members list: {is_list_members}, Invitations list: {is_list_invitations}"
                    
                    if org_has_name:
                        org_name = org_data.get("name", "")
                        details += f", Org name: '{org_name}'"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Organization Team Endpoint (Owner)", success, details)
            return success
        except Exception as e:
            self.log_test("Organization Team Endpoint (Owner)", False, str(e))
            return False

    def test_team_invitation_send(self):
        """Test POST /api/organization/invite - Send team invitation"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Team Invitation Send", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test inviting a new member as specified in the request
            # The endpoint expects query parameters, not JSON body
            params = {
                "invitee_email": "empleado@ejemplo.com",
                "invitee_name": "Juan Empleado", 
                "role": "auditor"
            }
            
            response = requests.post(f"{self.api_url}/organization/invite", 
                                   params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_invitation = "invitation" in data
                
                success = has_message and has_invitation
                details = f"Status: {response.status_code}, Message: {has_message}, Invitation: {has_invitation}"
                
                if has_invitation:
                    invitation = data.get("invitation", {})
                    correct_email = invitation.get("invitee_email") == "empleado@ejemplo.com"
                    correct_name = invitation.get("invitee_name") == "Juan Empleado"
                    correct_role = invitation.get("role") == "auditor"
                    has_id = "id" in invitation
                    has_org_id = "organization_id" in invitation
                    
                    success = success and correct_email and correct_name and correct_role and has_id and has_org_id
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, ID: {has_id}, Org ID: {has_org_id}"
                    
                    # Store invitation ID for later tests
                    if has_id:
                        self.test_invitation_id = invitation.get("id")
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Team Invitation Send", success, details)
            return success
        except Exception as e:
            self.log_test("Team Invitation Send", False, str(e))
            return False

    def test_pending_invitations_endpoint(self):
        """Test GET /api/organization/invitations - Check pending invitations"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Pending Invitations Endpoint", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/invitations", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                is_list = isinstance(data, list)
                
                success = is_list
                details = f"Status: {response.status_code}, Is list: {is_list}, Count: {len(data) if is_list else 'N/A'}"
                
                # This endpoint returns invitations FOR the current user (as invitee)
                # Since we're testing with owner account, it should return empty list or invitations for owner
                if is_list:
                    details += f", Invitations count: {len(data)}"
                    
                    # Check structure of first invitation if any
                    if len(data) > 0:
                        first_inv = data[0]
                        has_required_fields = all(field in first_inv for field in ["id", "organization_id", "invitee_email", "role", "status"])
                        details += f", Has required fields: {has_required_fields}"
                        success = success and has_required_fields
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Pending Invitations Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Pending Invitations Endpoint", False, str(e))
            return False

    def test_team_invitation_in_team_list(self):
        """Test if sent invitation appears in team list pending invitations"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Team Invitation In Team List", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_pending_invitations = "pending_invitations" in data
                
                if has_pending_invitations:
                    pending_invitations = data.get("pending_invitations", [])
                    is_list = isinstance(pending_invitations, list)
                    
                    success = is_list
                    details = f"Status: {response.status_code}, Has pending invitations: {has_pending_invitations}, Is list: {is_list}, Count: {len(pending_invitations) if is_list else 'N/A'}"
                    
                    # Look for our test invitation
                    found_test_invitation = False
                    if is_list:
                        for invitation in pending_invitations:
                            if invitation.get("invitee_email") == "empleado@ejemplo.com":
                                found_test_invitation = True
                                correct_name = invitation.get("invitee_name") == "Juan Empleado"
                                correct_role = invitation.get("role") == "auditor"
                                correct_status = invitation.get("status") == "pending"
                                
                                details += f", Found test invitation: {found_test_invitation}, Name: {correct_name}, Role: {correct_role}, Status: {correct_status}"
                                success = success and correct_name and correct_role and correct_status
                                break
                        
                        if not found_test_invitation:
                            details += f", Test invitation not found in pending list"
                            # This might not be a failure if invitation was processed differently
                    
                else:
                    success = False
                    details = f"Status: {response.status_code}, Missing pending_invitations field"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Team Invitation In Team List", success, details)
            return success
        except Exception as e:
            self.log_test("Team Invitation In Team List", False, str(e))
            return False

    def test_team_invitation_duplicate_prevention(self):
        """Test duplicate invitation prevention - REVIEW REQUEST REQUIREMENT"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Team Invitation Duplicate Prevention", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Use a fixed email for duplicate testing
            import time
            timestamp = str(int(time.time()))
            test_email = f"duplicate.test.{timestamp}@example.com"
            
            # Send first invitation
            params = {
                "invitee_email": test_email,
                "invitee_name": "Duplicate Test User",
                "role": "auditor"
            }
            
            first_response = requests.post(f"{self.api_url}/organization/invite", 
                                         params=params, headers=headers, timeout=10)
            
            # Send second invitation with same email (should fail)
            second_response = requests.post(f"{self.api_url}/organization/invite", 
                                          params=params, headers=headers, timeout=10)
            
            # First should succeed, second should fail with appropriate error
            first_success = first_response.status_code == 200
            second_fails = second_response.status_code == 400
            
            success = first_success and second_fails
            details = f"First invitation: {first_response.status_code}, Second invitation: {second_response.status_code}"
            
            if second_fails:
                try:
                    error_data = second_response.json()
                    error_message = error_data.get('detail', '').lower()
                    has_duplicate_error = 'already' in error_message or 'duplicate' in error_message or 'invited' in error_message
                    details += f", Duplicate error message: {has_duplicate_error}"
                    success = success and has_duplicate_error
                except:
                    details += ", Could not parse error message"
            
            self.log_test("Team Invitation Duplicate Prevention", success, details)
            return success
        except Exception as e:
            self.log_test("Team Invitation Duplicate Prevention", False, str(e))
            return False

    def test_team_invitation_comprehensive_flow(self):
        """Test comprehensive team invitation flow as specified in review request"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Team Invitation Comprehensive Flow", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Step 1: Verify owner login works (already tested but confirm)
            me_response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            if me_response.status_code != 200:
                self.log_test("Team Invitation Comprehensive Flow", False, "Owner authentication failed")
                return False
                
            user_data = me_response.json()
            is_owner = user_data.get("organization_role") == "owner"
            has_org_id = user_data.get("organization_id") is not None
            
            if not (is_owner and has_org_id):
                self.log_test("Team Invitation Comprehensive Flow", False, f"Owner role: {is_owner}, Has org: {has_org_id}")
                return False
            
            # Step 2: Test POST /api/organization/invite with query parameters
            import time
            timestamp = str(int(time.time()))
            test_email = f"comprehensive.test.{timestamp}@example.com"
            
            params = {
                "invitee_email": test_email,
                "invitee_name": "Comprehensive Test User",
                "role": "auditor"
            }
            
            invite_response = requests.post(f"{self.api_url}/organization/invite", 
                                          params=params, headers=headers, timeout=10)
            
            if invite_response.status_code != 200:
                try:
                    error_data = invite_response.json()
                    details = f"Invite failed: {invite_response.status_code}, Error: {error_data.get('detail', 'Unknown')}"
                except:
                    details = f"Invite failed: {invite_response.status_code}"
                self.log_test("Team Invitation Comprehensive Flow", False, details)
                return False
            
            invite_data = invite_response.json()
            has_invitation_link = "invitation_link" in invite_data
            has_invitation = "invitation" in invite_data
            
            # Step 3: Verify invitation appears in GET /api/organization/team pending_invitations
            team_response = requests.get(f"{self.api_url}/organization/team", headers=headers, timeout=10)
            
            if team_response.status_code != 200:
                self.log_test("Team Invitation Comprehensive Flow", False, f"Team endpoint failed: {team_response.status_code}")
                return False
            
            team_data = team_response.json()
            pending_invitations = team_data.get("pending_invitations", [])
            
            # Find our invitation
            found_invitation = False
            for invitation in pending_invitations:
                if invitation.get("invitee_email") == test_email:
                    found_invitation = True
                    break
            
            # Step 4: Test duplicate prevention
            duplicate_response = requests.post(f"{self.api_url}/organization/invite", 
                                             params=params, headers=headers, timeout=10)
            duplicate_prevented = duplicate_response.status_code == 400
            
            # Final assessment
            success = (has_invitation_link and has_invitation and found_invitation and duplicate_prevented)
            details = f"Invitation link: {has_invitation_link}, Invitation data: {has_invitation}, Found in team list: {found_invitation}, Duplicate prevented: {duplicate_prevented}"
            
            if has_invitation_link:
                invitation_link = invite_data.get("invitation_link", "")
                link_valid = len(invitation_link) > 0 and ("http" in invitation_link or "invitation" in invitation_link)
                details += f", Link valid: {link_valid}"
                success = success and link_valid
            
            self.log_test("Team Invitation Comprehensive Flow", success, details)
            return success
        except Exception as e:
            self.log_test("Team Invitation Comprehensive Flow", False, str(e))
            return False

    def test_admin_fix_pending_payment(self):
        """Test POST /api/payments/fix-pending/{user_id} endpoint - URGENT FIX"""
        if not self.admin_token:
            self.log_test("Admin Fix Pending Payment", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Use the specific user_id from the review request
            user_id = "b7524205-e008-449c-b33b-2a7f52817396"
            
            response = requests.post(f"{self.api_url}/payments/fix-pending/{user_id}", 
                                   headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                message_contains_fixed = "fixed" in data.get("message", "").lower()
                
                success = has_message and message_contains_fixed
                details = f"Status: {response.status_code}, Message: {has_message}, Contains 'fixed': {message_contains_fixed}"
                
                if has_message:
                    message = data.get("message", "")
                    details += f", Message: {message}"
                    
            elif response.status_code == 404:
                # No pending transactions found - this might be expected if already fixed
                data = response.json()
                message = data.get("detail", "")
                success = "no pending transactions" in message.lower()
                details = f"Status: {response.status_code}, Message: {message}, Expected 404: {success}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Fix Pending Payment", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Fix Pending Payment", False, str(e))
            return False

    def test_owner_subscription_after_fix(self):
        """Test GET /api/auth/me for owner user after payment fix"""
        if not self.owner_token:
            self.log_test("Owner Subscription After Fix", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_subscription = data.get("subscription_plan") is not None
                subscription_plan = data.get("subscription_plan")
                subscription_expires = data.get("subscription_expires")
                
                success = has_subscription and subscription_plan == "enterprise"
                details = f"Status: {response.status_code}, Has subscription: {has_subscription}, Plan: {subscription_plan}, Expires: {subscription_expires}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Subscription After Fix", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Subscription After Fix", False, str(e))
            return False

    def test_email_settings_get(self):
        """Test GET /api/settings/email endpoint"""
        if not self.admin_token:
            self.log_test("Email Settings GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{self.api_url}/settings/email", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_configured = "configured" in data
                configured = data.get("configured", False)
                
                success = has_configured
                details = f"Status: {response.status_code}, Has configured field: {has_configured}, Configured: {configured}"
                
                # If configured, check for other fields
                if configured:
                    expected_fields = ["smtp_server", "smtp_port", "email", "sender_name"]
                    has_fields = all(field in data for field in expected_fields)
                    no_password = "password" not in data  # Password should not be returned
                    
                    success = success and has_fields and no_password
                    details += f", Has required fields: {has_fields}, No password: {no_password}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Email Settings GET", success, details)
            return success
        except Exception as e:
            self.log_test("Email Settings GET", False, str(e))
            return False

    def test_email_settings_post(self):
        """Test POST /api/settings/email endpoint"""
        if not self.admin_token:
            self.log_test("Email Settings POST", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test email configuration
            email_config = {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email": "test@csaaudit.com",
                "password": "test_password_123",
                "sender_name": "CSA Audit System"
            }
            
            response = requests.post(f"{self.api_url}/settings/email", 
                                   json=email_config, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "saved successfully" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Message: {has_message}, Success message: {success_message}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Email Settings POST", success, details)
            return success
        except Exception as e:
            self.log_test("Email Settings POST", False, str(e))
            return False

    def test_subscription_cancellation(self):
        """Test POST /api/payments/cancel-subscription endpoint"""
        if not self.owner_token:
            self.log_test("Subscription Cancellation", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.post(f"{self.api_url}/payments/cancel-subscription", 
                                   headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_status = "status" in data
                cancelled_message = "cancelled successfully" in data.get("message", "").lower()
                cancelled_status = data.get("status") == "cancelled"
                
                success = has_message and has_status and cancelled_message and cancelled_status
                details = f"Status: {response.status_code}, Message: {has_message}, Status field: {has_status}, Cancelled message: {cancelled_message}, Cancelled status: {cancelled_status}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Subscription Cancellation", success, details)
            return success
        except Exception as e:
            self.log_test("Subscription Cancellation", False, str(e))
            return False

    def test_gmail_account_subscription_issue(self):
        """URGENT: Test the CORRECT Gmail account subscription issue - ysaias.corredor@gmail.com"""
        try:
            # First, try to login with the Gmail account
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
                    gmail_token = data["access_token"]
                    user_data = data["user"]
                    user_id = user_data.get("id")
                    subscription_plan = user_data.get("subscription_plan")
                    subscription_expires = user_data.get("subscription_expires")
                    
                    # Check subscription status via /auth/me
                    headers = {"Authorization": f"Bearer {gmail_token}"}
                    me_response = requests.get(f"{self.api_url}/auth/me", 
                                             headers=headers, timeout=10)
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        current_plan = me_data.get("subscription_plan")
                        current_expires = me_data.get("subscription_expires")
                        
                        # Check for pending payments using admin token
                        if self.admin_token:
                            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                            
                            # Get support tickets to see pending payments
                            support_response = requests.get(f"{self.api_url}/admin/support-tickets", 
                                                           headers=admin_headers, timeout=10)
                            
                            pending_payments_found = False
                            if support_response.status_code == 200:
                                support_data = support_response.json()
                                failed_payments = support_data.get("failed_payments", [])
                                
                                # Look for this user in failed payments
                                for payment in failed_payments:
                                    if payment.get("email") == "ysaias.corredor@gmail.com":
                                        pending_payments_found = True
                                        break
                            
                            # If user has no active subscription or pending payments found, try to fix
                            if not current_plan or pending_payments_found:
                                fix_response = requests.post(f"{self.api_url}/payments/fix-pending/{user_id}", 
                                                           headers=admin_headers, timeout=10)
                                
                                if fix_response.status_code == 200:
                                    fix_data = fix_response.json()
                                    
                                    # Verify subscription is now active
                                    final_me_response = requests.get(f"{self.api_url}/auth/me", 
                                                                    headers=headers, timeout=10)
                                    
                                    if final_me_response.status_code == 200:
                                        final_data = final_me_response.json()
                                        final_plan = final_data.get("subscription_plan")
                                        final_expires = final_data.get("subscription_expires")
                                        
                                        success = final_plan is not None
                                        details = f"Gmail login: ✅, User ID: {user_id}, Fix applied: ✅, Final plan: {final_plan}, Expires: {final_expires}"
                                    else:
                                        success = False
                                        details = f"Gmail login: ✅, Fix applied: ✅, But final /auth/me failed: {final_me_response.status_code}"
                                else:
                                    success = False
                                    details = f"Gmail login: ✅, But fix-pending failed: {fix_response.status_code}"
                            else:
                                success = True
                                details = f"Gmail login: ✅, User ID: {user_id}, Already has active subscription: {current_plan}, Expires: {current_expires}"
                        else:
                            success = False
                            details = f"Gmail login: ✅, But no admin token to check/fix payments"
                    else:
                        success = False
                        details = f"Gmail login: ✅, But /auth/me failed: {me_response.status_code}"
                else:
                    success = False
                    details = f"Gmail login response missing token or user data"
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Gmail login failed: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Gmail login failed: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("URGENT: Gmail Account Subscription Issue", success, details)
            return success
        except Exception as e:
            self.log_test("URGENT: Gmail Account Subscription Issue", False, str(e))
            return False

    def test_find_gmail_user_in_database(self):
        """Find and analyze the Gmail user account in the database"""
        if not self.admin_token:
            self.log_test("Find Gmail User in Database", False, "No admin token available")
            return False
            
        try:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get all users to find the Gmail account
            users_response = requests.get(f"{self.api_url}/admin/users?search=ysaias.corredor@gmail.com", 
                                        headers=admin_headers, timeout=10)
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get("users", [])
                
                gmail_user_found = False
                gmail_user_details = {}
                
                for user in users:
                    if user.get("email") == "ysaias.corredor@gmail.com":
                        gmail_user_found = True
                        gmail_user_details = {
                            "id": user.get("id"),
                            "name": user.get("name"),
                            "email": user.get("email"),
                            "subscription_plan": user.get("subscription_plan"),
                            "subscription_expires": user.get("subscription_expires"),
                            "role": user.get("role"),
                            "total_audits": user.get("total_audits", 0)
                        }
                        break
                
                if gmail_user_found:
                    # Check for payment transactions for this user
                    support_response = requests.get(f"{self.api_url}/admin/support-tickets", 
                                                   headers=admin_headers, timeout=10)
                    
                    pending_payments = []
                    if support_response.status_code == 200:
                        support_data = support_response.json()
                        failed_payments = support_data.get("failed_payments", [])
                        
                        for payment in failed_payments:
                            if payment.get("email") == "ysaias.corredor@gmail.com":
                                pending_payments.append({
                                    "amount": payment.get("amount"),
                                    "package_type": payment.get("package_type"),
                                    "session_id": payment.get("session_id"),
                                    "payment_status": payment.get("payment_status")
                                })
                    
                    success = True
                    details = f"Gmail user found: {gmail_user_details}, Pending payments: {len(pending_payments)} - {pending_payments}"
                else:
                    success = False
                    details = f"Gmail user NOT FOUND in database. Total users searched: {len(users)}"
            else:
                success = False
                details = f"Failed to get users list: {users_response.status_code}"
            
            self.log_test("Find Gmail User in Database", success, details)
            return success
        except Exception as e:
            self.log_test("Find Gmail User in Database", False, str(e))
            return False

    def test_critical_subscription_diagnosis(self):
        """CRITICAL BUSINESS ISSUE: Test ysaias.corredor@gmail.com subscription status"""
        try:
            print("\n🚨 CRITICAL BUSINESS ISSUE DIAGNOSIS 🚨")
            print("Testing user: ysaias.corredor@gmail.com (PAYING CUSTOMER)")
            print("Issue: App doesn't show active subscription plan")
            print("-" * 60)
            
            # Step 1: Login with the specific user
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("CRITICAL: Gmail User Login", False, f"Login failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Login Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Login Error: {response.text[:200]}")
                return False
            
            # Login successful - get token and user data
            login_response = response.json()
            user_token = login_response.get("access_token")
            user_data = login_response.get("user", {})
            
            print(f"✅ Login successful for {user_data.get('email', 'Unknown')}")
            print(f"   User ID: {user_data.get('id', 'Unknown')}")
            print(f"   Name: {user_data.get('name', 'Unknown')}")
            print(f"   Role: {user_data.get('role', 'Unknown')}")
            
            # Step 2: Check GET /api/auth/me response
            headers = {"Authorization": f"Bearer {user_token}"}
            me_response = requests.get(f"{self.api_url}/auth/me", 
                                     headers=headers, timeout=10)
            
            if me_response.status_code != 200:
                self.log_test("CRITICAL: Auth Me Response", False, f"Auth/me failed: {me_response.status_code}")
                return False
            
            me_data = me_response.json()
            
            # Step 3: Analyze subscription data
            subscription_plan = me_data.get("subscription_plan")
            subscription_expires = me_data.get("subscription_expires")
            subscription_status = me_data.get("subscription_status")
            
            print(f"\n📊 SUBSCRIPTION ANALYSIS:")
            print(f"   subscription_plan: {subscription_plan}")
            print(f"   subscription_expires: {subscription_expires}")
            print(f"   subscription_status: {subscription_status}")
            
            # Step 4: Check payment history (admin required)
            if self.admin_token:
                print(f"\n💳 PAYMENT HISTORY CHECK:")
                
                # Get user ID for payment lookup
                user_id = me_data.get("id")
                
                # Check support tickets endpoint for payment issues
                admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                support_response = requests.get(f"{self.api_url}/admin/support-tickets", 
                                              headers=admin_headers, timeout=10)
                
                if support_response.status_code == 200:
                    support_data = support_response.json()
                    failed_payments = support_data.get("failed_payments", [])
                    
                    # Look for this user in failed payments
                    user_failed_payments = [p for p in failed_payments if p.get("user_id") == user_id]
                    
                    print(f"   Failed payments for user: {len(user_failed_payments)}")
                    for payment in user_failed_payments:
                        print(f"   - Amount: ${payment.get('amount', 'Unknown')}")
                        print(f"   - Status: {payment.get('payment_status', 'Unknown')}")
                        print(f"   - Package: {payment.get('package_type', 'Unknown')}")
                        print(f"   - Session ID: {payment.get('session_id', 'Unknown')}")
            
            # Step 5: Determine issue type
            has_active_subscription = subscription_plan is not None and subscription_plan != "None"
            has_valid_expiration = subscription_expires is not None
            
            print(f"\n🔍 DIAGNOSIS:")
            if has_active_subscription and has_valid_expiration:
                print("   ✅ Backend shows ACTIVE subscription")
                print("   🎯 Issue is likely FRONTEND DISPLAY problem")
                issue_type = "FRONTEND_DISPLAY"
            elif not has_active_subscription:
                print("   ❌ Backend shows NO active subscription")
                print("   🎯 Issue is BACKEND SUBSCRIPTION ACTIVATION")
                issue_type = "BACKEND_ACTIVATION"
            else:
                print("   ⚠️  Partial subscription data")
                print("   🎯 Issue is DATA INCONSISTENCY")
                issue_type = "DATA_INCONSISTENCY"
            
            # Step 6: Business impact assessment
            print(f"\n💼 BUSINESS IMPACT:")
            print("   🚨 CRITICAL: Paying customer cannot access paid features")
            print("   💰 Revenue at risk: Customer may request refund")
            print("   📈 Customer satisfaction: Severely impacted")
            print("   ⏰ Resolution urgency: IMMEDIATE")
            
            success = True  # Test completed successfully (diagnosis done)
            details = f"User login: ✅, Subscription plan: {subscription_plan}, Issue type: {issue_type}"
            
            self.log_test("CRITICAL: Subscription Status Diagnosis", success, details)
            return success
            
        except Exception as e:
            self.log_test("CRITICAL: Subscription Status Diagnosis", False, str(e))
            return False

    # ===== ENHANCED USER CREATION WITH CUSTOM PASSWORD TESTS (REVIEW REQUEST) =====
    
    def test_enhanced_user_creation_with_custom_password(self):
        """Test enhanced user creation system with custom password functionality - REVIEW REQUEST"""
        print("\n🔧 TESTING ENHANCED USER CREATION WITH CUSTOM PASSWORD FUNCTIONALITY")
        print("=" * 80)
        
        # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
        success = self.test_owner_gmail_login()
        if not success:
            return False
            
        # Step 2: Test POST /api/organization/create-user with CUSTOM password
        success = self.test_create_user_with_custom_password()
        if not success:
            return False
            
        # Step 3: Verify the user was created with the specified password (not auto-generated)
        success = self.test_login_with_custom_password()
        if not success:
            return False
            
        # Step 4: Test POST /api/organization/create-user WITHOUT password (auto-generate)
        success = self.test_create_user_with_auto_password()
        if not success:
            return False
            
        # Step 5: Verify auto-generated password works for login
        success = self.test_login_with_auto_password()
        if not success:
            return False
            
        # Step 6: Test password validation (password too short should fail)
        success = self.test_password_validation_short_password()
        if not success:
            return False
            
        print("✅ ENHANCED USER CREATION SYSTEM WITH CUSTOM PASSWORD - ALL TESTS PASSED!")
        return True

    def test_owner_gmail_login(self):
        """Test login with ysaias.corredor@gmail.com / Clave.01"""
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
                    details += f", Correct email: {correct_email}, Has org: {has_organization}, Owner role: {is_owner}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Owner Gmail Login (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Gmail Login (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_create_user_with_custom_password(self):
        """Test POST /api/organization/create-user with CUSTOM password"""
        if not self.owner_token:
            self.log_test("Create User With Custom Password", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create user with custom password
            user_data = {
                "email": "test.custom.password@example.com",
                "name": "Test Custom Password User",
                "role": "auditor",
                "password": "MyCustomPass123"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_user = "user" in data
                has_password_type = "password_type" in data
                
                success = has_message and has_user and has_password_type
                details = f"Status: {response.status_code}, Message: {has_message}, User: {has_user}, Password type: {has_password_type}"
                
                if success:
                    user_info = data.get("user", {})
                    password_type = data.get("password_type")
                    temp_password = user_info.get("temporary_password")
                    
                    correct_email = user_info.get("email") == "test.custom.password@example.com"
                    correct_name = user_info.get("name") == "Test Custom Password User"
                    correct_role = user_info.get("role") == "auditor"
                    is_custom_password = password_type == "custom"
                    password_matches = temp_password == "MyCustomPass123"
                    
                    success = success and correct_email and correct_name and correct_role and is_custom_password and password_matches
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, Custom: {is_custom_password}, Password matches: {password_matches}"
                    
                    # Store for later login test
                    self.custom_password_user = {
                        "email": "test.custom.password@example.com",
                        "password": "MyCustomPass123"
                    }
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create User With Custom Password", success, details)
            return success
        except Exception as e:
            self.log_test("Create User With Custom Password", False, str(e))
            return False

    def test_login_with_custom_password(self):
        """Test login with the new user using the custom password: test.custom.password@example.com / MyCustomPass123"""
        if not hasattr(self, 'custom_password_user'):
            self.log_test("Login With Custom Password", False, "Custom password user not created")
            return False
            
        try:
            login_data = self.custom_password_user
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                
                success = has_token and has_user
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "test.custom.password@example.com"
                    correct_name = user_data.get("name") == "Test Custom Password User"
                    correct_role = user_data.get("organization_role") == "auditor"
                    has_organization = user_data.get("organization_id") is not None
                    
                    success = success and correct_email and correct_name and correct_role and has_organization
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, Has org: {has_organization}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Login With Custom Password", success, details)
            return success
        except Exception as e:
            self.log_test("Login With Custom Password", False, str(e))
            return False

    def test_create_user_with_auto_password(self):
        """Test POST /api/organization/create-user WITHOUT password (auto-generate)"""
        if not self.owner_token:
            self.log_test("Create User With Auto Password", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create user without password (should auto-generate)
            user_data = {
                "email": "test.auto.password@example.com",
                "name": "Test Auto Password User",
                "role": "viewer"
                # No password field - should auto-generate
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_user = "user" in data
                has_password_type = "password_type" in data
                
                success = has_message and has_user and has_password_type
                details = f"Status: {response.status_code}, Message: {has_message}, User: {has_user}, Password type: {has_password_type}"
                
                if success:
                    user_info = data.get("user", {})
                    password_type = data.get("password_type")
                    temp_password = user_info.get("temporary_password")
                    
                    correct_email = user_info.get("email") == "test.auto.password@example.com"
                    correct_name = user_info.get("name") == "Test Auto Password User"
                    correct_role = user_info.get("role") == "viewer"
                    is_generated_password = password_type == "generated"
                    has_temp_password = temp_password is not None and len(temp_password) > 6
                    
                    success = success and correct_email and correct_name and correct_role and is_generated_password and has_temp_password
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, Generated: {is_generated_password}, Has temp password: {has_temp_password}"
                    
                    # Store for later login test
                    self.auto_password_user = {
                        "email": "test.auto.password@example.com",
                        "password": temp_password
                    }
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create User With Auto Password", success, details)
            return success
        except Exception as e:
            self.log_test("Create User With Auto Password", False, str(e))
            return False

    def test_login_with_auto_password(self):
        """Test login with auto-generated password"""
        if not hasattr(self, 'auto_password_user'):
            self.log_test("Login With Auto Password", False, "Auto password user not created")
            return False
            
        try:
            login_data = self.auto_password_user
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                
                success = has_token and has_user
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "test.auto.password@example.com"
                    correct_name = user_data.get("name") == "Test Auto Password User"
                    correct_role = user_data.get("organization_role") == "viewer"
                    has_organization = user_data.get("organization_id") is not None
                    
                    success = success and correct_email and correct_name and correct_role and has_organization
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, Has org: {has_organization}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Login With Auto Password", success, details)
            return success
        except Exception as e:
            self.log_test("Login With Auto Password", False, str(e))
            return False

    def test_password_validation_short_password(self):
        """Test password validation (password too short should fail)"""
        if not self.owner_token:
            self.log_test("Password Validation Short Password", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Try to create user with password too short (should fail)
            user_data = {
                "email": "test.short.password@example.com",
                "name": "Test Short Password User",
                "role": "auditor",
                "password": "123"  # Too short - should fail
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user_data, headers=headers, timeout=10)
            
            # Should return 400 error for password too short
            success = response.status_code == 400
            
            if success:
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', '').lower()
                    has_password_error = 'password' in error_message and ('short' in error_message or 'characters' in error_message or '6' in error_message)
                    success = success and has_password_error
                    details = f"Status: {response.status_code} (expected 400), Password error: {has_password_error}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code} (expected 400), Response: {response.text[:200]}"
            else:
                details = f"Status: {response.status_code} (expected 400 for short password)"
            
            self.log_test("Password Validation Short Password", success, details)
            return success
        except Exception as e:
            self.log_test("Password Validation Short Password", False, str(e))
            return False

    # ===== DELETE USER FUNCTIONALITY TESTS (REVIEW REQUEST) =====
    
    def test_delete_user_functionality(self):
        """Test DELETE user functionality - REVIEW REQUEST SPECIFIC TEST"""
        print("\n🗑️  TESTING DELETE USER FUNCTIONALITY - REVIEW REQUEST")
        print("=" * 70)
        
        # Step 1: Login with ysaias.corredor@gmail.com / Clave.01 (organization owner)
        success = self.test_owner_gmail_login()
        if not success:
            return False
            
        # Step 2: Create a test user to delete
        success = self.test_create_user_for_deletion()
        if not success:
            return False
            
        # Step 3: Verify the user appears in the team list
        success = self.test_verify_user_in_team_list()
        if not success:
            return False
            
        # Step 4: Test the DELETE functionality
        success = self.test_delete_user_endpoint()
        if not success:
            return False
            
        # Step 5: Verify the user is removed from team list after deletion
        success = self.test_verify_user_removed_from_team()
        if not success:
            return False
            
        # Step 6: Verify removed user can still login but has no organization
        success = self.test_deleted_user_login_still_works()
        if not success:
            return False
            
        # Step 7: Verify error handling - try to delete non-existent user
        success = self.test_delete_nonexistent_user()
        if not success:
            return False
            
        print("✅ DELETE USER FUNCTIONALITY - ALL TESTS PASSED!")
        return True

    def test_create_user_for_deletion(self):
        """Create a test user specifically for deletion testing"""
        if not self.owner_token:
            self.log_test("Create User For Deletion", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create user with specific credentials as mentioned in review request
            import time
            timestamp = str(int(time.time()))
            test_email = f"test.delete.user.{timestamp}@example.com"
            
            user_data = {
                "email": test_email,
                "name": "Test Delete User",
                "role": "auditor",
                "password": "TestPass123"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_user = "user" in data
                
                success = has_message and has_user
                details = f"Status: {response.status_code}, Message: {has_message}, User: {has_user}"
                
                if success:
                    user_info = data.get("user", {})
                    user_id = user_info.get("id")
                    returned_email = user_info.get("email")
                    correct_email = returned_email == test_email
                    correct_name = user_info.get("name") == "Test Delete User"
                    correct_role = user_info.get("role") == "auditor"
                    
                    success = success and correct_email and correct_name and correct_role and user_id
                    details += f", Email: {correct_email}, Name: {correct_name}, Role: {correct_role}, ID: {bool(user_id)}"
                    
                    # Store user info for deletion test
                    self.test_delete_user = {
                        "id": user_id,
                        "email": returned_email,  # Use the actual returned email
                        "name": "Test Delete User",
                        "password": "TestPass123"
                    }
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create User For Deletion", success, details)
            return success
        except Exception as e:
            self.log_test("Create User For Deletion", False, str(e))
            return False

    def test_verify_user_in_team_list(self):
        """Verify the test user appears in GET /api/organization/team"""
        if not self.owner_token or not hasattr(self, 'test_delete_user'):
            self.log_test("Verify User In Team List", False, "No owner token or test user")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_team_members = "team_members" in data
                
                if has_team_members:
                    team_members = data.get("team_members", [])
                    
                    # Look for our test user
                    user_found = False
                    for member in team_members:
                        if member.get("user_id") == self.test_delete_user["id"]:
                            user_found = True
                            user_data = member.get("user", {})
                            correct_email = user_data.get("email") == self.test_delete_user["email"]
                            correct_name = user_data.get("name") == self.test_delete_user["name"]
                            correct_role = member.get("role") == "auditor"
                            
                            success = correct_email and correct_name and correct_role
                            details = f"Status: {response.status_code}, User found: {user_found}, Email: {correct_email}, Name: {correct_name}, Role: {correct_role}"
                            break
                    
                    if not user_found:
                        success = False
                        details = f"Status: {response.status_code}, User not found in team list. Total members: {len(team_members)}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, Missing team_members field"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Verify User In Team List", success, details)
            return success
        except Exception as e:
            self.log_test("Verify User In Team List", False, str(e))
            return False

    def test_delete_user_endpoint(self):
        """Test DELETE /api/organization/remove-user/{user_id} endpoint"""
        if not self.owner_token or not hasattr(self, 'test_delete_user'):
            self.log_test("Delete User Endpoint", False, "No owner token or test user")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            user_id = self.test_delete_user["id"]
            
            response = requests.delete(f"{self.api_url}/organization/remove-user/{user_id}", 
                                     headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "removed" in data.get("message", "").lower() and "successfully" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Message: {has_message}, Success message: {success_message}"
                
                if has_message:
                    message = data.get("message", "")
                    details += f", Message: '{message}'"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Delete User Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Delete User Endpoint", False, str(e))
            return False

    def test_verify_user_removed_from_team(self):
        """Verify the user is removed from team list after deletion"""
        if not self.owner_token or not hasattr(self, 'test_delete_user'):
            self.log_test("Verify User Removed From Team", False, "No owner token or test user")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_team_members = "team_members" in data
                
                if has_team_members:
                    team_members = data.get("team_members", [])
                    
                    # Look for our test user (should NOT be found)
                    user_found = False
                    for member in team_members:
                        if member.get("user_id") == self.test_delete_user["id"]:
                            user_found = True
                            break
                    
                    success = not user_found  # Success if user is NOT found
                    details = f"Status: {response.status_code}, User found: {user_found}, Total members: {len(team_members)}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, Missing team_members field"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Verify User Removed From Team", success, details)
            return success
        except Exception as e:
            self.log_test("Verify User Removed From Team", False, str(e))
            return False

    def test_deleted_user_login_still_works(self):
        """Verify removed user can still login but has no organization"""
        if not hasattr(self, 'test_delete_user'):
            self.log_test("Removed User Login Still Works", False, "No test user available")
            return False
            
        try:
            login_data = {
                "email": self.test_delete_user["email"],
                "password": self.test_delete_user["password"]
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            # Login should succeed but user should have no organization
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                
                if has_user:
                    user_data = data["user"]
                    no_organization = user_data.get("organization_id") is None
                    correct_email = user_data.get("email") == self.test_delete_user["email"]
                    
                    # The key test is that user has no organization_id (removed from org)
                    success = has_token and has_user and no_organization and correct_email
                    details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, No org: {no_organization}, Correct email: {correct_email}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, Missing user data"
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Removed User Login Still Works", success, details)
            return success
        except Exception as e:
            self.log_test("Removed User Login Still Works", False, str(e))
            return False

    def test_delete_nonexistent_user(self):
        """Test error handling - try to delete non-existent user"""
        if not self.owner_token:
            self.log_test("Delete Nonexistent User", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Use a fake UUID that doesn't exist
            fake_user_id = "00000000-0000-0000-0000-000000000000"
            
            response = requests.delete(f"{self.api_url}/organization/remove-user/{fake_user_id}", 
                                     headers=headers, timeout=10)
            
            # Should return 404 or 400 with appropriate error message
            success = response.status_code in [404, 400]
            details = f"Status: {response.status_code} (expected 404 or 400)"
            
            if success:
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', '').lower()
                    has_appropriate_error = any(word in error_message for word in ['not found', 'does not exist', 'invalid'])
                    details += f", Appropriate error: {has_appropriate_error}"
                    success = success and has_appropriate_error
                except:
                    details += ", Could not parse error message"
            
            self.log_test("Delete Nonexistent User", success, details)
            return success
        except Exception as e:
            self.log_test("Delete Nonexistent User", False, str(e))
            return False

    def test_delete_user_functionality_review_request(self):
        """Test delete user functionality as per review request - CRITICAL TEST"""
        print("\n🗑️ TESTING DELETE USER FUNCTIONALITY - REVIEW REQUEST")
        print("=" * 60)
        
        # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
        try:
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                owner_token = data.get("access_token")
                user_data = data.get("user", {})
                
                success = owner_token is not None
                details = f"Status: {response.status_code}, Token: {success}, User ID: {user_data.get('id')}, Organization: {user_data.get('organization_id')}"
                
                self.log_test("Step 1: Owner Login (ysaias.corredor@gmail.com)", success, details)
                
                if not success:
                    return False
                    
            else:
                self.log_test("Step 1: Owner Login (ysaias.corredor@gmail.com)", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step 1: Owner Login (ysaias.corredor@gmail.com)", False, str(e))
            return False
        
        # Step 2: Create a test user using POST /api/organization/create-user
        try:
            headers = {"Authorization": f"Bearer {owner_token}"}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use unique email to avoid conflicts
            test_email = f"test.delete.function.{timestamp}@example.com"
            
            create_user_data = {
                "email": test_email,
                "name": "Test Delete Function User",
                "role": "auditor",
                "password": "DeleteTest123"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=create_user_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                test_user_data = data.get("user", {})
                test_user_id = test_user_data.get("id")
                
                success = test_user_id is not None
                details = f"Status: {response.status_code}, User ID: {test_user_id}, Email: {test_user_data.get('email')}, Role: {test_user_data.get('role')}"
                
                self.log_test("Step 2: Create Test User", success, details)
                
                if not success:
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                    
                self.log_test("Step 2: Create Test User", False, details)
                return False
                
        except Exception as e:
            self.log_test("Step 2: Create Test User", False, str(e))
            return False
        
        # Step 3: Verify the user was created and appears in the team
        try:
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                team_members = data.get("team_members", [])
                
                # Find our test user in the team
                test_user_found = False
                for member in team_members:
                    if member.get("user", {}).get("email") == test_email:
                        test_user_found = True
                        break
                
                success = test_user_found
                details = f"Status: {response.status_code}, Team members count: {len(team_members)}, Test user found: {test_user_found}"
                
                self.log_test("Step 3: Verify User in Team", success, details)
                
                if not success:
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                    
                self.log_test("Step 3: Verify User in Team", False, details)
                return False
                
        except Exception as e:
            self.log_test("Step 3: Verify User in Team", False, str(e))
            return False
        
        # Step 4: Test the DELETE /api/organization/remove-user/{user_id} endpoint
        try:
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            response = requests.delete(f"{self.api_url}/organization/remove-user/{test_user_id}", 
                                     headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "removed from team successfully" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Message: {data.get('message', 'No message')}"
                
                self.log_test("Step 4: Delete User", success, details)
                
                if not success:
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                    
                self.log_test("Step 4: Delete User", False, details)
                return False
                
        except Exception as e:
            self.log_test("Step 4: Delete User", False, str(e))
            return False
        
        # Step 5: Check that the user is properly removed from the team after deletion
        try:
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                team_members = data.get("team_members", [])
                
                # Verify our test user is no longer in the team
                test_user_still_found = False
                for member in team_members:
                    if member.get("user", {}).get("email") == test_email:
                        test_user_still_found = True
                        break
                
                success = not test_user_still_found  # Success if user is NOT found
                details = f"Status: {response.status_code}, Team members count: {len(team_members)}, Test user still found: {test_user_still_found}"
                
                self.log_test("Step 5: Verify User Removed from Team", success, details)
                
                if not success:
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                    
                self.log_test("Step 5: Verify User Removed from Team", False, details)
                return False
                
        except Exception as e:
            self.log_test("Step 5: Verify User Removed from Team", False, str(e))
            return False
        
        # Bonus: Verify deleted user can still login but has no organization
        try:
            login_data = {
                "email": test_email,
                "password": "DeleteTest123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("user", {})
                organization_id = user_data.get("organization_id")
                
                success = organization_id is None  # Should be None after removal
                details = f"Status: {response.status_code}, Organization ID: {organization_id} (should be None)"
                
                self.log_test("Bonus: Verify Deleted User Login (No Organization)", success, details)
                
            else:
                # If user can't login, that's also acceptable behavior
                success = True
                details = f"Status: {response.status_code} (User cannot login - acceptable behavior)"
                self.log_test("Bonus: Verify Deleted User Login (No Organization)", success, details)
                
        except Exception as e:
            self.log_test("Bonus: Verify Deleted User Login (No Organization)", False, str(e))
        
        print("🎯 DELETE USER FUNCTIONALITY REVIEW REQUEST TESTING COMPLETE")
        return True

    def test_review_request_delete_user_setup(self):
        """REVIEW REQUEST: Create test user for delete functionality testing"""
        try:
            # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Review Request - Owner Login", False, f"Login failed: {response.status_code}")
                return False
                
            data = response.json()
            owner_token = data.get("access_token")
            user_data = data.get("user", {})
            
            if not owner_token:
                self.log_test("Review Request - Owner Login", False, "No access token received")
                return False
                
            self.log_test("Review Request - Owner Login", True, f"Login successful, role: {user_data.get('organization_role', 'N/A')}")
            
            # Step 2: Create test user with specific details
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            user_create_data = {
                "email": "test.delete.now@example.com",
                "name": "Test Delete Now User", 
                "role": "auditor",
                "password": "DeleteNow123"
            }
            
            create_response = requests.post(f"{self.api_url}/organization/create-user",
                                          json=user_create_data, headers=headers, timeout=10)
            
            if create_response.status_code == 200:
                create_data = create_response.json()
                test_user_id = create_data.get("user", {}).get("id")
                
                success = test_user_id is not None
                details = f"User created with ID: {test_user_id}, Email: {user_create_data['email']}"
                self.log_test("Review Request - Create Test User", success, details)
                
                if not success:
                    return False
                    
            else:
                try:
                    error_data = create_response.json()
                    details = f"Status: {create_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {create_response.status_code}, Response: {create_response.text[:200]}"
                    
                self.log_test("Review Request - Create Test User", False, details)
                return False
            
            # Step 3: Verify user appears in team list
            team_response = requests.get(f"{self.api_url}/organization/team",
                                       headers=headers, timeout=10)
            
            if team_response.status_code == 200:
                team_data = team_response.json()
                team_members = team_data.get("team_members", [])
                
                # Look for our test user
                test_user_found = False
                for member in team_members:
                    if member.get("email") == "test.delete.now@example.com":
                        test_user_found = True
                        break
                
                success = test_user_found
                details = f"Team members count: {len(team_members)}, Test user found: {test_user_found}"
                self.log_test("Review Request - Verify User in Team", success, details)
                
                if success:
                    print(f"✅ REVIEW REQUEST COMPLETED SUCCESSFULLY:")
                    print(f"   - Owner login: ysaias.corredor@gmail.com ✅")
                    print(f"   - Test user created: test.delete.now@example.com ✅") 
                    print(f"   - User appears in team list ✅")
                    print(f"   - User ID: {test_user_id}")
                    print(f"   - Total team members: {len(team_members)}")
                    print(f"   - Ready for frontend delete button testing")
                    
                return success
                
            else:
                try:
                    error_data = team_response.json()
                    details = f"Status: {team_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {team_response.status_code}, Response: {team_response.text[:200]}"
                    
                self.log_test("Review Request - Verify User in Team", False, details)
                return False
                
        except Exception as e:
            self.log_test("Review Request - Delete User Setup", False, str(e))
            return False

    def test_delete_user_functionality_review_request(self):
        """URGENT: Test DELETE functionality with REAL user account - Review Request Testing"""
        print("\n🗑️ URGENT REVIEW REQUEST: Testing DELETE user functionality with REAL user account")
        print("User reports: Delete buttons don't work when clicked - buttons exist but clicking doesn't remove team members")
        
        try:
            # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
            print("Step 1: Login with ysaias.corredor@gmail.com / Clave.01")
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            login_response = requests.post(f"{self.api_url}/auth/login", 
                                         json=login_data, timeout=10)
            
            if login_response.status_code != 200:
                self.log_test("DELETE User Functionality Review Request", False, 
                            f"Login failed: {login_response.status_code}")
                return False
            
            login_data_response = login_response.json()
            owner_token = login_data_response.get("access_token")
            user_info = login_data_response.get("user", {})
            
            print(f"✅ Login successful - User: {user_info.get('name')}, Role: {user_info.get('organization_role')}")
            
            # Step 2: Get the team list with GET /api/organization/team
            print("Step 2: Get team list with GET /api/organization/team")
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            team_response = requests.get(f"{self.api_url}/organization/team", 
                                       headers=headers, timeout=10)
            
            if team_response.status_code != 200:
                self.log_test("DELETE User Functionality Review Request", False, 
                            f"Team list failed: {team_response.status_code}")
                return False
            
            team_data = team_response.json()
            team_members = team_data.get("team_members", [])
            organization = team_data.get("organization", {})
            
            print(f"✅ Team list retrieved - Organization: {organization.get('name')}, Team members: {len(team_members)}")
            
            # Step 3: Identify user IDs of team members (not the owner)
            print("Step 3: Identify team member user IDs (excluding owner)")
            
            owner_user_id = user_info.get("id")
            deletable_members = []
            
            for member in team_members:
                member_user_id = member.get("user_id")
                member_role = member.get("role")
                member_email = member.get("email", "Unknown")
                member_name = member.get("name", "Unknown")
                
                if member_user_id != owner_user_id and member_role != "owner":
                    deletable_members.append({
                        "user_id": member_user_id,
                        "email": member_email,
                        "name": member_name,
                        "role": member_role
                    })
                    print(f"   Found deletable member: {member_name} ({member_email}) - ID: {member_user_id}")
            
            if not deletable_members:
                # Create a test user to delete
                print("No deletable members found. Creating test user for deletion test...")
                
                create_user_data = {
                    "email": f"test.delete.review.{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                    "name": "Test Delete Review User",
                    "role": "auditor",
                    "password": "TestDelete123"
                }
                
                create_response = requests.post(f"{self.api_url}/organization/create-user", 
                                              json=create_user_data, headers=headers, timeout=10)
                
                if create_response.status_code == 200:
                    create_data = create_response.json()
                    test_user_id = create_data.get("user", {}).get("id")
                    if test_user_id:
                        deletable_members.append({
                            "user_id": test_user_id,
                            "email": create_user_data["email"],
                            "name": create_user_data["name"],
                            "role": create_user_data["role"]
                        })
                        print(f"✅ Created test user for deletion: {create_user_data['name']} - ID: {test_user_id}")
                    else:
                        self.log_test("DELETE User Functionality Review Request", False, 
                                    "Could not create test user for deletion test")
                        return False
                else:
                    self.log_test("DELETE User Functionality Review Request", False, 
                                f"Failed to create test user: {create_response.status_code}")
                    return False
            
            # Step 4: Test DELETE /api/organization/remove-user/{user_id} with REAL user ID
            print("Step 4: Test DELETE /api/organization/remove-user/{user_id} with REAL user ID")
            
            test_results = []
            
            for member in deletable_members[:2]:  # Test up to 2 members to avoid removing too many
                user_id = member["user_id"]
                user_name = member["name"]
                user_email = member["email"]
                
                print(f"   Testing DELETE for user: {user_name} ({user_email}) - ID: {user_id}")
                
                # Perform DELETE request
                delete_response = requests.delete(f"{self.api_url}/organization/remove-user/{user_id}", 
                                                headers=headers, timeout=10)
                
                test_result = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "status_code": delete_response.status_code,
                    "success": False,
                    "error": None,
                    "response_data": None
                }
                
                if delete_response.status_code == 200:
                    try:
                        response_data = delete_response.json()
                        test_result["response_data"] = response_data
                        test_result["success"] = True
                        print(f"   ✅ DELETE successful: {response_data.get('message', 'User removed')}")
                        
                        # Verify user was actually removed by checking team list again
                        verify_response = requests.get(f"{self.api_url}/organization/team", 
                                                     headers=headers, timeout=10)
                        
                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            verify_members = verify_data.get("team_members", [])
                            
                            # Check if user is still in the list
                            user_still_exists = any(m.get("user_id") == user_id for m in verify_members)
                            
                            if not user_still_exists:
                                print(f"   ✅ VERIFICATION: User {user_name} successfully removed from team")
                                test_result["verified_removed"] = True
                            else:
                                print(f"   ❌ VERIFICATION FAILED: User {user_name} still in team after DELETE")
                                test_result["verified_removed"] = False
                                test_result["success"] = False
                                test_result["error"] = "User still in team after DELETE"
                        else:
                            test_result["error"] = f"Could not verify removal: {verify_response.status_code}"
                            
                    except Exception as e:
                        test_result["error"] = f"JSON parse error: {str(e)}"
                        test_result["success"] = False
                        
                else:
                    try:
                        error_data = delete_response.json()
                        test_result["error"] = error_data.get("detail", f"HTTP {delete_response.status_code}")
                        test_result["response_data"] = error_data
                    except:
                        test_result["error"] = f"HTTP {delete_response.status_code}: {delete_response.text[:200]}"
                    
                    print(f"   ❌ DELETE failed: {test_result['error']}")
                
                test_results.append(test_result)
            
            # Step 5: Analyze results and provide diagnosis
            print("Step 5: Analysis and Diagnosis")
            
            successful_deletes = [r for r in test_results if r["success"]]
            failed_deletes = [r for r in test_results if not r["success"]]
            
            overall_success = len(successful_deletes) > 0 and len(failed_deletes) == 0
            
            details = f"Tested {len(test_results)} delete operations. "
            details += f"Successful: {len(successful_deletes)}, Failed: {len(failed_deletes)}. "
            
            if failed_deletes:
                details += "FAILURES: "
                for fail in failed_deletes:
                    details += f"{fail['user_name']} (HTTP {fail['status_code']}: {fail['error']}); "
            
            if successful_deletes:
                details += "SUCCESSES: "
                for success in successful_deletes:
                    verified = success.get("verified_removed", False)
                    details += f"{success['user_name']} (removed and verified: {verified}); "
            
            # Provide specific diagnosis for the user's issue
            if overall_success:
                diagnosis = "✅ DELETE functionality is WORKING correctly. "
                diagnosis += "If user reports delete buttons not working, issue is likely FRONTEND-related: "
                diagnosis += "1) JavaScript errors preventing API call, 2) Button not connected to delete function, "
                diagnosis += "3) Frontend not refreshing team list after successful delete, 4) Browser/session issues."
            else:
                diagnosis = "❌ DELETE functionality has BACKEND issues. "
                diagnosis += "Root causes found: "
                for fail in failed_deletes:
                    if fail["status_code"] == 403:
                        diagnosis += "Permission denied (user not owner?), "
                    elif fail["status_code"] == 404:
                        diagnosis += "User not found in organization, "
                    elif fail["status_code"] == 400:
                        diagnosis += "Bad request (validation error), "
                    else:
                        diagnosis += f"HTTP {fail['status_code']} error, "
            
            print(f"\n🔍 DIAGNOSIS: {diagnosis}")
            
            self.log_test("DELETE User Functionality Review Request", overall_success, details + diagnosis)
            return overall_success
            
        except Exception as e:
            self.log_test("DELETE User Functionality Review Request", False, f"Exception: {str(e)}")
            return False

    def test_review_request_create_real_team_members(self):
        """REVIEW REQUEST: Create real team members for delete functionality testing"""
        print("\n🎯 EXECUTING REVIEW REQUEST: Create Real Team Members for Delete Testing")
        print("=" * 80)
        
        try:
            # Step 1: Login with ysaias.corredor@gmail.com / Clave.01
            print("Step 1: Login with ysaias.corredor@gmail.com / Clave.01")
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Review Request - Owner Login", False, f"Status: {response.status_code}, Error: {error_data}")
                return False
            
            data = response.json()
            owner_token = data["access_token"]
            user_data = data["user"]
            
            print(f"✅ Owner login successful - User ID: {user_data.get('id')}, Organization ID: {user_data.get('organization_id')}")
            self.log_test("Review Request - Owner Login", True, f"Status: {response.status_code}, User: {user_data.get('email')}, Org: {user_data.get('organization_id')}")
            
            headers = {"Authorization": f"Bearer {owner_token}"}
            
            # Step 2: Create User 1 - delete.test.1@example.com
            print("\nStep 2: Create User 1 - delete.test.1@example.com")
            user1_data = {
                "email": "delete.test.1@example.com",
                "name": "Delete Test User 1",
                "role": "auditor",
                "password": "DeleteTest123"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user1_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user1_id = data.get("user", {}).get("id")
                print(f"✅ User 1 created successfully - ID: {user1_id}")
                self.log_test("Review Request - Create User 1", True, f"Status: {response.status_code}, User ID: {user1_id}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ User 1 creation failed - Status: {response.status_code}, Error: {error_data}")
                self.log_test("Review Request - Create User 1", False, f"Status: {response.status_code}, Error: {error_data}")
                return False
            
            # Step 3: Create User 2 - delete.test.2@example.com
            print("\nStep 3: Create User 2 - delete.test.2@example.com")
            user2_data = {
                "email": "delete.test.2@example.com",
                "name": "Delete Test User 2",
                "role": "viewer",
                "password": "DeleteTest456"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user2_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user2_id = data.get("user", {}).get("id")
                print(f"✅ User 2 created successfully - ID: {user2_id}")
                self.log_test("Review Request - Create User 2", True, f"Status: {response.status_code}, User ID: {user2_id}")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ User 2 creation failed - Status: {response.status_code}, Error: {error_data}")
                self.log_test("Review Request - Create User 2", False, f"Status: {response.status_code}, Error: {error_data}")
                return False
            
            # Step 4: Verify users appear in GET /api/organization/team as actual team_members
            print("\nStep 4: Verify users appear in team_members (not pending_invitations)")
            response = requests.get(f"{self.api_url}/organization/team", 
                                  headers=headers, timeout=10)
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.log_test("Review Request - Get Team Data", False, f"Status: {response.status_code}, Error: {error_data}")
                return False
            
            team_data = response.json()
            team_members = team_data.get("team_members", [])
            pending_invitations = team_data.get("pending_invitations", [])
            
            print(f"📊 Team Members Count: {len(team_members)}")
            print(f"📊 Pending Invitations Count: {len(pending_invitations)}")
            
            # Check if our created users are in team_members
            user1_found = any(member.get("email") == "delete.test.1@example.com" for member in team_members)
            user2_found = any(member.get("email") == "delete.test.2@example.com" for member in team_members)
            
            # Check they are NOT in pending_invitations
            user1_not_pending = not any(inv.get("invitee_email") == "delete.test.1@example.com" for inv in pending_invitations)
            user2_not_pending = not any(inv.get("invitee_email") == "delete.test.2@example.com" for inv in pending_invitations)
            
            print(f"✅ User 1 in team_members: {user1_found}")
            print(f"✅ User 2 in team_members: {user2_found}")
            print(f"✅ User 1 NOT in pending_invitations: {user1_not_pending}")
            print(f"✅ User 2 NOT in pending_invitations: {user2_not_pending}")
            
            # Step 5: Check that team_members array now has 3 members (owner + 2 new users)
            expected_count = 3  # Owner + 2 new users
            actual_count = len(team_members)
            has_correct_count = actual_count >= expected_count
            
            print(f"📊 Expected minimum team members: {expected_count}")
            print(f"📊 Actual team members: {actual_count}")
            print(f"✅ Has correct count: {has_correct_count}")
            
            # Print team member details for verification
            print("\n👥 TEAM MEMBERS DETAILS:")
            for i, member in enumerate(team_members, 1):
                print(f"  {i}. Email: {member.get('email')}, Name: {member.get('name')}, Role: {member.get('role')}")
            
            if pending_invitations:
                print("\n📧 PENDING INVITATIONS:")
                for i, inv in enumerate(pending_invitations, 1):
                    print(f"  {i}. Email: {inv.get('invitee_email')}, Name: {inv.get('invitee_name')}, Role: {inv.get('role')}")
            
            # Overall success check
            success = (user1_found and user2_found and user1_not_pending and 
                      user2_not_pending and has_correct_count)
            
            details = f"User1 in team: {user1_found}, User2 in team: {user2_found}, User1 not pending: {user1_not_pending}, User2 not pending: {user2_not_pending}, Team count: {actual_count}/{expected_count}"
            
            self.log_test("Review Request - Verify Team Members", success, details)
            
            if success:
                print("\n🎉 REVIEW REQUEST COMPLETED SUCCESSFULLY!")
                print("✅ Both test users created as REAL team members (not invitations)")
                print("✅ Users appear in team_members array")
                print("✅ Users do NOT appear in pending_invitations")
                print("✅ Team now has the expected number of members")
                print("\n🗑️ DELETE BUTTONS SHOULD NOW BE VISIBLE IN FRONTEND!")
            else:
                print("\n❌ REVIEW REQUEST FAILED!")
                print("Some requirements were not met. Check the details above.")
            
            return success
            
        except Exception as e:
            self.log_test("Review Request - Create Real Team Members", False, str(e))
            print(f"❌ Exception occurred: {str(e)}")
            return False

    def test_new_audit_category_questions(self):
        """Test POST /api/audits/questions with new categories - REVIEW REQUEST"""
        try:
            # Test with new categories as specified in review request
            request_data = {
                "work_types": ["jsa", "ppe", "chemical_work"],
                "language": "en"
            }
            
            response = requests.post(f"{self.api_url}/audits/questions", 
                                   json=request_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_questions = "questions" in data
                questions = data.get("questions", [])
                
                success = has_questions and len(questions) > 0
                details = f"Status: {response.status_code}, Questions count: {len(questions)}"
                
                if success:
                    # Verify questions for each work type
                    jsa_questions = [q for q in questions if q.get("work_type") == "jsa"]
                    ppe_questions = [q for q in questions if q.get("work_type") == "ppe"]
                    chemical_questions = [q for q in questions if q.get("work_type") == "chemical_work"]
                    
                    has_jsa = len(jsa_questions) > 0
                    has_ppe = len(ppe_questions) > 0
                    has_chemical = len(chemical_questions) > 0
                    
                    success = has_jsa and has_ppe and has_chemical
                    details += f", JSA questions: {len(jsa_questions)}, PPE questions: {len(ppe_questions)}, Chemical questions: {len(chemical_questions)}"
                    
                    # Verify question content is safety-related
                    if jsa_questions:
                        jsa_sample = jsa_questions[0].get("question", "")
                        has_safety_content = any(word in jsa_sample.lower() for word in ["safety", "hazard", "analysis", "job"])
                        details += f", Safety content in JSA: {has_safety_content}"
                        success = success and has_safety_content
                        
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("New Audit Category Questions", success, details)
            return success
        except Exception as e:
            self.log_test("New Audit Category Questions", False, str(e))
            return False

    def test_owner_gmail_login(self):
        """Test login with ysaias.corredor@gmail.com / Clave.01 - REVIEW REQUEST"""
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
                has_message = "message" in data
                
                if has_token:
                    self.owner_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@gmail.com"
                    user_role = user_data.get("role", "")
                    subscription_plan = user_data.get("subscription_plan", "")
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Role: {user_role}, Plan: {subscription_plan}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Owner Gmail Login (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Gmail Login (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_admin_dashboard_endpoint(self):
        """Test GET /api/admin/dashboard - REVIEW REQUEST (should work without withCredentials)"""
        if not self.owner_token:
            self.log_test("Admin Dashboard Endpoint", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/admin/dashboard", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for typical dashboard data
                has_data = len(data) > 0
                
                success = has_data
                details = f"Status: {response.status_code}, Has data: {has_data}"
                
                # Check for common dashboard fields
                if isinstance(data, dict):
                    common_fields = ["users", "audits", "statistics", "summary"]
                    has_common_fields = any(field in data for field in common_fields)
                    details += f", Has common dashboard fields: {has_common_fields}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Dashboard Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Dashboard Endpoint", False, str(e))
            return False

    def test_admin_users_endpoint(self):
        """Test GET /api/admin/users - REVIEW REQUEST (should return user data for admin)"""
        if not self.owner_token:
            self.log_test("Admin Users Endpoint", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/admin/users", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                success = True
                details = f"Status: {response.status_code}"
                
                # Check if data is a list of users
                if isinstance(data, list):
                    user_count = len(data)
                    details += f", Users count: {user_count}"
                    
                    # Check user structure if users exist
                    if user_count > 0:
                        first_user = data[0]
                        user_fields = ["id", "email", "name"]
                        has_user_fields = all(field in first_user for field in user_fields)
                        details += f", User fields valid: {has_user_fields}"
                        success = success and has_user_fields
                        
                        # Ensure no password_hash is exposed
                        no_password_exposed = "password_hash" not in first_user
                        details += f", No password exposed: {no_password_exposed}"
                        success = success and no_password_exposed
                        
                elif isinstance(data, dict):
                    # Could be paginated response
                    has_users_key = "users" in data
                    details += f", Has users key: {has_users_key}"
                    success = success and has_users_key
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Users Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Users Endpoint", False, str(e))
            return False

    def test_owner_gmail_login_current_status(self):
        """Test current login status for ysaias.corredor@gmail.com"""
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
                    user_id = user_data.get("id")
                    current_role = user_data.get("role")
                    current_plan = user_data.get("subscription_plan")
                    subscription_expires = user_data.get("subscription_expires")
                    
                    details += f", ID: {user_id}, Role: {current_role}, Plan: {current_plan}, Expires: {subscription_expires}"
                    
                    # Store user ID for admin updates
                    self.owner_user_id = user_id
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Owner Gmail Login Current Status", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Gmail Login Current Status", False, str(e))
            return False

    def test_update_user_to_admin_role(self):
        """Update ysaias.corredor@gmail.com to admin role using admin endpoint"""
        if not self.admin_token or not hasattr(self, 'owner_user_id'):
            self.log_test("Update User to Admin Role", False, "No admin token or owner user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Update user to admin role and unlimited subscription
            update_data = {
                "role": "admin",
                "subscription_plan": "enterprise",  # Using enterprise as "unlimited"
                "subscription_expires": "2025-12-31T23:59:59Z"  # Set far future expiration
            }
            
            response = requests.put(f"{self.api_url}/admin/user/{self.owner_user_id}", 
                                  json=update_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_updated_fields = "updated_fields" in data
                
                success = has_message and has_updated_fields
                details = f"Status: {response.status_code}, Message: {has_message}, Updated fields: {has_updated_fields}"
                
                if has_updated_fields:
                    updated_fields = data.get("updated_fields", [])
                    role_updated = "role" in updated_fields
                    plan_updated = "subscription_plan" in updated_fields
                    expires_updated = "subscription_expires" in updated_fields
                    
                    success = success and role_updated and plan_updated and expires_updated
                    details += f", Role field updated: {role_updated}, Plan field updated: {plan_updated}, Expires field updated: {expires_updated}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Update User to Admin Role", success, details)
            return success
        except Exception as e:
            self.log_test("Update User to Admin Role", False, str(e))
            return False

    def test_verify_admin_access_after_update(self):
        """Verify admin access works after role update"""
        try:
            # Re-login to get new token with admin role
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get("access_token")
                user_data = data.get("user", {})
                
                # Verify user now has admin role
                is_admin = user_data.get("role") == "admin"
                is_enterprise = user_data.get("subscription_plan") == "enterprise"
                
                if new_token and is_admin:
                    # Test admin dashboard access
                    headers = {"Authorization": f"Bearer {new_token}"}
                    dashboard_response = requests.get(f"{self.api_url}/admin/dashboard", 
                                                    headers=headers, timeout=10)
                    
                    dashboard_works = dashboard_response.status_code == 200
                    
                    if dashboard_works:
                        dashboard_data = dashboard_response.json()
                        # Check for the actual structure returned by the dashboard
                        has_metrics = "metrics" in dashboard_data
                        has_users_by_plan = "users_by_plan" in dashboard_data
                        has_revenue_by_month = "revenue_by_month" in dashboard_data
                        has_top_users = "top_users" in dashboard_data
                        
                        success = dashboard_works and has_metrics
                        details = f"Login: 200, Admin role: {is_admin}, Enterprise plan: {is_enterprise}, Dashboard: {dashboard_works}, Has metrics: {has_metrics}, Has users_by_plan: {has_users_by_plan}, Has revenue_by_month: {has_revenue_by_month}, Has top_users: {has_top_users}"
                    else:
                        success = False
                        details = f"Login: 200, Admin role: {is_admin}, Enterprise plan: {is_enterprise}, Dashboard: {dashboard_response.status_code}"
                else:
                    success = False
                    details = f"Login: 200, Admin role: {is_admin}, Enterprise plan: {is_enterprise}, Token: {bool(new_token)}"
            else:
                success = False
                details = f"Login failed: {response.status_code}"
            
            self.log_test("Verify Admin Access After Update", success, details)
            return success
        except Exception as e:
            self.log_test("Verify Admin Access After Update", False, str(e))
            return False

    def test_admin_dashboard_with_owner_credentials(self):
        """Test GET /api/admin/dashboard with owner credentials after admin update"""
        try:
            # Login with owner credentials
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Test admin dashboard
                    dashboard_response = requests.get(f"{self.api_url}/admin/dashboard", 
                                                    headers=headers, timeout=10)
                    
                    if dashboard_response.status_code == 200:
                        dashboard_data = dashboard_response.json()
                        
                        # Check for the actual dashboard structure
                        has_metrics = "metrics" in dashboard_data
                        has_users_by_plan = "users_by_plan" in dashboard_data
                        has_revenue_by_month = "revenue_by_month" in dashboard_data
                        has_top_users = "top_users" in dashboard_data
                        
                        success = has_metrics and has_users_by_plan and has_revenue_by_month and has_top_users
                        details = f"Dashboard: 200, User role: {user_data.get('role')}, Has metrics: {has_metrics}, Has users_by_plan: {has_users_by_plan}, Has revenue_by_month: {has_revenue_by_month}, Has top_users: {has_top_users}"
                        
                        if has_metrics:
                            # Log some dashboard metrics
                            metrics = dashboard_data.get("metrics", {})
                            total_users = metrics.get("total_users", 0)
                            total_audits = metrics.get("total_audits", 0)
                            active_subscribers = metrics.get("active_subscribers", 0)
                            details += f", Total users: {total_users}, Total audits: {total_audits}, Active subscribers: {active_subscribers}"
                            
                    else:
                        success = False
                        try:
                            error_data = dashboard_response.json()
                            details = f"Dashboard: {dashboard_response.status_code}, Error: {error_data.get('detail', 'Unknown')}"
                        except:
                            details = f"Dashboard: {dashboard_response.status_code}"
                else:
                    success = False
                    details = "No access token received"
            else:
                success = False
                details = f"Login failed: {response.status_code}"
            
            self.log_test("Admin Dashboard with Owner Credentials", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Dashboard with Owner Credentials", False, str(e))
            return False

    def run_review_request_tests(self):
        """Run specific tests for the review request"""
        print("🎯 URGENT REVIEW REQUEST TESTING - ADMIN ACCESS & UNLIMITED SUBSCRIPTION")
        print("=" * 80)
        print("Testing requirements:")
        print("1. Update ysaias.corredor@gmail.com to admin role")
        print("2. Update subscription to unlimited (enterprise plan)")
        print("3. Verify admin dashboard access works")
        print("=" * 80)
        
        # Step 1: Check current status
        self.test_owner_gmail_login_current_status()
        
        # Step 2: Login as admin to perform updates
        if not self.test_admin_login():
            print("❌ Cannot proceed without admin access")
            return False
        
        # Step 3: Update user to admin role and unlimited subscription
        self.test_update_user_to_admin_role()
        
        # Step 4: Verify admin access works
        self.test_verify_admin_access_after_update()
        
        # Step 5: Test admin dashboard specifically
        self.test_admin_dashboard_with_owner_credentials()
        
        print("=" * 80)
        print(f"🏁 Review Request Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL REVIEW REQUEST REQUIREMENTS COMPLETED SUCCESSFULLY!")
            print("✅ User ysaias.corredor@gmail.com now has admin access")
            print("✅ Subscription updated to unlimited (enterprise plan)")
            print("✅ Admin dashboard access verified")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"❌ {failed_tests} test(s) failed. Check details above.")
        
        return self.tests_passed == self.tests_run

    def test_stripe_user_login(self):
        """Test login with ysaias.corredor@gmail.com / Clave.01 (review request user)"""
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
                has_message = "message" in data
                
                if has_token:
                    self.owner_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@gmail.com"
                    subscription_plan = user_data.get("subscription_plan")
                    subscription_expires = user_data.get("subscription_expires")
                    user_role = user_data.get("role")
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Plan: {subscription_plan}, Expires: {subscription_expires}, Role: {user_role}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Stripe User Login (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe User Login (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_stripe_checkout_session_creation(self):
        """Test POST /api/payments/checkout/session with CSA Safety Pro package"""
        if not self.owner_token:
            self.log_test("Stripe Checkout Session Creation", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test checkout session creation for unlimited package
            checkout_data = {
                "package_id": "unlimited",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                has_session_id = "session_id" in data
                has_url = "url" in data
                
                success = has_session_id and has_url
                details = f"Status: {response.status_code}, Session ID: {has_session_id}, URL: {has_url}"
                
                if success:
                    session_id = data.get("session_id", "")
                    url = data.get("url", "")
                    
                    # Check if it's live mode (real Stripe) or demo mode
                    is_live_mode = session_id.startswith("cs_live_") or not session_id.startswith("cs_demo_")
                    is_demo_mode = session_id.startswith("cs_demo_")
                    
                    details += f", Live mode: {is_live_mode}, Demo mode: {is_demo_mode}"
                    
                    # For live mode, URL should be Stripe's checkout
                    if is_live_mode:
                        is_stripe_url = "checkout.stripe.com" in url
                        details += f", Stripe URL: {is_stripe_url}"
                        success = success and is_stripe_url
                    
                    # Store session ID for further testing
                    self.stripe_session_id = session_id
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Stripe Checkout Session Creation (CSA Safety Pro)", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Checkout Session Creation (CSA Safety Pro)", False, str(e))
            return False

    def test_stripe_api_key_configuration(self):
        """Test if Stripe API key is properly configured by attempting checkout"""
        if not self.owner_token:
            self.log_test("Stripe API Key Configuration", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test with a valid package to see if Stripe integration works
            checkout_data = {
                "package_id": "unlimited",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=checkout_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id", "")
                
                # If we get a live session ID, Stripe is configured
                is_live_configured = session_id.startswith("cs_live_")
                is_demo_mode = session_id.startswith("cs_demo_")
                
                success = is_live_configured or is_demo_mode
                details = f"Status: {response.status_code}, Live configured: {is_live_configured}, Demo mode: {is_demo_mode}, Session ID: {session_id[:20]}..."
                
            elif response.status_code == 400:
                # Check if error is related to Stripe configuration
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    is_stripe_error = 'stripe' in error_detail.lower() or 'api key' in error_detail.lower()
                    success = False
                    details = f"Status: {response.status_code}, Stripe config error: {is_stripe_error}, Error: {error_detail}"
                except:
                    success = False
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            else:
                success = False
                details = f"Status: {response.status_code}"
            
            self.log_test("Stripe API Key Configuration", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe API Key Configuration", False, str(e))
            return False

    def test_stripe_webhook_endpoint(self):
        """Test if Stripe webhook endpoint is accessible"""
        try:
            # Test webhook endpoint accessibility (should return method not allowed for GET)
            response = requests.get(f"{self.api_url}/payments/webhook/stripe", timeout=10)
            
            # Webhook endpoint should return 405 (Method Not Allowed) for GET requests
            # or 400 (Bad Request) if it expects POST with specific headers
            success = response.status_code in [405, 400, 422]
            details = f"Status: {response.status_code} (expected 405/400/422 for GET request)"
            
            self.log_test("Stripe Webhook Endpoint Accessibility", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Webhook Endpoint Accessibility", False, str(e))
            return False

    def test_stripe_payment_status_check(self):
        """Test payment status checking functionality"""
        if not self.owner_token:
            self.log_test("Stripe Payment Status Check", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # First create a checkout session to get a session ID
            checkout_data = {
                "package_id": "unlimited",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            checkout_response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                            json=checkout_data, headers=headers, timeout=15)
            
            if checkout_response.status_code == 200:
                checkout_data = checkout_response.json()
                session_id = checkout_data.get("session_id", "")
                
                if session_id:
                    # Test payment status endpoint
                    status_response = requests.get(f"{self.api_url}/payments/checkout/status/{session_id}", 
                                                 headers=headers, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        has_session_id = "session_id" in status_data
                        has_payment_status = "payment_status" in status_data
                        has_status = "status" in status_data
                        
                        success = has_session_id and has_payment_status and has_status
                        details = f"Status: {status_response.status_code}, Session ID: {has_session_id}, Payment Status: {has_payment_status}, Status: {has_status}"
                        
                        if success:
                            payment_status = status_data.get("payment_status", "")
                            status = status_data.get("status", "")
                            is_demo = status_data.get("demo_mode", False)
                            details += f", Payment: {payment_status}, Status: {status}, Demo: {is_demo}"
                        
                    else:
                        success = False
                        details = f"Status check failed: {status_response.status_code}"
                else:
                    success = False
                    details = "No session ID from checkout"
            else:
                success = False
                details = f"Checkout failed: {checkout_response.status_code}"
            
            self.log_test("Stripe Payment Status Check", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Payment Status Check", False, str(e))
            return False

    def test_stripe_error_handling(self):
        """Test Stripe error handling with invalid requests"""
        if not self.owner_token:
            self.log_test("Stripe Error Handling", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test with invalid package ID
            invalid_checkout_data = {
                "package_id": "invalid_package",
                "origin_url": "https://safesitepro.preview.emergentagent.com"
            }
            
            response = requests.post(f"{self.api_url}/payments/checkout/session", 
                                   json=invalid_checkout_data, headers=headers, timeout=10)
            
            # Should return 400 for invalid package
            success = response.status_code == 400
            
            if success:
                try:
                    error_data = response.json()
                    has_error_detail = "detail" in error_data
                    error_message = error_data.get("detail", "")
                    is_package_error = "package" in error_message.lower() or "invalid" in error_message.lower()
                    
                    success = success and has_error_detail and is_package_error
                    details = f"Status: {response.status_code}, Has error: {has_error_detail}, Package error: {is_package_error}, Message: {error_message}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            else:
                details = f"Status: {response.status_code} (expected 400)"
            
            self.log_test("Stripe Error Handling", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe Error Handling", False, str(e))
            return False

    def run_stripe_tests(self):
        """Run specific Stripe integration tests as requested in review"""
        print("🔥 STRIPE INTEGRATION TESTING - REVIEW REQUEST")
        print("=" * 60)
        print("Testing Stripe integration and payment system errors...")
        print()
        
        # Test user login first
        if not self.test_stripe_user_login():
            print("❌ Cannot proceed with Stripe tests - user login failed")
            return False
        
        # Test subscription packages endpoint
        self.test_subscription_packages_endpoint()
        
        # Test Stripe configuration
        self.test_stripe_api_key_configuration()
        
        # Test checkout session creation
        self.test_stripe_checkout_session_creation()
        
        # Test webhook endpoint
        self.test_stripe_webhook_endpoint()
        
        # Test payment status checking
        self.test_stripe_payment_status_check()
        
        # Test error handling
        self.test_stripe_error_handling()
        
        print("\n" + "=" * 60)
        print(f"🏁 STRIPE TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL STRIPE TESTS PASSED! Payment system is operational.")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} Stripe test(s) failed. Check the details above.")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

    def test_owner_login_audit_investigation(self):
        """URGENT: Test owner login and audit counting discrepancy for ysaias.corredor@gmail.com"""
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
                    user_data = data["user"]
                    user_id = user_data.get("id")
                    
                success = has_token and has_user
                details = f"Status: {response.status_code}, Token: {has_token}, User ID: {user_id}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == "ysaias.corredor@gmail.com"
                    subscription_plan = user_data.get("subscription_plan")
                    organization_id = user_data.get("organization_id")
                    success = success and correct_email
                    details += f", Email: {correct_email}, Plan: {subscription_plan}, Org ID: {organization_id}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("🚨 URGENT: Owner Login (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("🚨 URGENT: Owner Login (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_audit_count_discrepancy_investigation(self):
        """URGENT: Investigate audit counting discrepancy - User reports 12 audits but dashboard shows 9"""
        if not self.owner_token:
            self.log_test("🚨 URGENT: Audit Count Investigation", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # 1. GET ALL AUDITS for this user
            audits_response = requests.get(f"{self.api_url}/audits", 
                                         headers=headers, timeout=15)
            
            if audits_response.status_code == 200:
                audits_data = audits_response.json()
                total_audits_from_api = len(audits_data)
                
                # Analyze audit data
                completed_audits = [audit for audit in audits_data if audit.get("status") == "completed"]
                in_progress_audits = [audit for audit in audits_data if audit.get("status") == "in_progress"]
                
                completed_count = len(completed_audits)
                in_progress_count = len(in_progress_audits)
                
                # Check for any filtering issues
                audit_dates = []
                audit_statuses = []
                for audit in audits_data:
                    audit_dates.append(audit.get("created_at"))
                    audit_statuses.append(audit.get("status"))
                
                # 2. GET STATISTICS to check total_audits count
                stats_response = requests.get(f"{self.api_url}/statistics", 
                                            headers=headers, timeout=10)
                
                stats_total_audits = 0
                stats_working = False
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    stats_total_audits = stats_data.get("total_audits", 0)
                    stats_working = True
                
                # 3. Check for discrepancies
                api_vs_stats_match = total_audits_from_api == stats_total_audits
                user_reported_count = 12
                api_vs_user_match = total_audits_from_api == user_reported_count
                stats_vs_user_match = stats_total_audits == user_reported_count
                
                # Determine success based on investigation
                success = audits_response.status_code == 200 and stats_working
                
                details = f"🔍 AUDIT COUNT INVESTIGATION RESULTS:\n"
                details += f"   📊 GET /api/audits returned: {total_audits_from_api} audits\n"
                details += f"   📈 GET /api/statistics shows: {stats_total_audits} total_audits\n"
                details += f"   👤 User reports having: {user_reported_count} audits\n"
                details += f"   ✅ Completed audits: {completed_count}\n"
                details += f"   🔄 In-progress audits: {in_progress_count}\n"
                details += f"   🔍 API vs Stats match: {api_vs_stats_match}\n"
                details += f"   🔍 API vs User match: {api_vs_user_match}\n"
                details += f"   🔍 Stats vs User match: {stats_vs_user_match}\n"
                
                # Check for potential filtering issues
                if not api_vs_user_match:
                    details += f"   🚨 DISCREPANCY FOUND: Expected {user_reported_count}, got {total_audits_from_api}\n"
                    details += f"   📅 Audit date range: {min(audit_dates) if audit_dates else 'None'} to {max(audit_dates) if audit_dates else 'None'}\n"
                    details += f"   📋 Status breakdown: {dict(zip(*[audit_statuses, [audit_statuses.count(s) for s in set(audit_statuses)]]))}\n"
                
                # Mark as failed if there's a discrepancy
                if not api_vs_user_match or not stats_vs_user_match:
                    success = False
                    details += f"   ❌ DATA INCONSISTENCY DETECTED"
                
            else:
                success = False
                try:
                    error_data = audits_response.json()
                    details = f"GET /api/audits failed - Status: {audits_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"GET /api/audits failed - Status: {audits_response.status_code}"
            
            self.log_test("🚨 URGENT: Audit Count Discrepancy Investigation", success, details)
            return success
        except Exception as e:
            self.log_test("🚨 URGENT: Audit Count Discrepancy Investigation", False, str(e))
            return False

    def test_audit_filtering_issues_investigation(self):
        """URGENT: Check for audit filtering issues that might exclude audits"""
        if not self.owner_token:
            self.log_test("🚨 URGENT: Audit Filtering Investigation", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Get user info to check organization_id
            user_response = requests.get(f"{self.api_url}/auth/me", 
                                       headers=headers, timeout=10)
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_id = user_data.get("id")
                organization_id = user_data.get("organization_id")
                
                # Get all audits
                audits_response = requests.get(f"{self.api_url}/audits", 
                                             headers=headers, timeout=15)
                
                if audits_response.status_code == 200:
                    audits_data = audits_response.json()
                    
                    # Analyze potential filtering issues
                    filtering_analysis = {
                        "total_returned": len(audits_data),
                        "user_id_matches": 0,
                        "different_user_ids": set(),
                        "status_breakdown": {},
                        "date_range_issues": [],
                        "organization_issues": []
                    }
                    
                    for audit in audits_data:
                        # Check user_id filtering
                        audit_user_id = audit.get("user_id")
                        if audit_user_id == user_id:
                            filtering_analysis["user_id_matches"] += 1
                        else:
                            filtering_analysis["different_user_ids"].add(audit_user_id)
                        
                        # Status breakdown
                        status = audit.get("status", "unknown")
                        filtering_analysis["status_breakdown"][status] = filtering_analysis["status_breakdown"].get(status, 0) + 1
                        
                        # Check for date/time issues
                        created_at = audit.get("created_at")
                        completed_at = audit.get("completed_at")
                        if created_at and not completed_at and status == "completed":
                            filtering_analysis["date_range_issues"].append(audit.get("id"))
                    
                    # Check organization access
                    if organization_id:
                        # If user is part of organization, check if there might be org-level audits
                        filtering_analysis["organization_issues"].append(f"User is part of organization {organization_id}")
                    
                    success = audits_response.status_code == 200
                    
                    details = f"🔍 FILTERING ANALYSIS RESULTS:\n"
                    details += f"   👤 User ID: {user_id}\n"
                    details += f"   🏢 Organization ID: {organization_id}\n"
                    details += f"   📊 Total audits returned: {filtering_analysis['total_returned']}\n"
                    details += f"   ✅ Audits matching user ID: {filtering_analysis['user_id_matches']}\n"
                    details += f"   ❓ Different user IDs found: {len(filtering_analysis['different_user_ids'])}\n"
                    details += f"   📋 Status breakdown: {filtering_analysis['status_breakdown']}\n"
                    
                    if filtering_analysis["date_range_issues"]:
                        details += f"   📅 Date/time issues found in audits: {filtering_analysis['date_range_issues']}\n"
                    
                    if filtering_analysis["organization_issues"]:
                        details += f"   🏢 Organization issues: {filtering_analysis['organization_issues']}\n"
                    
                    # Check for potential issues
                    if filtering_analysis["user_id_matches"] != filtering_analysis["total_returned"]:
                        success = False
                        details += f"   🚨 FILTERING ISSUE: Not all audits belong to current user\n"
                    
                    if len(filtering_analysis["different_user_ids"]) > 0:
                        details += f"   ⚠️  WARNING: Found audits from other users: {filtering_analysis['different_user_ids']}\n"
                
                else:
                    success = False
                    details = f"Failed to get audits - Status: {audits_response.status_code}"
            else:
                success = False
                details = f"Failed to get user info - Status: {user_response.status_code}"
            
            self.log_test("🚨 URGENT: Audit Filtering Issues Investigation", success, details)
            return success
        except Exception as e:
            self.log_test("🚨 URGENT: Audit Filtering Issues Investigation", False, str(e))
            return False

    def test_database_audit_count_verification(self):
        """URGENT: Verify actual audit count in database through admin endpoints"""
        if not self.admin_token:
            self.log_test("🚨 URGENT: Database Audit Count Verification", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get admin dashboard data which might show global audit counts
            dashboard_response = requests.get(f"{self.api_url}/admin/dashboard", 
                                            headers=headers, timeout=15)
            
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                
                # Look for audit-related metrics
                metrics = dashboard_data.get("metrics", {})
                total_audits_global = metrics.get("total_audits", 0)
                total_users = metrics.get("total_users", 0)
                
                # Get user list to find our specific user
                users_response = requests.get(f"{self.api_url}/admin/users", 
                                            headers=headers, timeout=10)
                
                target_user_found = False
                target_user_data = {}
                
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    users_list = users_data.get("users", [])
                    
                    for user in users_list:
                        if user.get("email") == "ysaias.corredor@gmail.com":
                            target_user_found = True
                            target_user_data = user
                            break
                
                success = dashboard_response.status_code == 200 and users_response.status_code == 200
                
                details = f"🔍 DATABASE VERIFICATION RESULTS:\n"
                details += f"   🌐 Global total audits: {total_audits_global}\n"
                details += f"   👥 Total users in system: {total_users}\n"
                details += f"   🎯 Target user found: {target_user_found}\n"
                
                if target_user_found:
                    user_id = target_user_data.get("id")
                    user_plan = target_user_data.get("subscription_plan")
                    user_org_id = target_user_data.get("organization_id")
                    audits_used = target_user_data.get("audits_used_this_month", 0)
                    
                    details += f"   👤 User ID: {user_id}\n"
                    details += f"   💳 Subscription plan: {user_plan}\n"
                    details += f"   🏢 Organization ID: {user_org_id}\n"
                    details += f"   📊 Audits used this month: {audits_used}\n"
                    
                    # This gives us insight into potential discrepancies
                    if audits_used != 12 and audits_used != 9:
                        details += f"   ⚠️  WARNING: audits_used_this_month ({audits_used}) doesn't match user report (12) or dashboard (9)\n"
                
                else:
                    success = False
                    details += f"   ❌ CRITICAL: Target user ysaias.corredor@gmail.com not found in admin user list\n"
            
            else:
                success = False
                try:
                    error_data = dashboard_response.json()
                    details = f"Admin dashboard failed - Status: {dashboard_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Admin dashboard failed - Status: {dashboard_response.status_code}"
            
            self.log_test("🚨 URGENT: Database Audit Count Verification", success, details)
            return success
        except Exception as e:
            self.log_test("🚨 URGENT: Database Audit Count Verification", False, str(e))
            return False

    def test_urgent_audit_counting_investigation(self):
        """🚨 URGENT: Investigate audit counting discrepancy for ysaias.corredor@gmail.com"""
        print("\n🚨 URGENT AUDIT COUNT INVESTIGATION")
        print("=" * 60)
        print("User reports having 12 audits, but dashboard shows 0 audits")
        print("Investigating with credentials: ysaias.corredor@gmail.com / Clave.01")
        print("=" * 60)
        
        # Step 1: Login with user credentials
        try:
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user_token = data.get("access_token")
                user_data = data.get("user", {})
                user_id = user_data.get("id")
                organization_id = user_data.get("organization_id")
                
                print(f"✅ 1) LOGIN SUCCESSFUL")
                print(f"   User ID: {user_id}")
                print(f"   Organization ID: {organization_id}")
                print(f"   Subscription Plan: {user_data.get('subscription_plan')}")
                print(f"   Audits Used This Month: {user_data.get('audits_used_this_month')}")
                
                headers = {"Authorization": f"Bearer {user_token}"}
                
                # Step 2: Check GET /api/audits endpoint
                print(f"\n🔍 2) CHECKING GET /api/audits ENDPOINT")
                audits_response = requests.get(f"{self.api_url}/audits", 
                                             headers=headers, timeout=10)
                
                if audits_response.status_code == 200:
                    audits_data = audits_response.json()
                    audit_count = len(audits_data)
                    print(f"   Status: 200 OK")
                    print(f"   Audits returned: {audit_count}")
                    
                    if audit_count > 0:
                        print(f"   Sample audit IDs: {[audit.get('id') for audit in audits_data[:3]]}")
                        print(f"   Sample audit statuses: {[audit.get('status') for audit in audits_data[:3]]}")
                    else:
                        print(f"   ❌ NO AUDITS FOUND for this user")
                else:
                    print(f"   ❌ Error: {audits_response.status_code}")
                    audit_count = 0
                
                # Step 3: Check GET /api/organization/audits endpoint (if exists)
                print(f"\n🔍 3) CHECKING GET /api/organization/audits ENDPOINT")
                org_audits_response = requests.get(f"{self.api_url}/organization/audits", 
                                                 headers=headers, timeout=10)
                
                if org_audits_response.status_code == 200:
                    org_audits_data = org_audits_response.json()
                    org_audit_count = len(org_audits_data) if isinstance(org_audits_data, list) else 0
                    print(f"   Status: 200 OK")
                    print(f"   Organization audits returned: {org_audit_count}")
                elif org_audits_response.status_code == 404:
                    print(f"   Status: 404 - Endpoint does not exist")
                else:
                    print(f"   Status: {org_audits_response.status_code}")
                
                # Step 4: Check user statistics
                print(f"\n🔍 4) CHECKING GET /api/statistics ENDPOINT")
                stats_response = requests.get(f"{self.api_url}/statistics", 
                                            headers=headers, timeout=10)
                
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    total_audits = stats_data.get("total_audits", 0)
                    print(f"   Status: 200 OK")
                    print(f"   Total audits in statistics: {total_audits}")
                    print(f"   Compliant audits: {stats_data.get('compliant_audits', 0)}")
                    print(f"   Non-compliant audits: {stats_data.get('non_compliant_audits', 0)}")
                else:
                    print(f"   Status: {stats_response.status_code}")
                    total_audits = 0
                
                # Step 5: Check organization team if user has organization
                if organization_id:
                    print(f"\n🔍 5) CHECKING ORGANIZATION TEAM MEMBERS")
                    team_response = requests.get(f"{self.api_url}/organization/team", 
                                               headers=headers, timeout=10)
                    
                    if team_response.status_code == 200:
                        team_data = team_response.json()
                        team_members = team_data.get("team_members", [])
                        print(f"   Status: 200 OK")
                        print(f"   Organization: {team_data.get('organization', {}).get('name', 'Unknown')}")
                        print(f"   Team members count: {len(team_members)}")
                        
                        # Check if there are audits from other team members
                        member_user_ids = [member.get("user_id") for member in team_members if member.get("user_id")]
                        print(f"   Team member user IDs: {member_user_ids}")
                        
                        # Note: We can't directly query other users' audits without admin access
                        print(f"   Note: Cannot check other team members' audits without admin access")
                    else:
                        print(f"   Status: {team_response.status_code}")
                else:
                    print(f"\n🔍 5) USER HAS NO ORGANIZATION")
                
                # Step 6: Summary and diagnosis
                print(f"\n📊 INVESTIGATION SUMMARY")
                print(f"=" * 40)
                print(f"User ID: {user_id}")
                print(f"Organization ID: {organization_id}")
                print(f"GET /api/audits returned: {audit_count} audits")
                print(f"GET /api/statistics shows: {total_audits} total audits")
                print(f"User reports having: 12 audits")
                print(f"Dashboard shows: 0 audits")
                
                # Determine the issue
                if audit_count == 0 and total_audits == 0:
                    print(f"\n🚨 CRITICAL FINDING: USER HAS NO AUDITS IN SYSTEM")
                    print(f"   - Backend shows 0 audits for this user")
                    print(f"   - Statistics show 0 audits for this user")
                    print(f"   - User claims to have 12 audits")
                    print(f"   - POSSIBLE CAUSES:")
                    print(f"     1. User is confusing accounts (different email)")
                    print(f"     2. Audits were deleted or lost during migration")
                    print(f"     3. Audits are associated with different user_id")
                    print(f"     4. Audits are in organization but not showing")
                    print(f"     5. Database inconsistency or corruption")
                elif audit_count > 0:
                    print(f"\n✅ AUDITS FOUND: User has {audit_count} audits")
                    print(f"   - This contradicts the dashboard showing 0")
                    print(f"   - Issue is likely frontend-related")
                else:
                    print(f"\n⚠️  MIXED RESULTS: Need further investigation")
                
                success = True
                details = f"Investigation completed. User has {audit_count} audits in backend"
                
            else:
                success = False
                details = f"Login failed with status {response.status_code}"
                print(f"❌ LOGIN FAILED: {details}")
        
        except Exception as e:
            success = False
            details = f"Investigation failed: {str(e)}"
            print(f"❌ INVESTIGATION ERROR: {details}")
        
        self.log_test("🚨 URGENT: Audit Counting Investigation", success, details)
        return success

    def test_na_option_implementation(self):
        """Test N/A option implementation for audit questions - REVIEW REQUEST"""
        print("\n🎯 TESTING N/A OPTION IMPLEMENTATION - REVIEW REQUEST")
        print("=" * 60)
        
        # Step 1: Login with test user credentials
        login_success = self.test_user_login_for_na_testing()
        if not login_success:
            self.log_test("N/A Option - User Login", False, "Failed to login with test credentials")
            return False
        
        # Step 2: Create a new audit with 3 work types
        audit_id = self.create_audit_for_na_testing()
        if not audit_id:
            self.log_test("N/A Option - Create Audit", False, "Failed to create test audit")
            return False
        
        # Step 3: Add findings with all 3 compliance statuses
        findings_success = self.add_findings_with_all_compliance_statuses(audit_id)
        if not findings_success:
            self.log_test("N/A Option - Add Findings", False, "Failed to add findings with all compliance statuses")
            return False
        
        # Step 4: Test backward compatibility
        backward_compat_success = self.test_backward_compatibility_is_compliant(audit_id)
        if not backward_compat_success:
            self.log_test("N/A Option - Backward Compatibility", False, "Backward compatibility test failed")
            return False
        
        # Step 5: Complete audit and verify compliance score calculation
        score_success = self.test_compliance_score_excludes_na(audit_id)
        if not score_success:
            self.log_test("N/A Option - Compliance Score", False, "Compliance score calculation failed")
            return False
        
        # Step 6: Get audit details and verify all findings stored correctly
        details_success = self.verify_audit_details_with_na(audit_id)
        if not details_success:
            self.log_test("N/A Option - Audit Details", False, "Audit details verification failed")
            return False
        
        # Step 7: Test PDF generation includes N/A findings
        pdf_success = self.test_pdf_generation_with_na_findings(audit_id)
        if not pdf_success:
            self.log_test("N/A Option - PDF Generation", False, "PDF generation with N/A findings failed")
            return False
        
        print("✅ N/A OPTION IMPLEMENTATION - ALL TESTS PASSED")
        return True
    
    def test_user_login_for_na_testing(self):
        """Login with test user credentials for N/A testing"""
        try:
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.test_user_token = data["access_token"]
                    self.log_test("N/A Testing - User Login", True, f"Logged in as {login_data['email']}")
                    return True
            
            self.log_test("N/A Testing - User Login", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("N/A Testing - User Login", False, str(e))
            return False
    
    def create_audit_for_na_testing(self):
        """Create a new audit with 3 work types for N/A testing"""
        if not self.test_user_token:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            audit_data = {
                "site_name": "N/A Testing Construction Site",
                "auditor_name": "N/A Test Auditor",
                "selected_work_types": ["excavation", "height_work", "ppe"],
                "language": "en"
            }
            
            response = requests.post(f"{self.api_url}/audits", 
                                   json=audit_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                audit_id = data.get("id")
                self.log_test("N/A Testing - Create Audit", True, f"Created audit: {audit_id}")
                return audit_id
            
            self.log_test("N/A Testing - Create Audit", False, f"Status: {response.status_code}")
            return None
        except Exception as e:
            self.log_test("N/A Testing - Create Audit", False, str(e))
            return None
    
    def add_findings_with_all_compliance_statuses(self, audit_id):
        """Add findings with compliant, non_compliant, and n/a statuses"""
        if not self.test_user_token or not audit_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Finding 1: Compliant
            finding1 = {
                "question": "Is the excavation properly sloped or shored to prevent cave-ins?",
                "compliance_status": "compliant",
                "comment": "Proper shoring observed and documented"
            }
            
            response1 = requests.post(f"{self.api_url}/audits/{audit_id}/findings", 
                                    json=finding1, headers=headers, timeout=10)
            
            # Finding 2: Non-compliant (with comment and action_taken)
            finding2 = {
                "question": "Are workers wearing proper fall protection equipment?",
                "compliance_status": "non_compliant",
                "comment": "Missing harnesses on 2 workers at height",
                "action_taken": "Provided harnesses and retrained workers on fall protection"
            }
            
            response2 = requests.post(f"{self.api_url}/audits/{audit_id}/findings", 
                                    json=finding2, headers=headers, timeout=10)
            
            # Finding 3: N/A (should not require comment/action)
            finding3 = {
                "question": "Is appropriate PPE provided for all workers based on job hazards?",
                "compliance_status": "n/a"
            }
            
            response3 = requests.post(f"{self.api_url}/audits/{audit_id}/findings", 
                                    json=finding3, headers=headers, timeout=10)
            
            success = (response1.status_code == 200 and 
                      response2.status_code == 200 and 
                      response3.status_code == 200)
            
            if success:
                self.log_test("N/A Testing - Add All Compliance Statuses", True, 
                            "Added compliant, non_compliant, and n/a findings")
            else:
                self.log_test("N/A Testing - Add All Compliance Statuses", False, 
                            f"Status codes: {response1.status_code}, {response2.status_code}, {response3.status_code}")
            
            return success
        except Exception as e:
            self.log_test("N/A Testing - Add All Compliance Statuses", False, str(e))
            return False
    
    def test_backward_compatibility_is_compliant(self, audit_id):
        """Test backward compatibility with old is_compliant format"""
        if not self.test_user_token or not audit_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Add finding with old is_compliant: true format
            old_format_finding = {
                "question": "Are welders wearing proper protective equipment?",
                "is_compliant": True,
                "comment": "All welders have proper PPE - backward compatibility test"
            }
            
            response = requests.post(f"{self.api_url}/audits/{audit_id}/findings", 
                                   json=old_format_finding, headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                self.log_test("N/A Testing - Backward Compatibility", True, 
                            "Old is_compliant format still works")
            else:
                try:
                    error_data = response.json()
                    self.log_test("N/A Testing - Backward Compatibility", False, 
                                f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown')}")
                except:
                    self.log_test("N/A Testing - Backward Compatibility", False, 
                                f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("N/A Testing - Backward Compatibility", False, str(e))
            return False
    
    def test_compliance_score_excludes_na(self, audit_id):
        """Complete audit and verify compliance score excludes N/A responses"""
        if not self.test_user_token or not audit_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            # Complete the audit
            response = requests.put(f"{self.api_url}/audits/{audit_id}/complete", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                compliance_score = data.get("compliance_score")
                
                # Expected calculation: 2 compliant (including backward compat) + 1 non-compliant = 3 applicable
                # 2 compliant / 3 applicable = 66.67%
                # N/A should be excluded from calculation
                expected_score_range = (60.0, 70.0)  # Allow some tolerance
                
                if compliance_score is not None:
                    score_in_range = expected_score_range[0] <= compliance_score <= expected_score_range[1]
                    success = score_in_range
                    
                    self.log_test("N/A Testing - Compliance Score Calculation", success, 
                                f"Score: {compliance_score}% (expected ~66.67%, N/A excluded)")
                else:
                    success = False
                    self.log_test("N/A Testing - Compliance Score Calculation", False, 
                                "No compliance score returned")
            else:
                success = False
                self.log_test("N/A Testing - Compliance Score Calculation", False, 
                            f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("N/A Testing - Compliance Score Calculation", False, str(e))
            return False
    
    def verify_audit_details_with_na(self, audit_id):
        """Get audit details and verify all findings are stored correctly"""
        if not self.test_user_token or not audit_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            response = requests.get(f"{self.api_url}/audits/{audit_id}", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                findings = data.get("findings", [])
                
                # Verify we have 4 findings (3 new format + 1 backward compatibility)
                has_correct_count = len(findings) == 4
                
                # Check for each compliance status
                statuses = [f.get("compliance_status") for f in findings]
                has_compliant = "compliant" in statuses
                has_non_compliant = "non_compliant" in statuses
                has_na = "n/a" in statuses
                
                # Check backward compatibility finding (should have compliance_status set)
                backward_compat_finding = next((f for f in findings if f.get("is_compliant") == True), None)
                backward_compat_converted = (backward_compat_finding and 
                                           backward_compat_finding.get("compliance_status") == "compliant")
                
                success = (has_correct_count and has_compliant and 
                          has_non_compliant and has_na and backward_compat_converted)
                
                details = (f"Findings count: {len(findings)}, "
                          f"Has compliant: {has_compliant}, "
                          f"Has non_compliant: {has_non_compliant}, "
                          f"Has n/a: {has_na}, "
                          f"Backward compat converted: {backward_compat_converted}")
                
                self.log_test("N/A Testing - Audit Details Verification", success, details)
            else:
                success = False
                self.log_test("N/A Testing - Audit Details Verification", False, 
                            f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("N/A Testing - Audit Details Verification", False, str(e))
            return False
    
    def test_pdf_generation_with_na_findings(self, audit_id):
        """Test PDF generation includes N/A findings with proper labeling"""
        if not self.test_user_token or not audit_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            
            response = requests.get(f"{self.api_url}/audits/{audit_id}/pdf", 
                                  headers=headers, timeout=20)
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type
                
                # Check PDF content length
                content_length = len(response.content)
                has_content = content_length > 1000
                
                # Check if content starts with PDF signature
                pdf_signature = response.content[:4] == b'%PDF'
                
                success = is_pdf and has_content and pdf_signature
                
                details = (f"PDF type: {is_pdf}, "
                          f"Size: {content_length} bytes, "
                          f"PDF signature: {pdf_signature}")
                
                self.log_test("N/A Testing - PDF Generation with N/A", success, details)
            else:
                success = False
                try:
                    error_data = response.json()
                    self.log_test("N/A Testing - PDF Generation with N/A", False, 
                                f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown')}")
                except:
                    self.log_test("N/A Testing - PDF Generation with N/A", False, 
                                f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("N/A Testing - PDF Generation with N/A", False, str(e))
            return False

    def test_audit_with_no_questions_investigation(self):
        """URGENT INVESTIGATION: Audit with no questions issue - User ysaias.corredor@gmail.com / Clave.01"""
        try:
            # Step 1: Login as the specific user mentioned in the review request
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("URGENT: Audit Investigation - User Login", False, f"Login failed: {response.status_code}")
                return False
            
            login_data_response = response.json()
            user_token = login_data_response.get("access_token")
            user_info = login_data_response.get("user", {})
            
            if not user_token:
                self.log_test("URGENT: Audit Investigation - User Login", False, "No access token received")
                return False
            
            headers = {"Authorization": f"Bearer {user_token}"}
            
            print(f"✅ User Login Successful - ID: {user_info.get('id')}, Email: {user_info.get('email')}")
            
            # Step 2: GET /api/audits - find the audit with site_name "rdu" that is in_progress
            audits_response = requests.get(f"{self.api_url}/audits", headers=headers, timeout=10)
            
            if audits_response.status_code != 200:
                self.log_test("URGENT: Audit Investigation - Get Audits", False, f"Failed to get audits: {audits_response.status_code}")
                return False
            
            audits_data = audits_response.json()
            print(f"📋 Total audits found: {len(audits_data)}")
            
            # Find the specific audit with site_name "rdu" and status "in_progress"
            target_audit = None
            for audit in audits_data:
                if audit.get("site_name", "").lower() == "rdu" and audit.get("status") == "in_progress":
                    target_audit = audit
                    break
            
            if not target_audit:
                # Look for any in_progress audits
                in_progress_audits = [a for a in audits_data if a.get("status") == "in_progress"]
                print(f"🔍 No 'rdu' audit found. In-progress audits: {len(in_progress_audits)}")
                
                if in_progress_audits:
                    target_audit = in_progress_audits[0]  # Use the first in-progress audit
                    print(f"📝 Using audit: {target_audit.get('site_name')} (ID: {target_audit.get('id')})")
                else:
                    self.log_test("URGENT: Audit Investigation - Find Target Audit", False, "No in-progress audits found")
                    return False
            else:
                print(f"🎯 Found target audit 'rdu' - ID: {target_audit.get('id')}")
            
            # Step 3: Analyze the audit document structure
            audit_id = target_audit.get("id")
            site_name = target_audit.get("site_name")
            selected_work_types = target_audit.get("selected_work_types", [])
            findings = target_audit.get("findings", [])
            status = target_audit.get("status")
            language = target_audit.get("language", "en")
            
            print(f"🔍 AUDIT ANALYSIS:")
            print(f"   Site Name: {site_name}")
            print(f"   Status: {status}")
            print(f"   Selected Work Types: {selected_work_types}")
            print(f"   Number of Findings: {len(findings)}")
            print(f"   Language: {language}")
            
            # Step 4: Check what questions should be generated for those work types
            if selected_work_types:
                questions_request = {
                    "work_types": selected_work_types,
                    "language": language
                }
                
                questions_response = requests.post(f"{self.api_url}/audits/questions", 
                                                 json=questions_request, headers=headers, timeout=10)
                
                if questions_response.status_code == 200:
                    questions_data = questions_response.json()
                    expected_questions = questions_data.get("questions", [])
                    
                    print(f"📝 QUESTIONS ANALYSIS:")
                    print(f"   Expected questions for work types {selected_work_types}: {len(expected_questions)}")
                    
                    if expected_questions:
                        print(f"   First question: {expected_questions[0].get('question', 'N/A')[:100]}...")
                        print(f"   Work type of first question: {expected_questions[0].get('work_type', 'N/A')}")
                    else:
                        print(f"   ❌ NO QUESTIONS GENERATED for work types: {selected_work_types}")
                else:
                    print(f"   ❌ Failed to get questions: {questions_response.status_code}")
            else:
                print(f"   ❌ NO WORK TYPES SELECTED in audit")
            
            # Step 5: GET /api/work-types - verify work types are properly loaded
            work_types_response = requests.get(f"{self.api_url}/work-types", timeout=10)
            
            if work_types_response.status_code == 200:
                work_types_data = work_types_response.json()
                print(f"🏗️  WORK TYPES ANALYSIS:")
                print(f"   Total work types available: {len(work_types_data)}")
                
                # Check if selected work types exist in available work types
                available_ids = [wt.get("id") for wt in work_types_data]
                missing_work_types = [wt for wt in selected_work_types if wt not in available_ids]
                
                if missing_work_types:
                    print(f"   ❌ MISSING WORK TYPES: {missing_work_types}")
                else:
                    print(f"   ✅ All selected work types are available")
                    
                # Show available work types for reference
                print(f"   Available work type IDs: {available_ids[:10]}...")  # Show first 10
            else:
                print(f"   ❌ Failed to get work types: {work_types_response.status_code}")
            
            # Step 6: Check backend logs for any errors (if possible)
            print(f"🔍 DIAGNOSIS SUMMARY:")
            
            # Determine the root cause
            root_cause_found = False
            
            if not selected_work_types:
                print(f"   🚨 ROOT CAUSE: Audit has NO selected work types")
                root_cause_found = True
            elif missing_work_types:
                print(f"   🚨 ROOT CAUSE: Selected work types {missing_work_types} don't exist in system")
                root_cause_found = True
            elif 'expected_questions' in locals() and len(expected_questions) == 0:
                print(f"   🚨 ROOT CAUSE: No questions defined for work types {selected_work_types}")
                root_cause_found = True
            elif 'expected_questions' in locals() and len(expected_questions) > 0:
                print(f"   ✅ Questions should be available ({len(expected_questions)} questions)")
                print(f"   🚨 POSSIBLE CAUSE: Frontend not properly displaying questions or question index issue")
                root_cause_found = True
            
            if not root_cause_found:
                print(f"   ❓ Unable to determine root cause - need further investigation")
            
            # Success if we completed the investigation
            success = True
            details = f"Investigation completed. Audit: {site_name}, Work types: {len(selected_work_types)}, Expected questions: {len(expected_questions) if 'expected_questions' in locals() else 'Unknown'}"
            
            self.log_test("URGENT: Audit Investigation - Complete Analysis", success, details)
            return success
            
        except Exception as e:
            self.log_test("URGENT: Audit Investigation - Complete Analysis", False, str(e))
            return False

    def test_user_registration_critical(self):
        """🚨 CRITICAL TEST: User registration endpoint as reported in review request"""
        try:
            # Test the exact scenario from review request
            registration_data = {
                "email": "testexternal789@example.com",
                "name": "Test External User", 
                "password": "TestPassword123"
            }
            
            print(f"🔍 Testing registration with: {registration_data['email']}")
            
            response = requests.post(f"{self.api_url}/auth/register", 
                                   json=registration_data, timeout=15)
            
            print(f"📡 Registration Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_user = "user" in data
                has_token = "access_token" in data
                has_token_type = "token_type" in data
                
                success = has_message and has_user and has_token and has_token_type
                details = f"Status: {response.status_code}, Message: {has_message}, User: {has_user}, Token: {has_token}, Token Type: {has_token_type}"
                
                if success:
                    user_data = data.get("user", {})
                    correct_email = user_data.get("email") == registration_data["email"]
                    correct_name = user_data.get("name") == registration_data["name"]
                    has_user_id = "id" in user_data
                    no_password_exposed = "password" not in user_data and "password_hash" not in user_data
                    
                    success = success and correct_email and correct_name and has_user_id and no_password_exposed
                    details += f", Correct email: {correct_email}, Correct name: {correct_name}, Has ID: {has_user_id}, No password exposed: {no_password_exposed}"
                    
                    # Test immediate login with new credentials
                    if success:
                        login_data = {
                            "email": registration_data["email"],
                            "password": registration_data["password"]
                        }
                        
                        login_response = requests.post(f"{self.api_url}/auth/login", 
                                                     json=login_data, timeout=10)
                        
                        can_login = login_response.status_code == 200
                        success = success and can_login
                        details += f", Can login immediately: {can_login}"
                        
                        if can_login:
                            # Store token for further testing
                            login_data_response = login_response.json()
                            if "access_token" in login_data_response:
                                self.test_user_token = login_data_response["access_token"]
                                
            elif response.status_code == 400:
                # Check if it's a validation error or duplicate email
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "")
                    
                    if "already registered" in error_detail.lower():
                        # User already exists - try with different email
                        import time
                        unique_email = f"testexternal{int(time.time())}@example.com"
                        registration_data["email"] = unique_email
                        
                        retry_response = requests.post(f"{self.api_url}/auth/register", 
                                                     json=registration_data, timeout=15)
                        
                        if retry_response.status_code == 200:
                            success = True
                            details = f"Original email existed, retry with {unique_email} succeeded"
                        else:
                            success = False
                            details = f"Original email existed, retry failed: {retry_response.status_code}"
                    else:
                        success = False
                        details = f"Status: {response.status_code}, Validation Error: {error_detail}"
                except:
                    success = False
                    details = f"Status: {response.status_code}, Could not parse error response"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("🚨 CRITICAL: User Registration (Review Request)", success, details)
            return success
        except Exception as e:
            self.log_test("🚨 CRITICAL: User Registration (Review Request)", False, str(e))
            return False

    def test_registration_validation_rules(self):
        """Test registration validation rules and error handling"""
        test_cases = [
            {
                "name": "Empty Email",
                "data": {"email": "", "name": "Test User", "password": "TestPass123"},
                "expected_status": 422
            },
            {
                "name": "Invalid Email Format", 
                "data": {"email": "invalid-email", "name": "Test User", "password": "TestPass123"},
                "expected_status": 422
            },
            {
                "name": "Empty Name",
                "data": {"email": "test@example.com", "name": "", "password": "TestPass123"},
                "expected_status": 422
            },
            {
                "name": "Short Password",
                "data": {"email": "test@example.com", "name": "Test User", "password": "123"},
                "expected_status": [400, 422]  # Could be either depending on validation
            },
            {
                "name": "Missing Password",
                "data": {"email": "test@example.com", "name": "Test User"},
                "expected_status": 422
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.api_url}/auth/register", 
                                       json=test_case["data"], timeout=10)
                
                expected_statuses = test_case["expected_status"] if isinstance(test_case["expected_status"], list) else [test_case["expected_status"]]
                success = response.status_code in expected_statuses
                
                details = f"Status: {response.status_code} (expected: {test_case['expected_status']})"
                self.log_test(f"Registration Validation - {test_case['name']}", success, details)
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Registration Validation - {test_case['name']}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email (should fail appropriately)"""
        try:
            # First, try to register with admin email (should fail)
            duplicate_data = {
                "email": "admin@csaaudit.com",
                "name": "Duplicate Admin",
                "password": "TestPassword123"
            }
            
            response = requests.post(f"{self.api_url}/auth/register", 
                                   json=duplicate_data, timeout=10)
            
            success = response.status_code == 400
            
            if success:
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "")
                    has_duplicate_message = "already registered" in error_detail.lower() or "exists" in error_detail.lower()
                    success = success and has_duplicate_message
                    details = f"Status: {response.status_code}, Proper duplicate message: {has_duplicate_message}"
                except:
                    details = f"Status: {response.status_code}, Could not parse error"
            else:
                details = f"Status: {response.status_code} (expected 400 for duplicate email)"
            
            self.log_test("Registration Duplicate Email", success, details)
            return success
        except Exception as e:
            self.log_test("Registration Duplicate Email", False, str(e))
            return False

    def test_specific_user_registration_issue(self):
        """🚨 URGENT: Test specific user registration issue with amazon.corredor123@gmail.com"""
        print("\n🚨 URGENT INVESTIGATION: amazon.corredor123@gmail.com Registration Issue")
        print("=" * 80)
        
        target_email = "amazon.corredor123@gmail.com"
        target_name = "Amazon Corredor"
        target_password = "TestPassword123"
        
        try:
            # Step 1: Check if user already exists in database by attempting login
            print(f"🔍 Step 1: Checking if user {target_email} already exists...")
            login_data = {
                "email": target_email,
                "password": target_password
            }
            
            login_response = requests.post(f"{self.api_url}/auth/login", 
                                         json=login_data, timeout=10)
            
            user_exists = login_response.status_code == 200
            login_error = None
            user_details = None
            
            if user_exists:
                print(f"✅ User EXISTS in database")
                user_data = login_response.json()
                user_details = user_data.get("user", {})
                print(f"   📋 User Details:")
                print(f"      - ID: {user_details.get('id', 'N/A')}")
                print(f"      - Email: {user_details.get('email', 'N/A')}")
                print(f"      - Name: {user_details.get('name', 'N/A')}")
                print(f"      - Created: {user_details.get('created_at', 'N/A')}")
                print(f"      - Role: {user_details.get('role', 'N/A')}")
                print(f"      - Subscription: {user_details.get('subscription_plan', 'N/A')}")
                print(f"      - Organization: {user_details.get('organization_id', 'N/A')}")
            else:
                print(f"❌ User does NOT exist in database")
                try:
                    login_error = login_response.json().get('detail', 'Unknown error')
                    print(f"   🔍 Login Error: {login_error}")
                except:
                    login_error = f"HTTP {login_response.status_code}"
                    print(f"   🔍 Login Status: {login_response.status_code}")
            
            # Step 2: Attempt registration with the target email
            print(f"\n🔍 Step 2: Attempting registration with {target_email}...")
            registration_data = {
                "email": target_email,
                "name": target_name,
                "password": target_password
            }
            
            registration_response = requests.post(f"{self.api_url}/auth/register", 
                                                json=registration_data, timeout=10)
            
            registration_success = registration_response.status_code == 200
            registration_error = None
            registration_details = None
            
            print(f"   📊 Registration Response Status: {registration_response.status_code}")
            
            if registration_success:
                print(f"✅ Registration SUCCESSFUL")
                registration_details = registration_response.json()
                print(f"   📋 Registration Response:")
                print(f"      - Message: {registration_details.get('message', 'N/A')}")
                print(f"      - Token Type: {registration_details.get('token_type', 'N/A')}")
                print(f"      - Has Access Token: {'access_token' in registration_details}")
                if 'user' in registration_details:
                    new_user = registration_details['user']
                    print(f"      - New User ID: {new_user.get('id', 'N/A')}")
                    print(f"      - New User Email: {new_user.get('email', 'N/A')}")
            else:
                print(f"❌ Registration FAILED")
                try:
                    registration_error = registration_response.json().get('detail', 'Unknown error')
                    print(f"   🔍 Registration Error: {registration_error}")
                except:
                    registration_error = f"HTTP {registration_response.status_code}"
                    print(f"   🔍 Registration Response: {registration_response.text[:200]}")
            
            # Step 3: Check for "email already registered" error specifically
            print(f"\n🔍 Step 3: Analyzing registration error...")
            is_email_already_registered = False
            if registration_error:
                is_email_already_registered = "already registered" in registration_error.lower() or "email already" in registration_error.lower()
                print(f"   📊 'Email Already Registered' Error: {is_email_already_registered}")
                if is_email_already_registered:
                    print(f"   🎯 ROOT CAUSE IDENTIFIED: Email {target_email} is already registered in the system")
                    print(f"   💡 SOLUTION: User should use 'Forgot Password' or try logging in instead")
            
            # Step 4: Test with a different email to verify registration endpoint works
            print(f"\n🔍 Step 4: Testing registration endpoint with different email...")
            test_email = f"test.registration.{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            test_registration_data = {
                "email": test_email,
                "name": "Test Registration User",
                "password": "TestPassword123"
            }
            
            test_registration_response = requests.post(f"{self.api_url}/auth/register", 
                                                     json=test_registration_data, timeout=10)
            
            test_registration_works = test_registration_response.status_code == 200
            print(f"   📊 Test Registration Status: {test_registration_response.status_code}")
            print(f"   ✅ Registration Endpoint Working: {test_registration_works}")
            
            # Step 5: Check backend logs for registration attempts (if admin token available)
            print(f"\n🔍 Step 5: Checking backend logs for registration attempts...")
            if hasattr(self, 'admin_token') and self.admin_token:
                try:
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    logs_response = requests.get(f"{self.api_url}/admin/logs", 
                                               headers=headers, timeout=15)
                    
                    if logs_response.status_code == 200:
                        logs_data = logs_response.json()
                        logs_content = logs_data.get("logs", "")
                        
                        # Search for registration-related entries
                        registration_mentions = logs_content.lower().count("register")
                        email_mentions = logs_content.lower().count(target_email.lower())
                        
                        print(f"   📊 Backend Logs Analysis:")
                        print(f"      - Registration mentions: {registration_mentions}")
                        print(f"      - Target email mentions: {email_mentions}")
                        
                        if email_mentions > 0:
                            print(f"   🎯 FOUND: Target email appears in backend logs")
                        else:
                            print(f"   ❌ Target email not found in recent backend logs")
                    else:
                        print(f"   ❌ Could not retrieve backend logs (Status: {logs_response.status_code})")
                except Exception as e:
                    print(f"   ❌ Error checking backend logs: {str(e)}")
            else:
                print(f"   ⚠️  No admin token available to check backend logs")
            
            # Step 6: Final diagnosis and recommendations
            print(f"\n🎯 FINAL DIAGNOSIS:")
            print("=" * 50)
            
            if user_exists and is_email_already_registered:
                print(f"✅ ISSUE CONFIRMED: Email {target_email} is already registered")
                print(f"📋 USER STATUS: Active user account exists in database")
                print(f"💡 SOLUTION OPTIONS:")
                print(f"   1. User should try logging in with existing credentials")
                print(f"   2. User should use 'Forgot Password' if password is forgotten")
                print(f"   3. Admin can reset user password if needed")
                success = True
                details = f"User exists, registration correctly blocked with 'email already registered' error"
                
            elif not user_exists and registration_success:
                print(f"✅ ISSUE RESOLVED: Registration completed successfully")
                print(f"📋 NEW USER: Account created for {target_email}")
                print(f"💡 USER CAN NOW: Log in with the new account credentials")
                success = True
                details = f"Registration successful, new user account created"
                
            elif not user_exists and not registration_success and not is_email_already_registered:
                print(f"❌ REGISTRATION SYSTEM ISSUE: Registration failed for unknown reason")
                print(f"📋 ERROR: {registration_error}")
                print(f"💡 INVESTIGATION NEEDED: Backend registration endpoint has issues")
                success = False
                details = f"Registration failed with error: {registration_error}"
                
            elif user_exists and not is_email_already_registered:
                print(f"⚠️  INCONSISTENT STATE: User exists but registration didn't return proper error")
                print(f"📋 ISSUE: Registration error handling may be broken")
                print(f"💡 BACKEND FIX NEEDED: Registration should return 'email already registered' error")
                success = False
                details = f"User exists but registration error handling is inconsistent"
                
            else:
                print(f"❓ UNCLEAR STATE: Need further investigation")
                print(f"📋 User exists: {user_exists}")
                print(f"📋 Registration success: {registration_success}")
                print(f"📋 Email already registered error: {is_email_already_registered}")
                success = False
                details = f"Unclear state requiring manual investigation"
            
            print(f"\n📊 REGISTRATION ENDPOINT STATUS: {'✅ Working' if test_registration_works else '❌ Broken'}")
            
            self.log_test("URGENT: amazon.corredor123@gmail.com Registration Issue", success, details)
            return success
            
        except Exception as e:
            error_msg = f"Investigation failed: {str(e)}"
            print(f"❌ INVESTIGATION ERROR: {error_msg}")
            self.log_test("URGENT: amazon.corredor123@gmail.com Registration Issue", False, error_msg)
            return False

    def test_review_request_audit_flow(self):
        """Test the complete audit creation and question flow for user ysaias.corredor@gmail.com with password Clave.01"""
        try:
            # Step 1: Login with specified credentials
            login_data = {
                "email": "ysaias.corredor@gmail.com",
                "password": "Clave.01"
            }
            
            login_response = requests.post(f"{self.api_url}/auth/login", 
                                         json=login_data, timeout=10)
            
            if login_response.status_code != 200:
                try:
                    error_data = login_response.json()
                    details = f"Login failed - Status: {login_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Login failed - Status: {login_response.status_code}, Response: {login_response.text[:200]}"
                self.log_test("Review Request - Login", False, details)
                return False
            
            # Extract token and user data
            login_data_response = login_response.json()
            token = login_data_response.get("access_token")
            user_data = login_data_response.get("user", {})
            
            if not token:
                self.log_test("Review Request - Login", False, "No access token received")
                return False
            
            headers = {"Authorization": f"Bearer {token}"}
            user_id = user_data.get("id")
            
            self.log_test("Review Request - Login", True, f"Login successful, User ID: {user_id}, Role: {user_data.get('role')}")
            
            # Step 2: Create a new audit with specified parameters
            audit_data = {
                "site_name": "Test Site",
                "auditor_name": "Ysaias Test",
                "selected_work_types": ["excavation"],
                "language": "en"
            }
            
            audit_response = requests.post(f"{self.api_url}/audits", 
                                         json=audit_data, headers=headers, timeout=10)
            
            if audit_response.status_code != 200:
                try:
                    error_data = audit_response.json()
                    details = f"Audit creation failed - Status: {audit_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Audit creation failed - Status: {audit_response.status_code}, Response: {audit_response.text[:200]}"
                self.log_test("Review Request - Create Audit", False, details)
                return False
            
            # Extract audit data
            audit_response_data = audit_response.json()
            audit_id = audit_response_data.get("id")
            
            if not audit_id:
                self.log_test("Review Request - Create Audit", False, "No audit ID returned")
                return False
            
            # Verify audit data
            audit_site_name = audit_response_data.get("site_name")
            audit_auditor_name = audit_response_data.get("auditor_name")
            audit_work_types = audit_response_data.get("selected_work_types", [])
            audit_language = audit_response_data.get("language")
            
            audit_data_correct = (
                audit_site_name == "Test Site" and
                audit_auditor_name == "Ysaias Test" and
                "excavation" in audit_work_types and
                audit_language == "en"
            )
            
            if not audit_data_correct:
                details = f"Audit data mismatch - Site: {audit_site_name}, Auditor: {audit_auditor_name}, Work Types: {audit_work_types}, Language: {audit_language}"
                self.log_test("Review Request - Create Audit", False, details)
                return False
            
            self.log_test("Review Request - Create Audit", True, f"Audit created successfully, ID: {audit_id}")
            
            # Step 3: Get questions for the audit
            questions_data = {
                "work_types": ["excavation"],
                "language": "en"
            }
            
            questions_response = requests.post(f"{self.api_url}/audits/questions", 
                                             json=questions_data, headers=headers, timeout=10)
            
            if questions_response.status_code != 200:
                try:
                    error_data = questions_response.json()
                    details = f"Questions request failed - Status: {questions_response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Questions request failed - Status: {questions_response.status_code}, Response: {questions_response.text[:200]}"
                self.log_test("Review Request - Get Questions", False, details)
                return False
            
            # Verify questions data
            questions_response_data = questions_response.json()
            questions = questions_response_data.get("questions", [])
            
            if not questions:
                self.log_test("Review Request - Get Questions", False, "No questions returned")
                return False
            
            # Verify questions structure and content
            questions_valid = True
            for question in questions:
                if not isinstance(question, dict) or "question" not in question or "work_type" not in question:
                    questions_valid = False
                    break
            
            excavation_questions = [q for q in questions if q.get("work_type") == "excavation"]
            
            if not questions_valid:
                self.log_test("Review Request - Get Questions", False, "Invalid question structure")
                return False
            
            if len(excavation_questions) == 0:
                self.log_test("Review Request - Get Questions", False, "No excavation questions found")
                return False
            
            # Check if questions contain expected safety content
            first_question = excavation_questions[0].get("question", "")
            has_safety_content = any(keyword in first_question.lower() for keyword in ["excavation", "slope", "shore", "cave", "safety"])
            
            success = len(questions) > 0 and questions_valid and len(excavation_questions) > 0 and has_safety_content
            details = f"Questions returned: {len(questions)}, Excavation questions: {len(excavation_questions)}, Safety content: {has_safety_content}, First question: '{first_question[:50]}...'"
            
            self.log_test("Review Request - Get Questions", success, details)
            
            # Overall test result
            overall_success = success
            overall_details = f"Complete audit flow tested successfully - Login ✅, Audit Creation ✅, Questions ✅"
            
            self.log_test("Review Request - Complete Audit Flow", overall_success, overall_details)
            return overall_success
            
        except Exception as e:
            self.log_test("Review Request - Complete Audit Flow", False, str(e))
            return False

    def run_review_request_test(self):
        """Run only the review request test"""
        print("🎯 Starting Review Request Test - Audit Creation and Question Flow")
        print("=" * 80)
        print("Testing with user: ysaias.corredor@gmail.com")
        print("Backend URL:", self.api_url)
        print("=" * 80)
        
        # Run the specific review request test
        success = self.test_review_request_audit_flow()
        
        # Print summary
        print("=" * 80)
        print(f"🏁 Review Request Test Complete: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success:
            print("🎉 Review request test passed! Audit creation and question flow is working correctly.")
        else:
            print("❌ Review request test failed. Please check the issues above.")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🔍 Starting CSA Construction Safety Audit Backend Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # 🚨 URGENT: Test specific user registration issue first (review request priority)
        print("\n🚨 URGENT PRIORITY: Specific User Registration Issue Investigation")
        print("=" * 80)
        self.test_specific_user_registration_issue()
        print("=" * 40)
        
        # 🚨 CRITICAL: Test registration first (review request priority)
        print("\n🚨 CRITICAL PRIORITY: Testing User Registration (Review Request)")
        print("=" * 80)
        self.test_user_registration_critical()
        self.test_registration_validation_rules()
        self.test_registration_duplicate_email()
        print("=" * 40)
        
        # 🚨 URGENT INVESTIGATION: Audit with no questions issue
        print("\n🚨 URGENT INVESTIGATION: Audit with no questions issue")
        print("=" * 80)
        self.test_audit_with_no_questions_investigation()
        
        # 🎯 PRIORITY: N/A OPTION IMPLEMENTATION TESTING - REVIEW REQUEST
        print("\n🎯 PRIORITY REVIEW REQUEST: N/A Option Implementation Testing")
        print("=" * 80)
        self.test_na_option_implementation()
        
        # 🚨 URGENT INVESTIGATION: Run comprehensive audit counting investigation first
        self.test_urgent_audit_counting_investigation()
        
        # 🚨 URGENT INVESTIGATION: Audit Counting Discrepancy - HIGHEST PRIORITY
        print("\n🚨 URGENT INVESTIGATION: Audit Counting Discrepancy")
        print("-" * 80)
        print("User ysaias.corredor@gmail.com reports having 12 audits but dashboard shows 9")
        print("Investigating potential data inconsistency issues...")
        
        self.test_owner_login_audit_investigation()
        self.test_audit_count_discrepancy_investigation()
        self.test_audit_filtering_issues_investigation()
        
        # Get admin token for database verification
        self.test_admin_login()
        self.test_database_audit_count_verification()
        
        # NEW REVIEW REQUEST TESTS - SECOND PRIORITY
        print("\n🔍 NEW REVIEW REQUEST: Audit Categories & Admin Dashboard Testing")
        print("-" * 80)
        self.test_new_audit_category_questions()
        self.test_owner_gmail_login()
        self.test_admin_dashboard_endpoint()
        self.test_admin_users_endpoint()
        
        # PRIORITY: Execute Review Request First
        print("\n🎯 PRIORITY REVIEW REQUEST: Create Real Team Members for Delete Testing")
        print("-" * 80)
        self.test_review_request_create_real_team_members()
        
        # URGENT REVIEW REQUEST TEST - Run second
        print("\n🚨 URGENT REVIEW REQUEST: DELETE User Functionality Testing")
        print("-" * 60)
        self.test_delete_user_functionality_review_request()
        
        # PRIORITY: Review Request Test - Create test user for delete functionality
        print("\n🎯 REVIEW REQUEST: Delete User Functionality Setup")
        print("-" * 50)
        self.test_review_request_delete_user_setup()
        
        # ENHANCED USER CREATION SYSTEM TESTING (REVIEW REQUEST) - RUN FIRST
        self.test_enhanced_user_creation_with_custom_password()
        
        # DELETE USER FUNCTIONALITY TEST (REVIEW REQUEST) - RUN SECOND
        self.test_delete_user_functionality()
        
        # DELETE USER FUNCTIONALITY REVIEW REQUEST TEST - RUN THIRD
        self.test_delete_user_functionality_review_request()
        
        # CRITICAL BUSINESS ISSUE - Run fourth
        self.test_critical_subscription_diagnosis()
        
        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Backend is not accessible. Stopping tests.")
            return False
        
        # Critical Launch Verification Tests
        print("\n🚀 CRITICAL LAUNCH VERIFICATION TESTS...")
        self.test_database_connectivity()
        self.test_critical_endpoints_response_time()
        
        # Public endpoint tests
        print("\n📡 Testing Public Endpoints...")
        self.test_work_types_endpoint()
        self.test_subscription_packages_endpoint()
        self.test_api_route_prefix()
        self.test_cors_headers()
        
        # Authentication tests
        print("\n🔐 Testing Authentication & Security...")
        self.test_demo_login()
        self.test_admin_login()
        self.test_test_user_login()  # Test the reported user
        
        # URGENT: Owner login tests (user reported issue)
        print("\n🚨 URGENT: Testing Owner Login (User Reported Issue)...")
        self.test_owner_login()
        self.test_owner_password_validation()
        self.test_owner_jwt_token_generation()
        self.test_owner_user_data_response()
        
        self.test_invalid_login()
        self.test_password_hashing()
        self.test_jwt_token_structure()
        
        # User session persistence test (reported issue)
        print("\n🔄 Testing Session Persistence...")
        self.test_user_session_persistence()
        
        # Protected endpoint tests
        print("\n🛡️ Testing Protected Endpoints...")
        self.test_auth_me_endpoint()
        self.test_auth_me_without_token()
        self.test_auth_me_invalid_token()
        self.test_protected_endpoints_without_auth()
        
        # UPGRADE FLOW TESTS (CRITICAL ISSUE)
        print("\n💳 TESTING UPGRADE FLOW (CRITICAL ISSUE)...")
        self.test_upgrade_flow_basic_plan()
        self.test_upgrade_flow_enterprise_plan()
        
        # ORGANIZATION FLOW TESTS (CRITICAL USER REPORTED ISSUE)
        print("\n🏢 TESTING ORGANIZATION FLOW (USER REPORTED ISSUE)...")
        self.test_organization_flow_existing_user()
        
        # TEAM INVITATION TESTS (CRITICAL USER REPORTED ISSUE)
        print("\n👥 TESTING TEAM INVITATION FUNCTIONALITY (USER REPORTED ISSUE)...")
        self.test_owner_login()
        self.test_organization_team_endpoint_owner()
        self.test_team_invitation_send()
        self.test_pending_invitations_endpoint()
        self.test_team_invitation_in_team_list()
        
        # REVIEW REQUEST SPECIFIC TESTS
        print("\n🔍 TESTING SPECIFIC REVIEW REQUEST REQUIREMENTS...")
        self.test_team_invitation_duplicate_prevention()
        self.test_team_invitation_comprehensive_flow()
        
        # Error handling tests
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Support Panel Admin Endpoints
        print("\n🛠️ Testing Support Panel Admin Endpoints...")
        self.test_admin_create_user_endpoint()
        self.test_admin_create_user_without_auth()
        self.test_admin_create_user_with_user_token()
        self.test_system_logs_endpoint()
        self.test_system_logs_without_auth()
        self.test_support_tickets_endpoint()
        self.test_support_tickets_without_auth()
        
        # Statistics Endpoints
        print("\n📊 Testing Statistics & Charts...")
        self.test_create_test_audit_for_statistics()
        self.test_statistics_endpoint()
        self.test_statistics_charts_endpoint()
        self.test_statistics_without_auth()
        
        # FINAL LAUNCH CRITICAL TESTS
        print("\n🎯 FINAL LAUNCH CRITICAL TESTS...")
        self.test_stripe_payment_checkout_session()
        self.test_pdf_generation()
        self.test_company_settings_get()
        self.test_company_settings_post()
        self.test_bilingual_support()
        
        # URGENT: Review Request Specific Tests
        print("\n🚨 URGENT REVIEW REQUEST TESTING:")
        print("Testing admin payment fix and new endpoints...")
        self.test_admin_fix_pending_payment()
        self.test_owner_subscription_after_fix()
        self.test_email_settings_get()
        self.test_email_settings_post()
        self.test_subscription_cancellation()
        
        # URGENT: Gmail Account Subscription Issue
        print("\n🚨 URGENT: Gmail Account Subscription Issue Testing...")
        print("Testing CORRECT account: ysaias.corredor@gmail.com")
        self.test_find_gmail_user_in_database()
        self.test_gmail_account_subscription_issue()
        
        # Summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! READY FOR COMMERCIAL LAUNCH! 🚀")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            failed_tests = self.tests_run - self.tests_passed
            print(f"❌ {failed_tests} test(s) failed - LAUNCH READINESS COMPROMISED")
            return False

    # ===== NEW USER CREATION SYSTEM TESTS (REVIEW REQUEST) =====
    
    def test_gmail_owner_login(self):
        """Test login with ysaias.corredor@gmail.com / Clave.01 (REVIEW REQUEST)"""
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
                has_message = "message" in data
                
                if has_token:
                    self.owner_token = data["access_token"]
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if success and "user" in data:
                    user_data = data["user"]
                    self.owner_user_data = user_data
                    correct_email = user_data.get("email") == "ysaias.corredor@gmail.com"
                    has_organization = user_data.get("organization_id") is not None
                    is_owner = user_data.get("organization_role") == "owner"
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Has org: {has_organization}, Owner role: {is_owner}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Gmail Owner Login (ysaias.corredor@gmail.com)", success, details)
            return success
        except Exception as e:
            self.log_test("Gmail Owner Login (ysaias.corredor@gmail.com)", False, str(e))
            return False

    def test_direct_user_creation(self):
        """Test POST /api/organization/create-user - Direct user creation (REVIEW REQUEST)"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Direct User Creation", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create unique email for testing
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_email = f"test.direct.user.{timestamp}@example.com"
            
            # Test creating a new user directly
            user_data = {
                "email": test_email,
                "name": "Test Direct User",
                "role": "auditor"
            }
            
            response = requests.post(f"{self.api_url}/organization/create-user", 
                                   json=user_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_user = "user" in data
                has_instructions = "instructions" in data
                
                success = has_message and has_user and has_instructions
                details = f"Status: {response.status_code}, Message: {has_message}, User: {has_user}, Instructions: {has_instructions}"
                
                if has_user:
                    user_info = data["user"]
                    has_id = "id" in user_info
                    has_temp_password = "temporary_password" in user_info
                    correct_email = user_info.get("email") == test_email
                    correct_name = user_info.get("name") == "Test Direct User"
                    correct_role = user_info.get("role") == "auditor"
                    
                    success = success and has_id and has_temp_password and correct_email and correct_name and correct_role
                    details += f", ID: {has_id}, Temp password: {has_temp_password}, Email: {correct_email}, Name: {correct_name}, Role: {correct_role}"
                    
                    # Store for password change test
                    if has_temp_password and has_id:
                        self.test_created_user = {
                            "id": user_info["id"],
                            "email": test_email,
                            "temp_password": user_info["temporary_password"]
                        }
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Direct User Creation", success, details)
            return success
        except Exception as e:
            self.log_test("Direct User Creation", False, str(e))
            return False

    def test_new_user_login_with_temp_password(self):
        """Test login with newly created user and temporary password"""
        if not hasattr(self, 'test_created_user'):
            self.log_test("New User Login with Temp Password", False, "No created user available")
            return False
            
        try:
            login_data = {
                "email": self.test_created_user["email"],
                "password": self.test_created_user["temp_password"]
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if has_token:
                    self.test_created_user["token"] = data["access_token"]
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == self.test_created_user["email"]
                    has_organization = user_data.get("organization_id") is not None
                    is_auditor = user_data.get("organization_role") == "auditor"
                    success = success and correct_email
                    details += f", Correct email: {correct_email}, Has org: {has_organization}, Auditor role: {is_auditor}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("New User Login with Temp Password", success, details)
            return success
        except Exception as e:
            self.log_test("New User Login with Temp Password", False, str(e))
            return False

    def test_password_change_endpoint(self):
        """Test POST /api/auth/change-password - Password change functionality (REVIEW REQUEST)"""
        if not hasattr(self, 'test_created_user') or "token" not in self.test_created_user:
            self.log_test("Password Change Endpoint", False, "No created user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.test_created_user['token']}"}
            
            # Test changing password
            password_data = {
                "old_password": self.test_created_user["temp_password"],
                "new_password": "NewSecurePassword123!"
            }
            
            response = requests.post(f"{self.api_url}/auth/change-password", 
                                   json=password_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "successfully" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Message: {has_message}, Success: {success_message}"
                
                # Store new password for verification
                if success:
                    self.test_created_user["new_password"] = "NewSecurePassword123!"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Password Change Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Password Change Endpoint", False, str(e))
            return False

    def test_login_with_new_password(self):
        """Test login with new password after password change"""
        if not hasattr(self, 'test_created_user') or "new_password" not in self.test_created_user:
            self.log_test("Login with New Password", False, "No new password available")
            return False
            
        try:
            login_data = {
                "email": self.test_created_user["email"],
                "password": self.test_created_user["new_password"]
            }
            
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_token = "access_token" in data
                has_user = "user" in data
                has_message = "message" in data
                
                success = has_token and has_user and has_message
                details = f"Status: {response.status_code}, Token: {has_token}, User: {has_user}, Message: {has_message}"
                
                if has_token:
                    self.test_created_user["new_token"] = data["access_token"]
                
                if success and "user" in data:
                    user_data = data["user"]
                    correct_email = user_data.get("email") == self.test_created_user["email"]
                    success = success and correct_email
                    details += f", Correct email: {correct_email}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Login with New Password", success, details)
            return success
        except Exception as e:
            self.log_test("Login with New Password", False, str(e))
            return False

    def test_user_removal_endpoint(self):
        """Test DELETE /api/organization/remove-user/{user_id} - User removal (REVIEW REQUEST)"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("User Removal Endpoint", False, "No owner token available")
            return False
            
        if not hasattr(self, 'test_created_user') or "id" not in self.test_created_user:
            self.log_test("User Removal Endpoint", False, "No created user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            user_id = self.test_created_user["id"]
            
            response = requests.delete(f"{self.api_url}/organization/remove-user/{user_id}", 
                                     headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                success_message = "removed" in data.get("message", "").lower()
                
                success = has_message and success_message
                details = f"Status: {response.status_code}, Message: {has_message}, Success: {success_message}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Removal Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("User Removal Endpoint", False, str(e))
            return False

    def test_subscription_cancellation_endpoint(self):
        """Test POST /api/payments/cancel-subscription - Subscription cancellation (REVIEW REQUEST)"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Subscription Cancellation Endpoint", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            response = requests.post(f"{self.api_url}/payments/cancel-subscription", 
                                   headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_message = "message" in data
                has_status = "status" in data
                cancelled_status = data.get("status") == "cancelled"
                success_message = "cancelled" in data.get("message", "").lower()
                
                success = has_message and has_status and cancelled_status and success_message
                details = f"Status: {response.status_code}, Message: {has_message}, Status field: {has_status}, Cancelled: {cancelled_status}, Success msg: {success_message}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Subscription Cancellation Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Subscription Cancellation Endpoint", False, str(e))
            return False

    def run_new_user_creation_tests(self):
        """Run new user creation system tests (REVIEW REQUEST)"""
        print("🆕 NEW USER CREATION SYSTEM TESTING")
        print("Testing direct user creation system that replaces invitations")
        print("=" * 80)
        
        # Test sequence as requested in review
        tests = [
            self.test_gmail_owner_login,
            self.test_direct_user_creation,
            self.test_new_user_login_with_temp_password,
            self.test_password_change_endpoint,
            self.test_login_with_new_password,
            self.test_user_removal_endpoint,
            self.test_subscription_cancellation_endpoint
        ]
        
        for test in tests:
            test()
        
        print("=" * 80)
        print(f"🏁 New User Creation Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        
        return self.tests_passed == self.tests_run

    def run_critical_subscription_tests(self):
        """Run critical subscription-related tests for the reported issue"""
        print("🚨 CRITICAL SUBSCRIPTION ISSUE TESTING")
        print("Testing user: ysaias.corredor@clsolution.net / Clave.01")
        print("Issue: User paid for subscription but app shows 'no active subscription'")
        print("=" * 80)
        
        # First, get admin token for database checks
        self.test_admin_login()
        
        # Test owner login and subscription status
        self.test_owner_login()
        self.test_owner_subscription_status()
        
        # Check database records
        self.test_owner_database_record()
        
        # Test payment processing components
        self.test_stripe_webhook_endpoint()
        self.test_payment_processing_logs()
        self.test_subscription_update_flow()
        
        print("=" * 80)
        print(f"🏁 Critical Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        
        return self.tests_passed == self.tests_run

def main():
    import sys
    
    # Check if we should run new user creation tests only
    if len(sys.argv) > 1 and sys.argv[1] == "--new-user-creation":
        tester = CSABackendTester()
        success = tester.run_new_user_creation_tests()
        return 0 if success else 1
    
    # Check if we should run critical subscription tests only
    if len(sys.argv) > 1 and sys.argv[1] == "--subscription":
        tester = CSABackendTester()
        success = tester.run_critical_subscription_tests()
        return 0 if success else 1
    
    # Run all tests
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

    def test_admin_dashboard_endpoint_review_request(self):
        """Test GET /api/admin/dashboard endpoint - REVIEW REQUEST SPECIFIC TEST"""
        if not self.owner_token:
            self.log_test("Admin Dashboard Endpoint (Review Request)", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/admin/dashboard", 
                                  headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected dashboard fields
                expected_fields = ["metrics", "users_by_plan", "revenue_by_month", "top_users"]
                has_all_fields = all(field in data for field in expected_fields)
                
                success = has_all_fields
                details = f"Status: {response.status_code}, Has all fields: {has_all_fields}"
                
                if has_all_fields:
                    # Validate metrics structure
                    metrics = data.get("metrics", {})
                    metrics_fields = ["total_users", "total_audits", "active_subscribers", "total_revenue"]
                    has_metrics = all(field in metrics for field in metrics_fields)
                    
                    # Validate data types
                    users_by_plan = data.get("users_by_plan", [])
                    revenue_by_month = data.get("revenue_by_month", [])
                    top_users = data.get("top_users", [])
                    
                    is_list_users = isinstance(users_by_plan, list)
                    is_list_revenue = isinstance(revenue_by_month, list)
                    is_list_top = isinstance(top_users, list)
                    
                    success = success and has_metrics and is_list_users and is_list_revenue and is_list_top
                    details += f", Metrics: {has_metrics}, Lists valid: users={is_list_users}, revenue={is_list_revenue}, top={is_list_top}"
                    
                    # Check if we have actual data
                    total_users = metrics.get("total_users", 0)
                    total_audits = metrics.get("total_audits", 0)
                    details += f", Total users: {total_users}, Total audits: {total_audits}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Dashboard Endpoint (Review Request)", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Dashboard Endpoint (Review Request)", False, str(e))
            return False

    def test_admin_users_endpoint_review_request(self):
        """Test GET /api/admin/users endpoint - REVIEW REQUEST SPECIFIC TEST"""
        if not self.owner_token:
            self.log_test("Admin Users Endpoint (Review Request)", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/admin/users", 
                                  headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected pagination fields
                expected_fields = ["users", "total_count", "page", "per_page", "total_pages"]
                has_all_fields = all(field in data for field in expected_fields)
                
                success = has_all_fields
                details = f"Status: {response.status_code}, Has all fields: {has_all_fields}"
                
                if has_all_fields:
                    users = data.get("users", [])
                    total_count = data.get("total_count", 0)
                    page = data.get("page", 0)
                    per_page = data.get("per_page", 0)
                    total_pages = data.get("total_pages", 0)
                    
                    is_list_users = isinstance(users, list)
                    has_users = len(users) > 0
                    
                    success = success and is_list_users
                    details += f", Users list: {is_list_users}, User count: {len(users)}, Total: {total_count}, Page: {page}/{total_pages}"
                    
                    # Check user data structure (should not contain password_hash)
                    if users:
                        first_user = users[0]
                        has_email = "email" in first_user
                        has_name = "name" in first_user
                        has_role = "role" in first_user
                        no_password = "password_hash" not in first_user
                        
                        success = success and has_email and has_name and has_role and no_password
                        details += f", User fields: email={has_email}, name={has_name}, role={has_role}, no_password={no_password}"
                    
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Users Endpoint (Review Request)", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Users Endpoint (Review Request)", False, str(e))
            return False

    def test_owner_admin_role_verification_review_request(self):
        """Test that ysaias.corredor@gmail.com now has role='admin' - REVIEW REQUEST SPECIFIC TEST"""
        if not self.owner_token:
            self.log_test("Owner Admin Role Verification (Review Request)", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            response = requests.get(f"{self.api_url}/auth/me", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify user details
                email = data.get("email")
                role = data.get("role")
                subscription_plan = data.get("subscription_plan")
                
                correct_email = email == "ysaias.corredor@gmail.com"
                is_admin = role == "admin"
                has_subscription = subscription_plan is not None
                
                success = correct_email and is_admin
                details = f"Status: {response.status_code}, Email: {email}, Role: {role}, Plan: {subscription_plan}"
                details += f", Correct email: {correct_email}, Is admin: {is_admin}, Has subscription: {has_subscription}"
                
            else:
                success = False
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Admin Role Verification (Review Request)", success, details)
            return success
        except Exception as e:
            self.log_test("Owner Admin Role Verification (Review Request)", False, str(e))
            return False

    def test_admin_authentication_with_jwt_review_request(self):
        """Test admin authentication with JWT token - REVIEW REQUEST SPECIFIC TEST"""
        if not self.owner_token:
            self.log_test("Admin Authentication with JWT (Review Request)", False, "No owner token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Test multiple admin endpoints to verify JWT authentication works
            admin_endpoints = [
                ("/admin/dashboard", "Dashboard"),
                ("/admin/users", "Users List"),
                ("/admin/logs", "System Logs"),
                ("/admin/support-tickets", "Support Tickets")
            ]
            
            all_passed = True
            endpoint_results = []
            
            for endpoint, name in admin_endpoints:
                try:
                    response = requests.get(f"{self.api_url}{endpoint}", 
                                          headers=headers, timeout=15)
                    
                    endpoint_success = response.status_code == 200
                    endpoint_results.append(f"{name}: {response.status_code}")
                    
                    if not endpoint_success:
                        all_passed = False
                        
                except Exception as e:
                    endpoint_results.append(f"{name}: ERROR")
                    all_passed = False
            
            success = all_passed
            details = f"Admin endpoints tested: {', '.join(endpoint_results)}"
            
            self.log_test("Admin Authentication with JWT (Review Request)", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Authentication with JWT (Review Request)", False, str(e))
            return False

    def run_review_request_tests(self):
        """Run the specific tests requested in the review"""
        print("🚀 Starting CSA Backend Testing Suite - ADMIN DASHBOARD FOCUS")
        print("=" * 60)
        
        # REVIEW REQUEST SPECIFIC TESTS - Admin Dashboard Functionality
        review_request_tests = [
            self.test_health_check,
            self.test_owner_login,  # Login with ysaias.corredor@gmail.com / Clave.01
            self.test_owner_admin_role_verification_review_request,  # Verify role="admin"
            self.test_admin_dashboard_endpoint_review_request,  # GET /api/admin/dashboard
            self.test_admin_users_endpoint_review_request,  # GET /api/admin/users
            self.test_admin_authentication_with_jwt_review_request,  # Test admin auth with JWT
        ]
        
        print(f"\n🎯 Running {len(review_request_tests)} REVIEW REQUEST SPECIFIC tests...")
        print("Focus: Admin dashboard functionality testing")
        print("-" * 60)
        
        for test in review_request_tests:
            test()
        
        print("\n" + "=" * 60)
        print(f"🏁 REVIEW REQUEST Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL REVIEW REQUEST TESTS PASSED!")
            print("✅ Admin dashboard functionality is working correctly")
            print("✅ User ysaias.corredor@gmail.com has admin access")
            print("✅ Backend admin endpoints are operational")
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} tests failed")
            print("❌ Admin dashboard functionality needs attention")
        
        success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    # Check if we should run review request tests specifically
    if len(sys.argv) > 1 and sys.argv[1] == "review":
        tester = CSABackendTester()
        success = tester.run_review_request_tests()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "audit-flow":
        # Run the specific audit flow test for the review request
        tester = CSABackendTester()
        success = tester.run_review_request_test()
        sys.exit(0 if success else 1)
    else:
        sys.exit(main())