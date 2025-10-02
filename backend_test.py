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

    def create_test_session(self):
        """Create a test session using MongoDB directly (simulating OAuth)"""
        try:
            # This would normally be done through OAuth, but for testing we'll simulate it
            # In a real test, you'd use the auth_testing.md instructions
            print("⚠️  Note: Authentication testing requires manual session creation via MongoDB")
            print("   Refer to /app/auth_testing.md for session creation instructions")
            
            # For now, we'll test without authentication and expect 401s
            self.log_test("Test Session Creation", False, "Manual session creation required - see auth_testing.md")
            return False
        except Exception as e:
            self.log_test("Test Session Creation", False, str(e))
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
        self.test_work_types_endpoint()
        self.test_subscription_packages_endpoint()
        self.test_api_route_prefix()
        self.test_cors_headers()
        
        # Authentication tests
        self.create_test_session()
        self.test_protected_endpoints_without_auth()
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