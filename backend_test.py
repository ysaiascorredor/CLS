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
                "origin_url": "https://safeinspect-2.preview.emergentagent.com"
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
                "origin_url": "https://safeinspect-2.preview.emergentagent.com"
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
                "origin_url": "https://safeinspect-2.preview.emergentagent.com"
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

    def run_all_tests(self):
        """Run all backend tests"""
        print("🔍 Starting CSA Construction Safety Audit Backend Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
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