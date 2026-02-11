#!/usr/bin/env python3
"""
Backend API Test Suite for OpenWebUI Clone Chat Application
Tests all backend endpoints in the specified sequence.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://ui-replica-36.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.chat_id = None
        self.results = []
        
    def log_result(self, test_name, success, message, response=None):
        """Log test results with details"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if response:
            result["status_code"] = response.status_code if hasattr(response, 'status_code') else 'N/A'
            try:
                result["response_data"] = response.json() if hasattr(response, 'json') else str(response)
            except:
                result["response_data"] = str(response)
        
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_get_models(self):
        """Test GET /api/models - Should return list of 8 AI models"""
        try:
            response = requests.get(f"{BACKEND_URL}/models", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/models", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            models = response.json()
            
            if not isinstance(models, list):
                self.log_result("GET /api/models", False, f"Expected list, got {type(models)}", response)
                return False
                
            if len(models) != 8:
                self.log_result("GET /api/models", False, f"Expected 8 models, got {len(models)}", response)
                return False
                
            # Check required fields
            for model in models:
                if not all(field in model for field in ['id', 'name', 'provider']):
                    self.log_result("GET /api/models", False, f"Model missing required fields: {model}", response)
                    return False
                    
            self.log_result("GET /api/models", True, f"Successfully returned {len(models)} models with correct structure", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/models", False, f"Request failed: {str(e)}")
            return False
    
    def test_create_chat(self):
        """Test POST /api/chats - Create new chat"""
        try:
            chat_data = {"title": "Test Chat", "model": "gpt-4o"}
            response = requests.post(f"{BACKEND_URL}/chats", json=chat_data, timeout=10)
            
            if response.status_code != 200:
                self.log_result("POST /api/chats", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            chat = response.json()
            
            # Check required fields
            required_fields = ['id', 'title', 'model', 'created_at']
            for field in required_fields:
                if field not in chat:
                    self.log_result("POST /api/chats", False, f"Response missing required field: {field}", response)
                    return False
                    
            if chat['title'] != "Test Chat" or chat['model'] != "gpt-4o":
                self.log_result("POST /api/chats", False, f"Chat data mismatch: title='{chat.get('title')}', model='{chat.get('model')}'", response)
                return False
                
            # Save chat ID for subsequent tests
            self.chat_id = chat['id']
            self.log_result("POST /api/chats", True, f"Successfully created chat with ID: {self.chat_id}", response)
            return True
            
        except Exception as e:
            self.log_result("POST /api/chats", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_chats(self):
        """Test GET /api/chats - Get list of all chats"""
        try:
            response = requests.get(f"{BACKEND_URL}/chats", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/chats", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            chats = response.json()
            
            if not isinstance(chats, list):
                self.log_result("GET /api/chats", False, f"Expected list, got {type(chats)}", response)
                return False
                
            # Should contain at least our created chat
            if len(chats) == 0:
                self.log_result("GET /api/chats", False, "No chats returned", response)
                return False
                
            # Check if our chat is in the list
            chat_found = any(chat.get('id') == self.chat_id for chat in chats)
            if not chat_found:
                self.log_result("GET /api/chats", False, f"Created chat {self.chat_id} not found in chat list", response)
                return False
                
            # Check sorting (should be by created_at desc)
            if len(chats) > 1:
                for i in range(len(chats) - 1):
                    if chats[i].get('created_at', '') < chats[i + 1].get('created_at', ''):
                        self.log_result("GET /api/chats", False, "Chats not sorted by created_at desc", response)
                        return False
                        
            self.log_result("GET /api/chats", True, f"Successfully returned {len(chats)} chats, properly sorted", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/chats", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_chat_by_id(self):
        """Test GET /api/chats/{chat_id} - Get specific chat with messages"""
        if not self.chat_id:
            self.log_result("GET /api/chats/{chat_id}", False, "No chat_id available from previous test")
            return False
            
        try:
            response = requests.get(f"{BACKEND_URL}/chats/{self.chat_id}", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/chats/{chat_id}", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            chat = response.json()
            
            # Check required fields
            required_fields = ['id', 'title', 'model', 'created_at', 'messages']
            for field in required_fields:
                if field not in chat:
                    self.log_result("GET /api/chats/{chat_id}", False, f"Response missing required field: {field}", response)
                    return False
                    
            if chat['id'] != self.chat_id:
                self.log_result("GET /api/chats/{chat_id}", False, f"Chat ID mismatch: expected {self.chat_id}, got {chat['id']}", response)
                return False
                
            if not isinstance(chat['messages'], list):
                self.log_result("GET /api/chats/{chat_id}", False, f"Messages should be a list, got {type(chat['messages'])}", response)
                return False
                
            # Should be empty initially
            if len(chat['messages']) != 0:
                self.log_result("GET /api/chats/{chat_id}", False, f"Expected empty messages array, got {len(chat['messages'])} messages", response)
                return False
                
            self.log_result("GET /api/chats/{chat_id}", True, f"Successfully retrieved chat with empty messages array", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/chats/{chat_id}", False, f"Request failed: {str(e)}")
            return False
    
    def test_rename_chat(self):
        """Test PUT /api/chats/{chat_id} - Rename chat"""
        if not self.chat_id:
            self.log_result("PUT /api/chats/{chat_id}", False, "No chat_id available from previous test")
            return False
            
        try:
            rename_data = {"title": "Renamed Chat"}
            response = requests.put(f"{BACKEND_URL}/chats/{self.chat_id}", json=rename_data, timeout=10)
            
            if response.status_code != 200:
                self.log_result("PUT /api/chats/{chat_id}", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            result = response.json()
            
            if result.get('status') != 'ok':
                self.log_result("PUT /api/chats/{chat_id}", False, f"Expected status 'ok', got {result.get('status')}", response)
                return False
                
            # Verify the rename by fetching the chat again
            get_response = requests.get(f"{BACKEND_URL}/chats/{self.chat_id}", timeout=10)
            if get_response.status_code == 200:
                updated_chat = get_response.json()
                if updated_chat.get('title') != "Renamed Chat":
                    self.log_result("PUT /api/chats/{chat_id}", False, f"Title not updated. Expected 'Renamed Chat', got '{updated_chat.get('title')}'", response)
                    return False
                    
            self.log_result("PUT /api/chats/{chat_id}", True, "Successfully renamed chat", response)
            return True
            
        except Exception as e:
            self.log_result("PUT /api/chats/{chat_id}", False, f"Request failed: {str(e)}")
            return False
    
    def test_send_message(self):
        """Test POST /api/chats/{chat_id}/messages - Send message and get AI response"""
        if not self.chat_id:
            self.log_result("POST /api/chats/{chat_id}/messages", False, "No chat_id available from previous test")
            return False
            
        try:
            message_data = {"content": "What is 2+2? Answer briefly."}
            print(f"Sending message to LLM... (this may take a few seconds)")
            response = requests.post(f"{BACKEND_URL}/chats/{self.chat_id}/messages", json=message_data, timeout=60)
            
            if response.status_code != 200:
                self.log_result("POST /api/chats/{chat_id}/messages", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            result = response.json()
            
            # Check required fields
            if 'user_message' not in result or 'assistant_message' not in result:
                self.log_result("POST /api/chats/{chat_id}/messages", False, "Response missing user_message or assistant_message", response)
                return False
                
            user_msg = result['user_message']
            ai_msg = result['assistant_message']
            
            # Check user message
            required_user_fields = ['id', 'chat_id', 'role', 'content', 'timestamp']
            for field in required_user_fields:
                if field not in user_msg:
                    self.log_result("POST /api/chats/{chat_id}/messages", False, f"User message missing field: {field}", response)
                    return False
                    
            if user_msg['role'] != 'user' or user_msg['content'] != message_data['content']:
                self.log_result("POST /api/chats/{chat_id}/messages", False, "User message content/role incorrect", response)
                return False
                
            # Check assistant message
            required_ai_fields = ['id', 'chat_id', 'role', 'content', 'timestamp']
            for field in required_ai_fields:
                if field not in ai_msg:
                    self.log_result("POST /api/chats/{chat_id}/messages", False, f"Assistant message missing field: {field}", response)
                    return False
                    
            if ai_msg['role'] != 'assistant' or not ai_msg['content']:
                self.log_result("POST /api/chats/{chat_id}/messages", False, "Assistant message role/content incorrect", response)
                return False
                
            self.log_result("POST /api/chats/{chat_id}/messages", True, f"Successfully sent message and received AI response: {ai_msg['content'][:50]}...", response)
            return True
            
        except Exception as e:
            self.log_result("POST /api/chats/{chat_id}/messages", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_chat_with_messages(self):
        """Test GET /api/chats/{chat_id} - Verify chat now has messages"""
        if not self.chat_id:
            self.log_result("GET /api/chats/{chat_id} (with messages)", False, "No chat_id available from previous test")
            return False
            
        try:
            response = requests.get(f"{BACKEND_URL}/chats/{self.chat_id}", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/chats/{chat_id} (with messages)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            chat = response.json()
            
            if 'messages' not in chat:
                self.log_result("GET /api/chats/{chat_id} (with messages)", False, "Response missing messages field", response)
                return False
                
            messages = chat['messages']
            
            if len(messages) != 2:
                self.log_result("GET /api/chats/{chat_id} (with messages)", False, f"Expected 2 messages (user + assistant), got {len(messages)}", response)
                return False
                
            # Check message order (should be user first, then assistant)
            if messages[0]['role'] != 'user' or messages[1]['role'] != 'assistant':
                self.log_result("GET /api/chats/{chat_id} (with messages)", False, f"Message roles incorrect: {[m['role'] for m in messages]}", response)
                return False
                
            self.log_result("GET /api/chats/{chat_id} (with messages)", True, f"Chat successfully contains {len(messages)} messages in correct order", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/chats/{chat_id} (with messages)", False, f"Request failed: {str(e)}")
            return False
    
    def test_delete_chat(self):
        """Test DELETE /api/chats/{chat_id} - Delete chat"""
        if not self.chat_id:
            self.log_result("DELETE /api/chats/{chat_id}", False, "No chat_id available from previous test")
            return False
            
        try:
            response = requests.delete(f"{BACKEND_URL}/chats/{self.chat_id}", timeout=10)
            
            if response.status_code != 200:
                self.log_result("DELETE /api/chats/{chat_id}", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            result = response.json()
            
            if result.get('status') != 'ok':
                self.log_result("DELETE /api/chats/{chat_id}", False, f"Expected status 'ok', got {result.get('status')}", response)
                return False
                
            self.log_result("DELETE /api/chats/{chat_id}", True, "Successfully deleted chat", response)
            return True
            
        except Exception as e:
            self.log_result("DELETE /api/chats/{chat_id}", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_deleted_chat(self):
        """Test GET /api/chats/{chat_id} - Verify chat is deleted (should return 404)"""
        if not self.chat_id:
            self.log_result("GET /api/chats/{chat_id} (deleted)", False, "No chat_id available from previous test")
            return False
            
        try:
            response = requests.get(f"{BACKEND_URL}/chats/{self.chat_id}", timeout=10)
            
            if response.status_code != 404:
                self.log_result("GET /api/chats/{chat_id} (deleted)", False, f"Expected status 404, got {response.status_code}", response)
                return False
                
            self.log_result("GET /api/chats/{chat_id} (deleted)", True, "Correctly returned 404 for deleted chat", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/chats/{chat_id} (deleted)", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_settings_initial(self):
        """Test GET /api/settings - Should return empty object initially"""
        try:
            response = requests.get(f"{BACKEND_URL}/settings", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/settings (initial)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            data = response.json()
            
            if data == {}:
                self.log_result("GET /api/settings (initial)", True, "Successfully returned empty object as expected", response)
            else:
                self.log_result("GET /api/settings (initial)", True, f"⚠️ Not empty but working. Contains: {data}", response)
            return True
            
        except Exception as e:
            self.log_result("GET /api/settings (initial)", False, f"Request failed: {str(e)}")
            return False
    
    def test_put_settings_save(self):
        """Test PUT /api/settings - Save initial settings"""
        try:
            settings_data = {
                "appName": "My Custom AI",
                "theme": "midnight-blue", 
                "logoText": "AI",
                "mainBg": "#1a1a2e",
                "fontSize": 16
            }
            
            response = requests.put(
                f"{BACKEND_URL}/settings",
                json=settings_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result("PUT /api/settings (save)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            result = response.json()
            
            if result.get('status') != 'ok':
                self.log_result("PUT /api/settings (save)", False, f"Expected status 'ok', got {result.get('status')}", response)
                return False
                
            self.log_result("PUT /api/settings (save)", True, "Successfully saved initial settings", response)
            return True
            
        except Exception as e:
            self.log_result("PUT /api/settings (save)", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_settings_verify(self):
        """Test GET /api/settings - Verify saved settings are returned correctly"""
        try:
            response = requests.get(f"{BACKEND_URL}/settings", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/settings (verify)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            data = response.json()
            
            expected_settings = {
                "appName": "My Custom AI",
                "theme": "midnight-blue", 
                "logoText": "AI",
                "mainBg": "#1a1a2e",
                "fontSize": 16
            }
            
            # Check if all expected fields are present and correct
            missing_fields = []
            incorrect_values = []
            
            for key, expected_value in expected_settings.items():
                if key not in data:
                    missing_fields.append(key)
                elif data[key] != expected_value:
                    incorrect_values.append(f"{key}: expected '{expected_value}', got '{data[key]}'")
            
            if missing_fields or incorrect_values:
                issues = []
                if missing_fields:
                    issues.append(f"Missing fields: {missing_fields}")
                if incorrect_values:
                    issues.append(f"Incorrect values: {incorrect_values}")
                self.log_result("GET /api/settings (verify)", False, "; ".join(issues), response)
                return False
            else:
                self.log_result("GET /api/settings (verify)", True, "All settings retrieved correctly", response)
                return True
            
        except Exception as e:
            self.log_result("GET /api/settings (verify)", False, f"Request failed: {str(e)}")
            return False
    
    def test_put_settings_update(self):
        """Test PUT /api/settings - Update with different values"""
        try:
            updated_settings = {
                "appName": "Updated AI",
                "logoType": "text",
                "logoBgColor": "#ff5500"
            }
            
            response = requests.put(
                f"{BACKEND_URL}/settings",
                json=updated_settings,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result("PUT /api/settings (update)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            result = response.json()
            
            if result.get('status') != 'ok':
                self.log_result("PUT /api/settings (update)", False, f"Expected status 'ok', got {result.get('status')}", response)
                return False
                
            self.log_result("PUT /api/settings (update)", True, "Successfully updated settings", response)
            return True
            
        except Exception as e:
            self.log_result("PUT /api/settings (update)", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_settings_final_verify(self):
        """Test GET /api/settings - Verify updated values persist and merge correctly"""
        try:
            response = requests.get(f"{BACKEND_URL}/settings", timeout=10)
            
            if response.status_code != 200:
                self.log_result("GET /api/settings (final)", False, f"Expected status 200, got {response.status_code}", response)
                return False
                
            data = response.json()
            
            # Expected final state should be a merge of initial and updated settings
            expected_final = {
                "appName": "Updated AI",  # Updated
                "theme": "midnight-blue",  # Should persist from initial 
                "logoText": "AI",  # Should persist from initial
                "mainBg": "#1a1a2e",  # Should persist from initial
                "fontSize": 16,  # Should persist from initial
                "logoType": "text",  # New from update
                "logoBgColor": "#ff5500"  # New from update
            }
            
            # Check all expected fields
            missing_fields = []
            incorrect_values = []
            
            for key, expected_value in expected_final.items():
                if key not in data:
                    missing_fields.append(key)
                elif data[key] != expected_value:
                    incorrect_values.append(f"{key}: expected '{expected_value}', got '{data[key]}'")
            
            if missing_fields or incorrect_values:
                issues = []
                if missing_fields:
                    issues.append(f"Missing fields: {missing_fields}")
                if incorrect_values:
                    issues.append(f"Incorrect values: {incorrect_values}")
                self.log_result("GET /api/settings (final)", False, "; ".join(issues), response)
                return False
            else:
                # Check for extra fields (informational only)
                extra_fields = [key for key in data if key not in expected_final]
                extra_info = f" (Extra fields: {extra_fields})" if extra_fields else ""
                self.log_result("GET /api/settings (final)", True, f"All expected settings present and merged correctly{extra_info}", response)
                return True
            
        except Exception as e:
            self.log_result("GET /api/settings (final)", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting Backend API Test Suite for OpenWebUI Clone")
        print(f"📡 Testing backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        tests = [
            ("1. GET /api/models", self.test_get_models),
            ("2. POST /api/chats", self.test_create_chat),
            ("3. GET /api/chats", self.test_get_chats),
            ("4. GET /api/chats/{chat_id}", self.test_get_chat_by_id),
            ("5. PUT /api/chats/{chat_id}", self.test_rename_chat),
            ("6. POST /api/chats/{chat_id}/messages", self.test_send_message),
            ("7. GET /api/chats/{chat_id} (with messages)", self.test_get_chat_with_messages),
            ("8. DELETE /api/chats/{chat_id}", self.test_delete_chat),
            ("9. GET /api/chats/{chat_id} (deleted)", self.test_get_deleted_chat),
            ("10. GET /api/settings (initial)", self.test_get_settings_initial),
            ("11. PUT /api/settings (save)", self.test_put_settings_save),
            ("12. GET /api/settings (verify)", self.test_get_settings_verify),
            ("13. PUT /api/settings (update)", self.test_put_settings_update),
            ("14. GET /api/settings (final)", self.test_get_settings_final_verify)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            if test_func():
                passed += 1
            else:
                print(f"   ⚠️  Test failed, but continuing with remaining tests...")
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests PASSED! Backend API is working correctly.")
            return True
        else:
            print(f"❌ {total - passed} tests FAILED. See details above.")
            return False

def main():
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS:")
    print("=" * 60)
    
    for result in tester.results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}")
        print(f"   📝 {result['message']}")
        if 'status_code' in result:
            print(f"   🔗 HTTP {result['status_code']}")
        print()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())