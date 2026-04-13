"""
Backend API Tests for JWT Authentication and RBAC
Tests: Auth endpoints, Admin user management, Chat isolation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://jwt-rbac-setup.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "pass123456"
TEST_USER_NAME = "Test User"


class TestAuthEndpoints:
    """Test authentication endpoints: signup, login, me"""
    
    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✅ Admin login successful: {data['user']['name']} (role: {data['user']['role']})")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid credentials correctly rejected with 401")
    
    def test_signup_new_user(self):
        """Test signup creates a regular user (not admin since admin exists)"""
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": TEST_USER_NAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL.lower()
        assert data["user"]["role"] == "user", "Second user should have 'user' role, not admin"
        print(f"✅ Signup successful: {data['user']['name']} (role: {data['user']['role']})")
    
    def test_signup_duplicate_email(self):
        """Test signup with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": "Duplicate User",
            "email": ADMIN_EMAIL,
            "password": "somepassword"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Duplicate email correctly rejected with 400")
    
    def test_get_me_with_token(self):
        """Test /auth/me returns current user info"""
        # First login to get token
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_res.json()["token"]
        
        # Call /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print(f"✅ /auth/me returned correct user: {data['name']}")
    
    def test_get_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ /auth/me without token correctly returns 401")


class TestAdminUserManagement:
    """Test admin-only user management endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def user_token(self):
        """Get regular user token"""
        # First try to login, if fails create user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "regularuser@test.com",
            "password": "pass123456"
        })
        if response.status_code == 200:
            return response.json()["token"]
        
        # Create user
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": "Regular User",
            "email": "regularuser@test.com",
            "password": "pass123456"
        })
        return response.json()["token"]
    
    def test_admin_list_users(self, admin_token):
        """Test admin can list all users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1, "Should have at least 1 user (admin)"
        # Check admin user exists
        admin_user = next((u for u in users if u["email"] == ADMIN_EMAIL), None)
        assert admin_user is not None, "Admin user should be in list"
        assert admin_user["role"] == "admin"
        print(f"✅ Admin can list users: {len(users)} users found")
    
    def test_regular_user_cannot_list_users(self, user_token):
        """Test regular user cannot access admin endpoints"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Regular user correctly denied access to admin endpoint (403)")
    
    def test_admin_create_user(self, admin_token):
        """Test admin can create new user"""
        new_email = f"created_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/admin/users", 
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Created User",
                "email": new_email,
                "password": "pass123456",
                "role": "user"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["email"] == new_email.lower()
        assert data["role"] == "user"
        print(f"✅ Admin created user: {data['email']}")
        return data["id"]
    
    def test_admin_update_user(self, admin_token):
        """Test admin can update user"""
        # First create a user to update
        new_email = f"toupdate_{uuid.uuid4().hex[:8]}@test.com"
        create_res = requests.post(f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "To Update", "email": new_email, "password": "pass123456", "role": "user"}
        )
        user_id = create_res.json()["id"]
        
        # Update the user
        response = requests.put(f"{BASE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name", "role": "admin"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify update
        users_res = requests.get(f"{BASE_URL}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        updated_user = next((u for u in users_res.json() if u["id"] == user_id), None)
        assert updated_user["name"] == "Updated Name"
        assert updated_user["role"] == "admin"
        print(f"✅ Admin updated user: {updated_user['name']} (role: {updated_user['role']})")
    
    def test_admin_delete_user(self, admin_token):
        """Test admin can delete user"""
        # First create a user to delete
        new_email = f"todelete_{uuid.uuid4().hex[:8]}@test.com"
        create_res = requests.post(f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "To Delete", "email": new_email, "password": "pass123456", "role": "user"}
        )
        user_id = create_res.json()["id"]
        
        # Delete the user
        response = requests.delete(f"{BASE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify deletion
        users_res = requests.get(f"{BASE_URL}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        deleted_user = next((u for u in users_res.json() if u["id"] == user_id), None)
        assert deleted_user is None, "Deleted user should not be in list"
        print("✅ Admin deleted user successfully")


class TestChatIsolation:
    """Test that users can only see their own chats"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def user_token(self):
        # Create or login as test user
        email = "chattest@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": "pass123456"
        })
        if response.status_code == 200:
            return response.json()["token"]
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": "Chat Test User",
            "email": email,
            "password": "pass123456"
        })
        return response.json()["token"]
    
    def test_user_can_create_chat(self, user_token):
        """Test user can create a chat"""
        response = requests.post(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "User Test Chat", "model": "gpt-4o"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["title"] == "User Test Chat"
        print(f"✅ User created chat: {data['id']}")
        return data["id"]
    
    def test_chat_isolation(self, admin_token, user_token):
        """Test that admin cannot see user's chats and vice versa"""
        # Create chat as user
        user_chat_res = requests.post(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "User Private Chat", "model": "gpt-4o"}
        )
        user_chat_id = user_chat_res.json()["id"]
        
        # Create chat as admin
        admin_chat_res = requests.post(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Admin Private Chat", "model": "gpt-4o"}
        )
        admin_chat_id = admin_chat_res.json()["id"]
        
        # Get user's chats - should not contain admin's chat
        user_chats = requests.get(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {user_token}"}
        ).json()
        user_chat_ids = [c["id"] for c in user_chats]
        assert user_chat_id in user_chat_ids, "User should see their own chat"
        assert admin_chat_id not in user_chat_ids, "User should NOT see admin's chat"
        
        # Get admin's chats - should not contain user's chat
        admin_chats = requests.get(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()
        admin_chat_ids = [c["id"] for c in admin_chats]
        assert admin_chat_id in admin_chat_ids, "Admin should see their own chat"
        assert user_chat_id not in admin_chat_ids, "Admin should NOT see user's chat"
        
        print("✅ Chat isolation working: users can only see their own chats")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/chats/{user_chat_id}", headers={"Authorization": f"Bearer {user_token}"})
        requests.delete(f"{BASE_URL}/api/chats/{admin_chat_id}", headers={"Authorization": f"Bearer {admin_token}"})
    
    def test_user_cannot_access_other_user_chat(self, admin_token, user_token):
        """Test user cannot access another user's chat directly"""
        # Create chat as admin
        admin_chat_res = requests.post(f"{BASE_URL}/api/chats",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Admin Only Chat", "model": "gpt-4o"}
        )
        admin_chat_id = admin_chat_res.json()["id"]
        
        # Try to access admin's chat as user
        response = requests.get(f"{BASE_URL}/api/chats/{admin_chat_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ User correctly denied access to other user's chat (404)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/chats/{admin_chat_id}", headers={"Authorization": f"Bearer {admin_token}"})


class TestConnectionsEndpoint:
    """Test connections endpoint (admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def user_token(self):
        email = "conntest@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": "pass123456"
        })
        if response.status_code == 200:
            return response.json()["token"]
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": "Conn Test User",
            "email": email,
            "password": "pass123456"
        })
        return response.json()["token"]
    
    def test_admin_can_get_connections(self, admin_token):
        """Test admin can access connections endpoint"""
        response = requests.get(f"{BASE_URL}/api/connections",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "providers" in data
        assert "openai" in data["providers"]
        print("✅ Admin can access connections endpoint")
    
    def test_user_cannot_get_connections(self, user_token):
        """Test regular user cannot access connections endpoint"""
        response = requests.get(f"{BASE_URL}/api/connections",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Regular user correctly denied access to connections (403)")


class TestModelsEndpoint:
    """Test models endpoint (public)"""
    
    def test_models_endpoint_public(self):
        """Test models endpoint is accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/models")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        models = response.json()
        assert isinstance(models, list)
        assert len(models) > 0, "Should have at least 1 model"
        print(f"✅ Models endpoint returned {len(models)} models")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
