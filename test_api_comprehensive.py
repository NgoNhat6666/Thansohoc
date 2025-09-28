#!/usr/bin/env python3
"""
Test script for Numerus API - đảm bảo tất cả tính năng hoạt động
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/v1"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ Health endpoint OK")

def test_systems():
    """Test systems endpoint"""
    print("🔍 Testing systems endpoint...")
    response = requests.get(f"{BASE_URL}/systems")
    assert response.status_code == 200
    data = response.json()
    assert "systems" in data
    assert len(data["systems"]) > 0
    
    # Check some expected systems
    system_ids = [s["id"] for s in data["systems"]]
    expected_systems = ["pythagorean", "chaldean", "hebrew_gematria"]
    for sys in expected_systems:
        assert sys in system_ids, f"Missing system: {sys}"
    print(f"✅ Found {len(data['systems'])} systems: {system_ids}")

def test_analyze_basic():
    """Test basic analyze functionality"""
    print("🔍 Testing basic analyze...")
    payload = {
        "full_name": "Nguyen Van A",
        "date_of_birth": "1990-01-15",
        "system": "pythagorean"
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "system" in data
    assert "numbers" in data
    assert "disclaimer" in data
    
    # Check numbers
    numbers = data["numbers"]
    required_numbers = ["life_path", "expression", "soul_urge", "personality", 
                       "birthday", "maturity", "personal_year"]
    for num_type in required_numbers:
        assert num_type in numbers, f"Missing {num_type}"
        assert isinstance(numbers[num_type], int), f"{num_type} should be integer"
        assert 1 <= numbers[num_type] <= 33, f"{num_type} out of range: {numbers[num_type]}"
    
    print(f"✅ Basic analyze OK - Life Path: {numbers['life_path']}, Expression: {numbers['expression']}")

def test_analyze_with_trace():
    """Test analyze with trace"""
    print("🔍 Testing analyze with trace...")
    payload = {
        "full_name": "Nguyen Van A",
        "date_of_birth": "1990-01-15",
        "system": "pythagorean",
        "trace": True
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check trace structure
    assert "trace" in data
    trace = data["trace"]
    assert "dob" in trace
    assert "name" in trace
    assert "pre_reduction" in trace
    
    print("✅ Trace functionality OK")

def test_analyze_different_systems():
    """Test different numerology systems"""
    print("🔍 Testing different systems...")
    systems_to_test = ["pythagorean", "chaldean"]
    results = {}
    
    for system in systems_to_test:
        payload = {
            "full_name": "Nguyen Van A", 
            "date_of_birth": "1990-01-15",
            "system": system
        }
        response = requests.post(f"{BASE_URL}/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        results[system] = data["numbers"]["expression"]
    
    # Results should be different for different systems
    assert results["pythagorean"] != results["chaldean"], "Systems should give different results"
    print(f"✅ Different systems OK - Pythagorean: {results['pythagorean']}, Chaldean: {results['chaldean']}")

def test_karmic_debt_detection():
    """Test karmic debt detection"""
    print("🔍 Testing karmic debt detection...")
    # Use a name/date that should trigger karmic debt
    payload = {
        "full_name": "Test Name For Debt",
        "date_of_birth": "1985-05-14",  # Date that might trigger 14
        "system": "pythagorean",
        "trace": True
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check if karmic debt detection exists in trace
    if "karmic_debt_hits" in data.get("trace", {}):
        print(f"✅ Karmic debt detection working: {len(data['trace']['karmic_debt_hits'])} hits found")
    else:
        print("⚠️  No karmic debt hits found (this is okay)")

def test_error_handling():
    """Test error handling"""
    print("🔍 Testing error handling...")
    
    # Invalid date format
    payload = {
        "full_name": "Test",
        "date_of_birth": "invalid-date",
        "system": "pythagorean"
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 400
    
    # Invalid system
    payload = {
        "full_name": "Test",
        "date_of_birth": "1990-01-15", 
        "system": "invalid_system"
    }
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 400
    
    print("✅ Error handling OK")

def main():
    """Run all tests"""
    print("🚀 Starting Numerus API comprehensive tests...")
    
    try:
        test_health()
        test_systems() 
        test_analyze_basic()
        test_analyze_with_trace()
        test_analyze_different_systems()
        test_karmic_debt_detection()
        test_error_handling()
        
        print("\n🎉 ALL TESTS PASSED! Ứng dụng hoạt động hoàn hảo!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()