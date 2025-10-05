#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for PythonQuest Feedback System
Tests all feedback-related endpoints with proper authentication
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://pylearn-10.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.regular_user_token = None
        self.admin_user_token = None
        self.test_results = []
        self.feedback_ids = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Create test users and get authentication tokens"""
        print("\n=== AUTHENTICATION SETUP ===")
        
        # Create regular user
        regular_user_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/signup", 
                                   json=regular_user_data, headers=self.headers)
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                self.regular_user_token = data["access_token"]
                self.regular_user_id = data["user"]["id"]
                self.log_result("Regular User Creation", True, f"Created user: {regular_user_data['username']}")
            else:
                self.log_result("Regular User Creation", False, 
                              f"Failed to create regular user: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Regular User Creation", False, f"Exception: {str(e)}")
            return False
        
        # Try to create admin user - try multiple admin usernames
        admin_usernames = ["administrator", "admin"]
        admin_created = False
        
        for username in admin_usernames:
            admin_email = f"{username}_{uuid.uuid4().hex[:8]}@example.com"
            admin_user_data = {
                "username": username,
                "email": admin_email, 
                "password": "AdminPassword123!"
            }
            
            try:
                response = requests.post(f"{self.base_url}/auth/signup", 
                                       json=admin_user_data, headers=self.headers)
                if response.status_code == 201 or response.status_code == 200:
                    data = response.json()
                    self.admin_user_token = data["access_token"]
                    self.admin_user_id = data["user"]["id"]
                    self.log_result("Admin User Creation", True, f"Created {username} user")
                    admin_created = True
                    break
            except Exception as e:
                continue
        
        if not admin_created:
            self.log_result("Admin User Creation", False, "Could not create any admin user")
            return False
        
        return True
    
    def test_feedback_submission(self):
        """Test feedback submission endpoint"""
        print("\n=== FEEDBACK SUBMISSION TESTS ===")
        
        if not self.regular_user_token:
            self.log_result("Feedback Submission Setup", False, "No regular user token available")
            return
        
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.regular_user_token}"
        
        # Test valid feedback submission
        valid_feedback = {
            "rating": 4,
            "category": "general",
            "comment": "This level was really helpful for learning Python basics!"
        }
        
        try:
            response = requests.post(f"{self.base_url}/levels/100/feedback", 
                                   json=valid_feedback, headers=auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("feedback_id"):
                    self.feedback_ids.append(data["feedback_id"])
                    self.log_result("Valid Feedback Submission", True, 
                                  f"Feedback submitted successfully: {data['feedback_id']}")
                else:
                    self.log_result("Valid Feedback Submission", False, 
                                  "Response missing success or feedback_id", data)
            else:
                self.log_result("Valid Feedback Submission", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Valid Feedback Submission", False, f"Exception: {str(e)}")
        
        # Test invalid rating
        invalid_feedback = {
            "rating": 6,  # Invalid rating (should be 1-5)
            "category": "general",
            "comment": "Test comment"
        }
        
        try:
            response = requests.post(f"{self.base_url}/levels/100/feedback", 
                                   json=invalid_feedback, headers=auth_headers)
            if response.status_code == 422:  # Validation error expected
                self.log_result("Invalid Rating Validation", True, "Correctly rejected invalid rating")
            else:
                self.log_result("Invalid Rating Validation", False, 
                              f"Should reject invalid rating, got: {response.status_code}")
        except Exception as e:
            self.log_result("Invalid Rating Validation", False, f"Exception: {str(e)}")
        
        # Test missing fields
        incomplete_feedback = {
            "rating": 3
            # Missing category and comment
        }
        
        try:
            response = requests.post(f"{self.base_url}/levels/100/feedback", 
                                   json=incomplete_feedback, headers=auth_headers)
            if response.status_code == 422:  # Validation error expected
                self.log_result("Missing Fields Validation", True, "Correctly rejected incomplete feedback")
            else:
                self.log_result("Missing Fields Validation", False, 
                              f"Should reject incomplete feedback, got: {response.status_code}")
        except Exception as e:
            self.log_result("Missing Fields Validation", False, f"Exception: {str(e)}")
        
        # Test unauthorized access
        try:
            response = requests.post(f"{self.base_url}/levels/100/feedback", 
                                   json=valid_feedback, headers=self.headers)  # No auth token
            if response.status_code == 401 or response.status_code == 403:
                self.log_result("Unauthorized Feedback Access", True, "Correctly rejected unauthorized access")
            else:
                self.log_result("Unauthorized Feedback Access", False, 
                              f"Should reject unauthorized access, got: {response.status_code}")
        except Exception as e:
            self.log_result("Unauthorized Feedback Access", False, f"Exception: {str(e)}")
        
        # Submit more test feedback for admin testing
        test_feedbacks = [
            {"rating": 5, "category": "difficulty", "comment": "Perfect difficulty level"},
            {"rating": 2, "category": "bug", "comment": "Found a small issue with the code editor"},
            {"rating": 3, "category": "suggestion", "comment": "Could use more examples"}
        ]
        
        for i, feedback in enumerate(test_feedbacks):
            try:
                response = requests.post(f"{self.base_url}/levels/{101 + i}/feedback", 
                                       json=feedback, headers=auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("feedback_id"):
                        self.feedback_ids.append(data["feedback_id"])
            except Exception as e:
                print(f"Failed to submit test feedback {i}: {e}")
    
    def test_admin_feedback_endpoints(self):
        """Test admin feedback management endpoints"""
        print("\n=== ADMIN FEEDBACK ENDPOINTS TESTS ===")
        
        if not self.admin_user_token:
            self.log_result("Admin Endpoints Setup", False, "No admin user token available")
            return
        
        admin_headers = self.headers.copy()
        admin_headers["Authorization"] = f"Bearer {self.admin_user_token}"
        
        # Test get all feedback
        try:
            response = requests.get(f"{self.base_url}/admin/feedback", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                if "feedback" in data and "statistics" in data:
                    feedback_count = len(data["feedback"])
                    self.log_result("Get All Feedback", True, 
                                  f"Retrieved {feedback_count} feedback items with statistics")
                else:
                    self.log_result("Get All Feedback", False, 
                                  "Response missing feedback or statistics", data)
            else:
                self.log_result("Get All Feedback", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Get All Feedback", False, f"Exception: {str(e)}")
        
        # Test filtering by status
        try:
            response = requests.get(f"{self.base_url}/admin/feedback?status=pending", 
                                  headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                pending_feedback = data.get("feedback", [])
                all_pending = all(fb.get("status") == "pending" for fb in pending_feedback)
                if all_pending:
                    self.log_result("Filter by Status", True, 
                                  f"Correctly filtered {len(pending_feedback)} pending feedback")
                else:
                    self.log_result("Filter by Status", False, "Filter returned non-pending feedback")
            else:
                self.log_result("Filter by Status", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Filter by Status", False, f"Exception: {str(e)}")
        
        # Test filtering by category
        try:
            response = requests.get(f"{self.base_url}/admin/feedback?category=general", 
                                  headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                general_feedback = data.get("feedback", [])
                all_general = all(fb.get("category") == "general" for fb in general_feedback)
                if all_general:
                    self.log_result("Filter by Category", True, 
                                  f"Correctly filtered {len(general_feedback)} general feedback")
                else:
                    self.log_result("Filter by Category", False, "Filter returned non-general feedback")
            else:
                self.log_result("Filter by Category", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Filter by Category", False, f"Exception: {str(e)}")
        
        # Test filtering by level_id
        try:
            response = requests.get(f"{self.base_url}/admin/feedback?level_id=100", 
                                  headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                level_feedback = data.get("feedback", [])
                all_level_100 = all(fb.get("level_id") == 100 for fb in level_feedback)
                if all_level_100:
                    self.log_result("Filter by Level ID", True, 
                                  f"Correctly filtered {len(level_feedback)} feedback for level 100")
                else:
                    self.log_result("Filter by Level ID", False, "Filter returned wrong level feedback")
            else:
                self.log_result("Filter by Level ID", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Filter by Level ID", False, f"Exception: {str(e)}")
        
        # Test status update
        if self.feedback_ids:
            feedback_id = self.feedback_ids[0]
            status_update = {"status": "reviewed"}
            
            try:
                response = requests.patch(f"{self.base_url}/admin/feedback/{feedback_id}/status", 
                                        json=status_update, headers=admin_headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_result("Update Feedback Status", True, 
                                      f"Successfully updated feedback status to reviewed")
                        
                        # Verify the status was updated
                        response = requests.get(f"{self.base_url}/admin/feedback", headers=admin_headers)
                        if response.status_code == 200:
                            feedback_data = response.json()
                            updated_feedback = next((fb for fb in feedback_data.get("feedback", []) 
                                                   if fb.get("_id") == feedback_id), None)
                            if updated_feedback and updated_feedback.get("status") == "reviewed":
                                self.log_result("Verify Status Update", True, "Status update verified")
                            else:
                                self.log_result("Verify Status Update", False, "Status not updated in database")
                    else:
                        self.log_result("Update Feedback Status", False, "Response missing success flag", data)
                else:
                    self.log_result("Update Feedback Status", False, 
                                  f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Update Feedback Status", False, f"Exception: {str(e)}")
        
        # Test invalid status update
        if self.feedback_ids:
            feedback_id = self.feedback_ids[0]
            invalid_status = {"status": "invalid_status"}
            
            try:
                response = requests.patch(f"{self.base_url}/admin/feedback/{feedback_id}/status", 
                                        json=invalid_status, headers=admin_headers)
                if response.status_code == 400:
                    self.log_result("Invalid Status Update", True, "Correctly rejected invalid status")
                else:
                    self.log_result("Invalid Status Update", False, 
                                  f"Should reject invalid status, got: {response.status_code}")
            except Exception as e:
                self.log_result("Invalid Status Update", False, f"Exception: {str(e)}")
        
        # Test feedback statistics
        try:
            response = requests.get(f"{self.base_url}/admin/feedback/statistics", 
                                  headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_feedback", "status_breakdown", "category_breakdown", "rating_distribution"]
                has_all_fields = all(field in data for field in required_fields)
                if has_all_fields:
                    self.log_result("Feedback Statistics", True, 
                                  f"Retrieved complete statistics: {data['total_feedback']} total feedback")
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_result("Feedback Statistics", False, 
                                  f"Missing fields: {missing_fields}", data)
            else:
                self.log_result("Feedback Statistics", False, 
                              f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Feedback Statistics", False, f"Exception: {str(e)}")
    
    def test_admin_access_control(self):
        """Test admin access control"""
        print("\n=== ADMIN ACCESS CONTROL TESTS ===")
        
        if not self.regular_user_token:
            self.log_result("Access Control Setup", False, "No regular user token available")
            return
        
        regular_headers = self.headers.copy()
        regular_headers["Authorization"] = f"Bearer {self.regular_user_token}"
        
        # Test regular user accessing admin endpoints
        admin_endpoints = [
            "/admin/feedback",
            "/admin/feedback/statistics"
        ]
        
        for endpoint in admin_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=regular_headers)
                if response.status_code == 403:
                    self.log_result(f"Access Control - {endpoint}", True, 
                                  "Correctly denied regular user access")
                else:
                    self.log_result(f"Access Control - {endpoint}", False, 
                                  f"Should deny access, got: {response.status_code}")
            except Exception as e:
                self.log_result(f"Access Control - {endpoint}", False, f"Exception: {str(e)}")
        
        # Test regular user trying to update feedback status
        if self.feedback_ids:
            feedback_id = self.feedback_ids[0]
            status_update = {"status": "resolved"}
            
            try:
                response = requests.patch(f"{self.base_url}/admin/feedback/{feedback_id}/status", 
                                        json=status_update, headers=regular_headers)
                if response.status_code == 403:
                    self.log_result("Access Control - Status Update", True, 
                                  "Correctly denied regular user status update")
                else:
                    self.log_result("Access Control - Status Update", False, 
                                  f"Should deny access, got: {response.status_code}")
            except Exception as e:
                self.log_result("Access Control - Status Update", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Backend API Tests for Feedback System")
        print(f"Base URL: {self.base_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        self.test_feedback_submission()
        self.test_admin_feedback_endpoints()
        self.test_admin_access_control()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"     Details: {result['details']}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()