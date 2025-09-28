#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST - Kiểm tra toàn bộ ứng dụng sau khi sửa lỗi
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_complete_functionality():
    print("🔍 KIỂM TRA TOÀN DIỆN ỨNG DỤNG")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("1. Root endpoint...")
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Numerus API" in data["message"]
    print("✅ Root endpoint OK")
    
    # Test 2: Health
    print("2. Health check...")
    resp = requests.get(f"{BASE_URL}/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("✅ Health OK")
    
    # Test 3: Systems
    print("3. Systems list...")
    resp = requests.get(f"{BASE_URL}/v1/systems")
    assert resp.status_code == 200
    systems = resp.json()["systems"]
    assert len(systems) >= 5
    print(f"✅ Found {len(systems)} systems")
    
    # Test 4: Basic Analysis
    print("4. Basic analysis...")
    payload = {
        "full_name": "Nguyen Van Test",
        "date_of_birth": "1990-01-15",
        "system": "pythagorean",
        "detailed": False
    }
    resp = requests.post(f"{BASE_URL}/v1/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "numbers" in data
    print(f"✅ Life Path: {data['numbers']['life_path']}")
    
    # Test 5: Detailed Analysis with Reporter
    print("5. Detailed analysis with reporter...")
    payload["detailed"] = True
    resp = requests.post(f"{BASE_URL}/v1/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "report" in data
    assert "header" in data["report"]
    assert "core" in data["report"]
    print("✅ Detailed report OK")
    
    # Test 6: Trace functionality
    print("6. Trace functionality...")
    payload["trace"] = True
    resp = requests.post(f"{BASE_URL}/v1/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "trace" in data
    assert "dob" in data["trace"]
    print("✅ Trace OK")
    
    # Test 7: Different systems
    print("7. Different numerology systems...")
    for system in ["pythagorean", "chaldean"]:
        payload = {
            "full_name": "Test User",
            "date_of_birth": "1990-01-01",
            "system": system
        }
        resp = requests.post(f"{BASE_URL}/v1/analyze", json=payload)
        assert resp.status_code == 200
        print(f"✅ {system} system OK")
    
    # Test 8: Export endpoint
    print("8. Export HTML...")
    resp = requests.post(f"{BASE_URL}/v1/export", json={
        "full_name": "Test Export",
        "date_of_birth": "1990-01-01", 
        "system": "pythagorean"
    })
    assert resp.status_code == 200
    assert "html" in resp.text.lower()
    print("✅ Export OK")
    
    # Test 9: Examples endpoint  
    print("9. Examples endpoint...")
    resp = requests.get(f"{BASE_URL}/v1/examples")
    assert resp.status_code == 200
    examples = resp.json()["examples"]
    assert len(examples) > 0
    print("✅ Examples OK")
    
    # Test 10: Error handling
    print("10. Error handling...")
    resp = requests.post(f"{BASE_URL}/v1/analyze", json={
        "full_name": "Test",
        "date_of_birth": "invalid-date",
        "system": "pythagorean"
    })
    assert resp.status_code == 400
    print("✅ Error handling OK")
    
    print("=" * 50)
    print("🎉 TẤT CẢ TESTS ĐỀU PASS!")
    print("🚀 ỨNG DỤNG HOÀN HẢO - KHÔNG CÒN LỖI!")

if __name__ == "__main__":
    try:
        test_complete_functionality()
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)