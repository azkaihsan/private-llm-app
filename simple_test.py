#!/usr/bin/env python3
"""
Simplified test to verify the core functionality
"""

import requests
import json

BACKEND_URL = "https://ui-replica-36.preview.emergentagent.com/api"

def test_core_functionality():
    print("🧪 Testing Core Provider Support Functionality")
    print("=" * 60)
    
    # Test 1: GET /api/connections - Should return 9 providers
    print("\n1. Testing GET /api/connections")
    response = requests.get(f"{BACKEND_URL}/connections")
    if response.status_code == 200:
        data = response.json()
        providers = data.get("providers", {})
        print(f"✅ Returns {len(providers)} providers: {list(providers.keys())}")
        
        # Check enabled status
        enabled = [p for p, config in providers.items() if config.get("enabled", False)]
        disabled = [p for p, config in providers.items() if not config.get("enabled", True)]
        print(f"✅ Enabled by default: {enabled}")
        print(f"✅ Disabled by default: {disabled}")
    else:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    # Test 2: GET /api/models - Should return 8 models from 3 enabled providers
    print("\n2. Testing GET /api/models")
    response = requests.get(f"{BACKEND_URL}/models")
    if response.status_code == 200:
        models = response.json()
        provider_counts = {}
        for model in models:
            provider = model.get("provider")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        print(f"✅ Returns {len(models)} models")
        print(f"✅ Provider distribution: {provider_counts}")
        
        expected_total = 8  # 4 openai + 2 anthropic + 2 gemini
        if len(models) == expected_total:
            print(f"✅ Correct total: {expected_total} models")
        else:
            print(f"❌ Expected {expected_total}, got {len(models)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    # Test 3: Enable additional providers
    print("\n3. Testing PUT /api/connections - Enable deepseek and grok")
    update_data = {
        "providers": {
            "openai": {"enabled": True, "useEmergentKey": True},
            "anthropic": {"enabled": True, "useEmergentKey": True},
            "gemini": {"enabled": True, "useEmergentKey": True},
            "deepseek": {"enabled": True, "apiKey": "test-key", "useEmergentKey": False},
            "qwen": {"enabled": False},
            "grok": {"enabled": True, "apiKey": "test-key", "useEmergentKey": False},
            "perplexity": {"enabled": False},
            "bedrock": {"enabled": False},
            "openai_compatible": {"enabled": False}
        },
        "defaultModel": "gpt-4o",
        "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
        "disabledModels": []
    }
    
    response = requests.put(f"{BACKEND_URL}/connections", json=update_data)
    if response.status_code == 200:
        print("✅ Successfully updated connections")
        
        # Verify models endpoint now returns more models
        response = requests.get(f"{BACKEND_URL}/models")
        if response.status_code == 200:
            models = response.json()
            provider_counts = {}
            for model in models:
                provider = model.get("provider")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            print(f"✅ Now returns {len(models)} models")
            print(f"✅ Provider distribution: {provider_counts}")
            
            expected_total = 12  # 4 openai + 2 anthropic + 2 gemini + 2 deepseek + 2 grok
            if len(models) == expected_total:
                print(f"✅ Correct total after update: {expected_total} models")
            else:
                print(f"❌ Expected {expected_total}, got {len(models)}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
    else:
        print(f"❌ Failed to update connections: {response.status_code}")
        return False
    
    # Test 4: Test custom models
    print("\n4. Testing custom models with openai_compatible")
    update_data["providers"]["openai_compatible"] = {
        "enabled": True,
        "apiKey": "test",
        "useEmergentKey": False,
        "baseUrl": "https://api.example.com/v1",
        "customModels": "custom-model-1, custom-model-2"
    }
    
    response = requests.put(f"{BACKEND_URL}/connections", json=update_data)
    if response.status_code == 200:
        response = requests.get(f"{BACKEND_URL}/models")
        if response.status_code == 200:
            models = response.json()
            custom_models = [m for m in models if m.get("provider") == "openai_compatible"]
            print(f"✅ Added {len(custom_models)} custom models: {[m.get('name') for m in custom_models]}")
            print(f"✅ Total models with custom: {len(models)}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
    else:
        print(f"❌ Failed to add custom models: {response.status_code}")
    
    print("\n🎉 Core functionality test completed!")
    return True

if __name__ == "__main__":
    test_core_functionality()