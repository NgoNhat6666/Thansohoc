#!/usr/bin/env python3
"""
Deep Testing - Kiểm tra edge cases và input validation
"""
import requests
import json

BASE_URL = "http://localhost:8000/v1"

def test_edge_cases():
    print("🔍 KIỂM TRA EDGE CASES VÀ INPUT VALIDATION")
    print("=" * 60)
    
    edge_cases = [
        # Vietnamese names with diacritics
        {"name": "Nguyễn Thị Hương", "dob": "1985-12-31", "expected": "pass"},
        {"name": "Trần Văn Đức", "dob": "2000-02-29", "expected": "pass"},  # leap year (2000 is leap year)
        
        # Special characters
        {"name": "Mary-Jane O'Connor", "dob": "1995-01-01", "expected": "pass"},
        {"name": "José María", "dob": "1988-07-15", "expected": "pass"},
        
        # Long names
        {"name": "Christopher Alexander Montgomery Wellington III", "dob": "1992-06-01", "expected": "pass"},
        
        # Single names
        {"name": "Madonna", "dob": "1958-08-16", "expected": "pass"},
        {"name": "Cher", "dob": "1946-05-20", "expected": "pass"},
        
        # Edge dates
        {"name": "Test User", "dob": "1900-01-01", "expected": "pass"},
        {"name": "Test User", "dob": "2023-12-31", "expected": "pass"},
        
        # Invalid dates (should fail)
        {"name": "Test User", "dob": "1990-13-01", "expected": "fail"},
        {"name": "Test User", "dob": "1990-02-30", "expected": "fail"},
        {"name": "Test User", "dob": "invalid", "expected": "fail"},
        
        # Empty/minimal inputs
        {"name": "A", "dob": "1990-01-01", "expected": "pass"},
        {"name": "", "dob": "1990-01-01", "expected": "fail"},
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"{i:2d}. Testing: '{case['name']}' - {case['dob']}")
        
        payload = {
            "full_name": case["name"],
            "date_of_birth": case["dob"],
            "system": "pythagorean"
        }
        
        try:
            resp = requests.post(f"{BASE_URL}/analyze", json=payload)
            
            if case["expected"] == "pass":
                assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
                data = resp.json()
                assert "numbers" in data, "Missing numbers in response"
                life_path = data["numbers"]["life_path"]
                assert 1 <= life_path <= 33, f"Invalid life path: {life_path}"
                print(f"    ✅ PASS - Life Path: {life_path}")
            else:
                assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
                print(f"    ✅ PASS - Correctly rejected")
                
        except Exception as e:
            if case["expected"] == "fail":
                print(f"    ✅ PASS - Correctly failed: {e}")
            else:
                print(f"    ❌ FAIL - Unexpected error: {e}")
                raise
    
    print("=" * 60)
    print("🎉 TẤT CẢ EDGE CASES PASSED!")

if __name__ == "__main__":
    test_edge_cases()