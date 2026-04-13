#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://ui-replica-36.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_symbol} {test_name}")
    if details:
        print(f"    {details}")
    print()

def test_connections_and_models():
    """Test the connections and models endpoints as specified in the review request"""
    
    print("=" * 80)
    print("TESTING CONNECTIONS AND MODELS ENDPOINTS")
    print("=" * 80)
    print()
    
    # Test 1: GET /api/connections - Should return default config
    print("TEST 1: GET /api/connections - Default configuration")
    try:
        response = requests.get(f"{BACKEND_URL}/connections", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Verify structure
            required_keys = ["providers", "defaultModel", "modelParams", "disabledModels"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                log_test("GET /api/connections - Structure", "FAIL", f"Missing keys: {missing_keys}")
                return False
            
            # Verify providers
            providers = data.get("providers", {})
            expected_providers = ["openai", "anthropic", "gemini"]
            missing_providers = [p for p in expected_providers if p not in providers]
            
            if missing_providers:
                log_test("GET /api/connections - Providers", "FAIL", f"Missing providers: {missing_providers}")
                return False
            
            # Verify all providers are enabled with useEmergentKey=true
            all_enabled = all(providers[p].get("enabled", False) for p in expected_providers)
            all_use_emergent = all(providers[p].get("useEmergentKey", False) for p in expected_providers)
            
            if not all_enabled:
                log_test("GET /api/connections - Providers Enabled", "FAIL", "Not all providers enabled by default")
                return False
            
            if not all_use_emergent:
                log_test("GET /api/connections - UseEmergentKey", "FAIL", "Not all providers using emergent key")
                return False
            
            # Verify default model
            if data.get("defaultModel") != "gpt-4o":
                log_test("GET /api/connections - Default Model", "FAIL", f"Expected gpt-4o, got {data.get('defaultModel')}")
                return False
            
            # Verify modelParams structure
            model_params = data.get("modelParams", {})
            required_params = ["temperature", "maxTokens", "topP"]
            missing_params = [p for p in required_params if p not in model_params]
            
            if missing_params:
                log_test("GET /api/connections - Model Params", "FAIL", f"Missing params: {missing_params}")
                return False
            
            log_test("GET /api/connections - Default Config", "PASS", 
                    f"3 providers enabled, defaultModel={data['defaultModel']}, disabledModels={data['disabledModels']}")
            
        else:
            log_test("GET /api/connections", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/connections", "FAIL", f"Exception: {str(e)}")
        return False
    
    # Test 2: PUT /api/connections - Save updated connections
    print("TEST 2: PUT /api/connections - Save updated configuration")
    try:
        update_data = {
            "providers": {
                "openai": {"enabled": True, "apiKey": "", "name": "OpenAI", "useEmergentKey": True},
                "anthropic": {"enabled": False, "apiKey": "", "name": "Anthropic", "useEmergentKey": True},
                "gemini": {"enabled": True, "apiKey": "", "name": "Google Gemini", "useEmergentKey": True}
            },
            "defaultModel": "gpt-4o",
            "modelParams": {"temperature": 0.5, "maxTokens": 2048, "topP": 0.9},
            "disabledModels": ["gpt-5-mini"]
        }
        
        response = requests.put(f"{BACKEND_URL}/connections", json=update_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                log_test("PUT /api/connections - Save", "PASS", "Updated connections saved successfully")
            else:
                log_test("PUT /api/connections - Save", "FAIL", f"Unexpected response: {result}")
                return False
        else:
            log_test("PUT /api/connections - Save", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("PUT /api/connections - Save", "FAIL", f"Exception: {str(e)}")
        return False
    
    # Test 3: GET /api/connections - Verify persistence
    print("TEST 3: GET /api/connections - Verify persistence of saved data")
    try:
        response = requests.get(f"{BACKEND_URL}/connections", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Verify anthropic is disabled
            anthropic_enabled = data.get("providers", {}).get("anthropic", {}).get("enabled", True)
            if anthropic_enabled:
                log_test("GET /api/connections - Anthropic Disabled", "FAIL", "Anthropic should be disabled")
                return False
            
            # Verify gpt-5-mini is in disabledModels
            disabled_models = data.get("disabledModels", [])
            if "gpt-5-mini" not in disabled_models:
                log_test("GET /api/connections - Disabled Models", "FAIL", "gpt-5-mini should be in disabledModels")
                return False
            
            # Verify temperature is 0.5
            temperature = data.get("modelParams", {}).get("temperature")
            if temperature != 0.5:
                log_test("GET /api/connections - Temperature", "FAIL", f"Expected 0.5, got {temperature}")
                return False
            
            log_test("GET /api/connections - Persistence", "PASS", 
                    f"Anthropic disabled, gpt-5-mini disabled, temperature={temperature}")
            
        else:
            log_test("GET /api/connections - Persistence", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/connections - Persistence", "FAIL", f"Exception: {str(e)}")
        return False
    
    # Test 4: GET /api/models - Should NOT include anthropic models
    print("TEST 4: GET /api/models - Verify anthropic models excluded")
    try:
        response = requests.get(f"{BACKEND_URL}/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            
            # Check that no anthropic models are included
            anthropic_models = [m for m in models if m.get("provider") == "anthropic"]
            if anthropic_models:
                log_test("GET /api/models - Anthropic Excluded", "FAIL", 
                        f"Found {len(anthropic_models)} anthropic models when provider is disabled")
                return False
            
            # Check that gpt-5-mini is included but with enabled=false
            gpt5_mini = next((m for m in models if m.get("id") == "gpt-5-mini"), None)
            if not gpt5_mini:
                log_test("GET /api/models - GPT-5-mini Present", "FAIL", "gpt-5-mini should be present in models")
                return False
            
            if gpt5_mini.get("enabled", True):
                log_test("GET /api/models - GPT-5-mini Disabled", "FAIL", "gpt-5-mini should have enabled=false")
                return False
            
            # Count total models (should be 6: 4 openai + 2 gemini)
            total_models = len(models)
            expected_count = 6  # 4 openai + 2 gemini (no anthropic)
            
            log_test("GET /api/models - Filtered Results", "PASS", 
                    f"Found {total_models} models (no anthropic), gpt-5-mini enabled=false")
            
        else:
            log_test("GET /api/models - Filtered", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/models - Filtered", "FAIL", f"Exception: {str(e)}")
        return False
    
    # Test 5: PUT /api/connections - Restore defaults
    print("TEST 5: PUT /api/connections - Restore defaults")
    try:
        restore_data = {
            "providers": {
                "openai": {"enabled": True, "apiKey": "", "name": "OpenAI", "useEmergentKey": True},
                "anthropic": {"enabled": True, "apiKey": "", "name": "Anthropic", "useEmergentKey": True},
                "gemini": {"enabled": True, "apiKey": "", "name": "Google Gemini", "useEmergentKey": True}
            },
            "defaultModel": "gpt-4o",
            "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
            "disabledModels": []
        }
        
        response = requests.put(f"{BACKEND_URL}/connections", json=restore_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                log_test("PUT /api/connections - Restore", "PASS", "Default connections restored successfully")
            else:
                log_test("PUT /api/connections - Restore", "FAIL", f"Unexpected response: {result}")
                return False
        else:
            log_test("PUT /api/connections - Restore", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("PUT /api/connections - Restore", "FAIL", f"Exception: {str(e)}")
        return False
    
    # Test 6: GET /api/models - Should now include all 8 models
    print("TEST 6: GET /api/models - Verify all models included and enabled")
    try:
        response = requests.get(f"{BACKEND_URL}/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            
            # Count models by provider
            openai_models = [m for m in models if m.get("provider") == "openai"]
            anthropic_models = [m for m in models if m.get("provider") == "anthropic"]
            gemini_models = [m for m in models if m.get("provider") == "gemini"]
            
            total_models = len(models)
            expected_total = 8  # 4 openai + 2 anthropic + 2 gemini
            
            if total_models != expected_total:
                log_test("GET /api/models - Total Count", "FAIL", 
                        f"Expected {expected_total} models, got {total_models}")
                return False
            
            # Verify all models are enabled
            disabled_models = [m for m in models if not m.get("enabled", True)]
            if disabled_models:
                log_test("GET /api/models - All Enabled", "FAIL", 
                        f"Found {len(disabled_models)} disabled models: {[m['id'] for m in disabled_models]}")
                return False
            
            log_test("GET /api/models - All Models", "PASS", 
                    f"Found all {total_models} models: {len(openai_models)} OpenAI, {len(anthropic_models)} Anthropic, {len(gemini_models)} Gemini - all enabled")
            
        else:
            log_test("GET /api/models - All Models", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET /api/models - All Models", "FAIL", f"Exception: {str(e)}")
        return False
    
    return True

def main():
    """Run all tests"""
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_connections_and_models()
    
    print("=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED! Connections and Models endpoints working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Check the output above for details.")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())