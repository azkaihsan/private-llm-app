#!/usr/bin/env python3
"""
Backend API Testing Script for OpenWebUI Clone
Tests all backend endpoints including new archive/export/import functionality
"""

import requests
import json
import sys
from datetime import datetime

# Use the production backend URL from frontend/.env
BASE_URL = "https://ui-replica-36.preview.emergentagent.com/api"

def print_test(title):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print('='*60)

def print_result(success, message, response=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if response and hasattr(response, 'text'):
        print(f"Response: {response.text[:200]}...")
    elif response:
        print(f"Response: {str(response)[:200]}...")

def test_archive_export_import_flow():
    """Test the complete archive, export, and import workflow"""
    
    # Test data
    test_chat_data = {
        "title": "Test Export Chat",
        "model": "gpt-4o"
    }
    
    import_chat_data = {
        "version": "1.0",
        "chat": {
            "title": "Imported Test",
            "model": "gpt-4o"
        },
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }
    
    chat_id = None
    imported_chat_id = None
    
    try:
        # 1. Create a test chat
        print_test("1. POST /api/chats - Create test chat")
        response = requests.post(f"{BASE_URL}/chats", json=test_chat_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            chat_id = data.get('id')
            print_result(True, f"Chat created with ID: {chat_id}", data)
        else:
            print_result(False, f"Failed to create chat. Status: {response.status_code}", response)
            return False
            
        # 2. Archive the chat
        print_test(f"2. PUT /api/chats/{chat_id}/archive - Archive the chat")
        response = requests.put(f"{BASE_URL}/chats/{chat_id}/archive", timeout=10)
        if response.status_code == 200:
            data = response.json()
            expected_response = data.get('status') == 'ok'
            print_result(expected_response, f"Chat archived successfully", data)
        else:
            print_result(False, f"Failed to archive chat. Status: {response.status_code}", response)
            return False
            
        # 3. Verify chat is NOT in regular list
        print_test("3. GET /api/chats - Verify archived chat not in regular list")
        response = requests.get(f"{BASE_URL}/chats", timeout=10)
        if response.status_code == 200:
            chats = response.json()
            chat_in_regular = any(chat.get('id') == chat_id for chat in chats)
            print_result(not chat_in_regular, f"Archived chat correctly excluded from regular list. Found {len(chats)} chats", chats)
        else:
            print_result(False, f"Failed to get chats. Status: {response.status_code}", response)
            return False
            
        # 4. Verify chat appears in archived list
        print_test("4. GET /api/chats/archived - Verify chat in archived list")
        response = requests.get(f"{BASE_URL}/chats/archived", timeout=10)
        if response.status_code == 200:
            archived_chats = response.json()
            chat_in_archived = any(chat.get('id') == chat_id for chat in archived_chats)
            print_result(chat_in_archived, f"Chat found in archived list. Found {len(archived_chats)} archived chats", archived_chats)
        else:
            print_result(False, f"Failed to get archived chats. Status: {response.status_code}", response)
            return False
            
        # 5. Unarchive the chat
        print_test(f"5. PUT /api/chats/{chat_id}/unarchive - Unarchive the chat")
        response = requests.put(f"{BASE_URL}/chats/{chat_id}/unarchive", timeout=10)
        if response.status_code == 200:
            data = response.json()
            expected_response = data.get('status') == 'ok'
            print_result(expected_response, f"Chat unarchived successfully", data)
        else:
            print_result(False, f"Failed to unarchive chat. Status: {response.status_code}", response)
            return False
            
        # 6. Verify chat is back in regular list
        print_test("6. GET /api/chats - Verify chat back in regular list")
        response = requests.get(f"{BASE_URL}/chats", timeout=10)
        if response.status_code == 200:
            chats = response.json()
            chat_in_regular = any(chat.get('id') == chat_id for chat in chats)
            print_result(chat_in_regular, f"Chat back in regular list. Found {len(chats)} total chats", f"Chat {chat_id} found: {chat_in_regular}")
        else:
            print_result(False, f"Failed to get chats. Status: {response.status_code}", response)
            return False
            
        # 7. Export the chat
        print_test(f"7. GET /api/chats/{chat_id}/export - Export the chat")
        response = requests.get(f"{BASE_URL}/chats/{chat_id}/export", timeout=10)
        if response.status_code == 200:
            export_data = response.json()
            required_fields = ['version', 'source', 'chat', 'messages', 'exported_at']
            has_all_fields = all(field in export_data for field in required_fields)
            print_result(has_all_fields, f"Export successful with all required fields", export_data)
        else:
            print_result(False, f"Failed to export chat. Status: {response.status_code}", response)
            return False
            
        # 8. Import a chat
        print_test("8. POST /api/chats/import - Import a new chat")
        response = requests.post(f"{BASE_URL}/chats/import", json=import_chat_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            imported_chat_id = data.get('chat_id')
            import_success = data.get('status') == 'ok' and imported_chat_id
            print_result(import_success, f"Chat imported with ID: {imported_chat_id}", data)
        else:
            print_result(False, f"Failed to import chat. Status: {response.status_code}", response)
            return False
            
        # 9. Verify imported chat has correct messages
        print_test(f"9. GET /api/chats/{imported_chat_id} - Verify imported chat has 2 messages")
        response = requests.get(f"{BASE_URL}/chats/{imported_chat_id}", timeout=10)
        if response.status_code == 200:
            chat_data = response.json()
            messages = chat_data.get('messages', [])
            has_two_messages = len(messages) == 2
            print_result(has_two_messages, f"Imported chat has {len(messages)} messages (expected 2)", f"Messages: {messages}")
        else:
            print_result(False, f"Failed to get imported chat. Status: {response.status_code}", response)
            return False
            
        # 10. Clean up: Archive both chats
        print_test("10. Archive both chats for cleanup")
        for test_id in [chat_id, imported_chat_id]:
            if test_id:
                response = requests.put(f"{BASE_URL}/chats/{test_id}/archive", timeout=10)
                success = response.status_code == 200
                print_result(success, f"Archived chat {test_id}", response.json() if success else response)
                
        # 11. Delete all archived chats
        print_test("11. DELETE /api/chats/archived/all - Delete all archived chats")
        response = requests.delete(f"{BASE_URL}/chats/archived/all", timeout=10)
        if response.status_code == 200:
            data = response.json()
            delete_success = data.get('status') == 'ok'
            deleted_count = data.get('deleted_count', 0)
            print_result(delete_success, f"Deleted {deleted_count} archived chats", data)
        else:
            print_result(False, f"Failed to delete archived chats. Status: {response.status_code}", response)
            return False
            
        # 12. Verify both chats are gone
        print_test("12. Verify both test chats are completely deleted")
        for test_id in [chat_id, imported_chat_id]:
            if test_id:
                response = requests.get(f"{BASE_URL}/chats/{test_id}", timeout=10)
                is_deleted = response.status_code == 404
                print_result(is_deleted, f"Chat {test_id} properly deleted (404 expected)", f"Status: {response.status_code}")
                
        print(f"\n{'='*60}")
        print("🎉 ALL ARCHIVE/EXPORT/IMPORT TESTS COMPLETED SUCCESSFULLY!")
        print('='*60)
        return True
        
    except Exception as e:
        print_result(False, f"Test failed with exception: {str(e)}")
        return False

def main():
    print("🚀 Starting Backend API Tests for Archive/Export/Import Features")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    success = test_archive_export_import_flow()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()