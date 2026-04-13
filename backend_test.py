#!/usr/bin/env python3
"""
Backend API Testing for Updated Provider Support
Tests the connections and models endpoints with 9 providers support
"""

import requests
import json
import sys
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://ui-replica-36.preview.emergentagent.com/api"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def test(self, name: str, condition: bool, details: str = ""):
        if condition:
            self.passed += 1
            status = "✅ PASS"
            print(f"{status}: {name}")
            if details:
                print(f"    {details}")
        else:
            self.failed += 1
            status = "❌ FAIL"
            print(f"{status}: {name}")
            if details:
                print(f"    {details}")
        
        self.results.append({
            "name": name,
            "status": status,
            "details": details
        })

    def summary(self):
        total = self.passed + self.failed
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total: {total}, Passed: {self.passed}, Failed: {self.failed}")
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result["status"] == "❌ FAIL":
                    print(f"  - {result['name']}: {result['details']}")
        return self.failed == 0

def test_connections_and_models():
    """Test the updated connections and models endpoints with 9 provider support"""
    runner = TestRunner()
    
    print("🧪 Testing Updated Connections and Models Endpoints with 9 Provider Support")
    print("=" * 80)
    
    # Test 1: GET /api/connections - Should return 9 providers
    print("\n1. Testing GET /api/connections - Should return 9 providers")
    try:
        response = requests.get(f"{BACKEND_URL}/connections", timeout=10)
        runner.test(
            "GET /connections returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})
            
            # Check for all 9 expected providers
            expected_providers = [
                "openai", "anthropic", "gemini",  # enabled by default
                "deepseek", "qwen", "grok", "perplexity", "bedrock", "openai_compatible"  # disabled by default
            ]
            
            runner.test(
                "Has 9 providers",
                len(providers) == 9,
                f"Found {len(providers)} providers: {list(providers.keys())}"
            )
            
            for provider in expected_providers:
                runner.test(
                    f"Has {provider} provider",
                    provider in providers,
                    f"Provider config: {providers.get(provider, 'MISSING')}"
                )
            
            # Check default enabled status
            enabled_by_default = ["openai", "anthropic", "gemini"]
            disabled_by_default = ["deepseek", "qwen", "grok", "perplexity", "bedrock", "openai_compatible"]
            
            for provider in enabled_by_default:
                if provider in providers:
                    runner.test(
                        f"{provider} enabled by default",
                        providers[provider].get("enabled", False),
                        f"Enabled: {providers[provider].get('enabled')}"
                    )
            
            for provider in disabled_by_default:
                if provider in providers:
                    runner.test(
                        f"{provider} disabled by default",
                        not providers[provider].get("enabled", True),
                        f"Enabled: {providers[provider].get('enabled')}"
                    )
            
            # Check required fields
            for provider_name, config in providers.items():
                required_fields = ["enabled", "apiKey", "name", "useEmergentKey"]
                for field in required_fields:
                    runner.test(
                        f"{provider_name} has {field} field",
                        field in config,
                        f"Config: {config}"
                    )
    
    except Exception as e:
        runner.test("GET /connections request", False, f"Error: {str(e)}")
    
    # Test 2: GET /api/models - Should return 8 models from 3 enabled providers
    print("\n2. Testing GET /api/models - Should return 8 models from 3 enabled providers")
    try:
        response = requests.get(f"{BACKEND_URL}/models", timeout=10)
        runner.test(
            "GET /models returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            models = response.json()
            
            runner.test(
                "Returns 8 models initially",
                len(models) == 8,
                f"Found {len(models)} models"
            )
            
            # Check provider distribution
            provider_counts = {}
            for model in models:
                provider = model.get("provider")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            expected_counts = {"openai": 4, "anthropic": 2, "gemini": 2}
            for provider, expected_count in expected_counts.items():
                actual_count = provider_counts.get(provider, 0)
                runner.test(
                    f"Has {expected_count} {provider} models",
                    actual_count == expected_count,
                    f"Expected: {expected_count}, Found: {actual_count}"
                )
            
            # Verify no models from disabled providers
            disabled_providers = ["deepseek", "qwen", "grok", "perplexity", "bedrock", "openai_compatible"]
            for provider in disabled_providers:
                count = provider_counts.get(provider, 0)
                runner.test(
                    f"No {provider} models (disabled)",
                    count == 0,
                    f"Found {count} models from disabled provider"
                )
    
    except Exception as e:
        runner.test("GET /models request", False, f"Error: {str(e)}")
    
    # Test 3: PUT /api/connections - Enable deepseek and grok
    print("\n3. Testing PUT /api/connections - Enable deepseek and grok")
    try:
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
        
        response = requests.put(
            f"{BACKEND_URL}/connections",
            json=update_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        runner.test(
            "PUT /connections returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.text}"
        )
        
        if response.status_code == 200:
            # Verify the update was saved
            verify_response = requests.get(f"{BACKEND_URL}/connections", timeout=10)
            if verify_response.status_code == 200:
                data = verify_response.json()
                providers = data.get("providers", {})
                
                runner.test(
                    "deepseek enabled after update",
                    providers.get("deepseek", {}).get("enabled", False),
                    f"deepseek config: {providers.get('deepseek')}"
                )
                
                runner.test(
                    "grok enabled after update",
                    providers.get("grok", {}).get("enabled", False),
                    f"grok config: {providers.get('grok')}"
                )
    
    except Exception as e:
        runner.test("PUT /connections request", False, f"Error: {str(e)}")
    
    # Test 4: GET /api/models - Should now return 12 models (8 + 2 + 2)
    print("\n4. Testing GET /api/models - Should return 12 models after enabling deepseek and grok")
    try:
        response = requests.get(f"{BACKEND_URL}/models", timeout=10)
        runner.test(
            "GET /models returns 200 after update",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            models = response.json()
            
            runner.test(
                "Returns 12 models after enabling deepseek and grok",
                len(models) == 12,
                f"Found {len(models)} models"
            )
            
            # Check provider distribution
            provider_counts = {}
            for model in models:
                provider = model.get("provider")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            expected_counts = {"openai": 4, "anthropic": 2, "gemini": 2, "deepseek": 2, "grok": 2}
            for provider, expected_count in expected_counts.items():
                actual_count = provider_counts.get(provider, 0)
                runner.test(
                    f"Has {expected_count} {provider} models",
                    actual_count == expected_count,
                    f"Expected: {expected_count}, Found: {actual_count}"
                )
    
    except Exception as e:
        runner.test("GET /models after update", False, f"Error: {str(e)}")
    
    # Test 5: PUT /api/connections - Enable openai_compatible with custom models
    print("\n5. Testing PUT /api/connections - Enable openai_compatible with custom models")
    try:
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
                "openai_compatible": {
                    "enabled": True,
                    "apiKey": "test",
                    "useEmergentKey": False,
                    "baseUrl": "https://api.example.com/v1",
                    "customModels": "custom-model-1, custom-model-2"
                }
            },
            "defaultModel": "gpt-4o",
            "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
            "disabledModels": []
        }
        
        response = requests.put(
            f"{BACKEND_URL}/connections",
            json=update_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        runner.test(
            "PUT /connections with openai_compatible returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.text}"
        )
    
    except Exception as e:
        runner.test("PUT /connections with openai_compatible", False, f"Error: {str(e)}")
    
    # Test 6: GET /api/models - Should include custom models
    print("\n6. Testing GET /api/models - Should include custom models from openai_compatible")
    try:
        response = requests.get(f"{BACKEND_URL}/models", timeout=10)
        runner.test(
            "GET /models returns 200 with custom models",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            models = response.json()
            
            runner.test(
                "Returns 14 models with custom models",
                len(models) == 14,
                f"Found {len(models)} models"
            )
            
            # Check for custom models
            custom_models = [m for m in models if m.get("provider") == "openai_compatible"]
            runner.test(
                "Has 2 custom models",
                len(custom_models) == 2,
                f"Found {len(custom_models)} custom models: {[m.get('name') for m in custom_models]}"
            )
            
            # Check custom model names
            custom_names = [m.get("name") for m in custom_models]
            expected_names = ["custom-model-1", "custom-model-2"]
            for name in expected_names:
                runner.test(
                    f"Has custom model {name}",
                    name in custom_names,
                    f"Found custom models: {custom_names}"
                )
    
    except Exception as e:
        runner.test("GET /models with custom models", False, f"Error: {str(e)}")
    
    # Test 7: Clean up - Reset to default configuration
    print("\n7. Testing cleanup - Reset to default configuration")
    try:
        default_data = {
            "providers": {
                "openai": {"enabled": True, "useEmergentKey": True},
                "anthropic": {"enabled": True, "useEmergentKey": True},
                "gemini": {"enabled": True, "useEmergentKey": True},
                "deepseek": {"enabled": False},
                "qwen": {"enabled": False},
                "grok": {"enabled": False},
                "perplexity": {"enabled": False},
                "bedrock": {"enabled": False},
                "openai_compatible": {"enabled": False}
            },
            "defaultModel": "gpt-4o",
            "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
            "disabledModels": []
        }
        
        response = requests.put(
            f"{BACKEND_URL}/connections",
            json=default_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        runner.test(
            "Reset to defaults returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # Verify reset
        if response.status_code == 200:
            verify_response = requests.get(f"{BACKEND_URL}/models", timeout=10)
            if verify_response.status_code == 200:
                models = verify_response.json()
                runner.test(
                    "Back to 8 models after reset",
                    len(models) == 8,
                    f"Found {len(models)} models after reset"
                )
    
    except Exception as e:
        runner.test("Reset to defaults", False, f"Error: {str(e)}")
    
    return runner.summary()

if __name__ == "__main__":
    print("🚀 Starting Backend API Tests for Updated Provider Support")
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    success = test_connections_and_models()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)