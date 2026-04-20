"""
Test file upload and download functionality
Tests:
- POST /api/files/upload with text file
- POST /api/files/upload with image file
- GET /api/files/{file_id}?auth={token} - authenticated download
- GET /api/files/{file_id} - unauthenticated download (should 401)
- POST /api/chats/{chat_id}/messages with file_ids
"""
import pytest
import requests
import os
import tempfile
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "user2@test.com"
USER_PASSWORD = "pass123456"


class TestFileUpload:
    """File upload endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_upload_text_file(self):
        """Test uploading a text file - should return file metadata with is_image=false"""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test text file content for testing file upload.")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                # Remove Content-Type header for multipart
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{BASE_URL}/api/files/upload", files=files, headers=headers)
            
            assert response.status_code == 200, f"Upload failed: {response.text}"
            data = response.json()
            
            # Verify response structure
            assert "id" in data, "Response should contain 'id'"
            assert "original_filename" in data, "Response should contain 'original_filename'"
            assert "is_image" in data, "Response should contain 'is_image'"
            assert data["is_image"] == False, "Text file should have is_image=false"
            assert data["original_filename"] == "test_document.txt"
            assert "content_type" in data
            assert "size" in data
            assert data["size"] > 0
            
            # Store file_id for later tests
            self.text_file_id = data["id"]
            print(f"✓ Text file uploaded successfully: {data['id']}")
            return data["id"]
        finally:
            os.unlink(temp_path)
    
    def test_upload_image_file(self):
        """Test uploading an image file - should return file metadata with is_image=true"""
        # Create a minimal PNG image (1x1 pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(png_data)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{BASE_URL}/api/files/upload", files=files, headers=headers)
            
            assert response.status_code == 200, f"Upload failed: {response.text}"
            data = response.json()
            
            # Verify response structure
            assert "id" in data, "Response should contain 'id'"
            assert "original_filename" in data, "Response should contain 'original_filename'"
            assert "is_image" in data, "Response should contain 'is_image'"
            assert data["is_image"] == True, "PNG file should have is_image=true"
            assert data["original_filename"] == "test_image.png"
            assert data["content_type"] == "image/png"
            
            print(f"✓ Image file uploaded successfully: {data['id']}")
            return data["id"]
        finally:
            os.unlink(temp_path)
    
    def test_download_file_with_auth(self):
        """Test downloading a file with auth query param"""
        # First upload a file
        file_id = self.test_upload_text_file()
        
        # Download with auth query param
        response = requests.get(f"{BASE_URL}/api/files/{file_id}?auth={self.token}")
        
        assert response.status_code == 200, f"Download failed: {response.text}"
        assert len(response.content) > 0, "Downloaded file should have content"
        print(f"✓ File downloaded successfully with auth query param")
    
    def test_download_file_with_bearer_token(self):
        """Test downloading a file with Bearer token header"""
        # First upload a file
        file_id = self.test_upload_text_file()
        
        # Download with Bearer token
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/files/{file_id}", headers=headers)
        
        assert response.status_code == 200, f"Download failed: {response.text}"
        assert len(response.content) > 0, "Downloaded file should have content"
        print(f"✓ File downloaded successfully with Bearer token")
    
    def test_download_file_without_auth(self):
        """Test downloading a file without authentication - should return 401"""
        # First upload a file
        file_id = self.test_upload_text_file()
        
        # Try to download without auth
        response = requests.get(f"{BASE_URL}/api/files/{file_id}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"✓ Unauthenticated download correctly returns 401")
    
    def test_download_nonexistent_file(self):
        """Test downloading a non-existent file - should return 404"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/files/nonexistent-file-id", headers=headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent file correctly returns 404")


class TestMessageWithFiles:
    """Test sending messages with file attachments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def _upload_test_file(self):
        """Helper to upload a test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file content for message attachment.")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('attachment.txt', f, 'text/plain')}
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{BASE_URL}/api/files/upload", files=files, headers=headers)
            
            assert response.status_code == 200
            return response.json()["id"]
        finally:
            os.unlink(temp_path)
    
    def _create_chat(self):
        """Helper to create a new chat"""
        response = self.session.post(f"{BASE_URL}/api/chats", json={
            "title": "TEST_File_Attachment_Chat",
            "model": "gpt-4o"
        })
        assert response.status_code == 200, f"Failed to create chat: {response.text}"
        return response.json()["id"]
    
    def test_send_message_with_file_ids(self):
        """Test sending a message with file_ids - should process files and return response with attachments"""
        # Upload a file first
        file_id = self._upload_test_file()
        
        # Create a chat
        chat_id = self._create_chat()
        
        # Send message with file_ids
        response = self.session.post(f"{BASE_URL}/api/chats/{chat_id}/messages", json={
            "content": "Please analyze this attached file.",
            "file_ids": [file_id]
        })
        
        assert response.status_code == 200, f"Send message failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "user_message" in data, "Response should contain 'user_message'"
        assert "assistant_message" in data, "Response should contain 'assistant_message'"
        
        user_msg = data["user_message"]
        assert "attachments" in user_msg, "User message should contain 'attachments'"
        assert user_msg["attachments"] is not None, "Attachments should not be None"
        assert len(user_msg["attachments"]) == 1, "Should have 1 attachment"
        
        attachment = user_msg["attachments"][0]
        assert attachment["id"] == file_id, "Attachment ID should match uploaded file"
        assert "filename" in attachment, "Attachment should have filename"
        assert "content_type" in attachment, "Attachment should have content_type"
        assert "size" in attachment, "Attachment should have size"
        
        print(f"✓ Message with file attachment sent successfully")
        print(f"  - User message has {len(user_msg['attachments'])} attachment(s)")
        print(f"  - Assistant responded: {data['assistant_message']['content'][:100]}...")
        
        # Cleanup - delete the test chat
        self.session.delete(f"{BASE_URL}/api/chats/{chat_id}")
    
    def test_send_message_with_image_file(self):
        """Test sending a message with an image file - should be processed as vision input"""
        # Create a minimal PNG image
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(png_data)
            temp_path = f.name
        
        try:
            # Upload image
            with open(temp_path, 'rb') as f:
                files = {'file': ('test_vision.png', f, 'image/png')}
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{BASE_URL}/api/files/upload", files=files, headers=headers)
            
            assert response.status_code == 200
            file_id = response.json()["id"]
            
            # Create a chat
            chat_id = self._create_chat()
            
            # Send message with image
            response = self.session.post(f"{BASE_URL}/api/chats/{chat_id}/messages", json={
                "content": "What do you see in this image?",
                "file_ids": [file_id]
            })
            
            assert response.status_code == 200, f"Send message failed: {response.text}"
            data = response.json()
            
            user_msg = data["user_message"]
            assert user_msg["attachments"] is not None
            assert len(user_msg["attachments"]) == 1
            assert user_msg["attachments"][0]["is_image"] == True
            
            print(f"✓ Message with image attachment sent successfully")
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/chats/{chat_id}")
        finally:
            os.unlink(temp_path)


class TestFileUploadEdgeCases:
    """Test edge cases for file upload"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_upload_without_auth(self):
        """Test uploading without authentication - should return 401"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                # No auth header
                response = requests.post(f"{BASE_URL}/api/files/upload", files=files)
            
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
            print(f"✓ Upload without auth correctly returns 401")
        finally:
            os.unlink(temp_path)
    
    def test_upload_various_file_types(self):
        """Test uploading various file types"""
        test_files = [
            ("test.json", '{"key": "value"}', "application/json", False),
            ("test.md", "# Markdown Header", "text/markdown", False),
            ("test.py", "print('hello')", "text/x-python", False),
            ("test.csv", "a,b,c\n1,2,3", "text/csv", False),
        ]
        
        for filename, content, content_type, expected_is_image in test_files:
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{filename.split(".")[-1]}', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                with open(temp_path, 'rb') as f:
                    files = {'file': (filename, f, content_type)}
                    headers = {"Authorization": f"Bearer {self.token}"}
                    response = requests.post(f"{BASE_URL}/api/files/upload", files=files, headers=headers)
                
                assert response.status_code == 200, f"Upload {filename} failed: {response.text}"
                data = response.json()
                assert data["is_image"] == expected_is_image, f"{filename} should have is_image={expected_is_image}"
                print(f"✓ {filename} uploaded successfully (is_image={data['is_image']})")
            finally:
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
