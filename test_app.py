#!/usr/bin/env python3
"""
Test script to generate traces in the OTEL demo app
Run this after starting the containers
"""

import requests
import time
import sys
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"

def test_index():
    """Test the index endpoint"""
    print("[*] Testing GET /")
    resp = requests.get(f"{BASE_URL}/")
    print(f"    Status: {resp.status_code}")
    return resp.json()

def test_users():
    """Test the users endpoint"""
    print("[*] Testing GET /api/users")
    resp = requests.get(f"{BASE_URL}/api/users")
    print(f"    Status: {resp.status_code}, Users: {len(resp.json().get('users', []))}")
    return resp.json()

def test_process():
    """Test the process endpoint"""
    print("[*] Testing GET /api/process")
    resp = requests.get(f"{BASE_URL}/api/process")
    print(f"    Status: {resp.status_code}, Duration: {resp.json().get('duration_ms')}ms")
    return resp.json()

def test_error():
    """Test the error endpoint"""
    print("[*] Testing GET /api/error")
    try:
        resp = requests.get(f"{BASE_URL}/api/error")
        print(f"    Status: {resp.status_code} - Error traced")
    except Exception as e:
        print(f"    Error: {e}")

def test_health():
    """Test health check"""
    print("[*] Testing GET /health")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"    Status: {resp.status_code}")
    return resp.json()

def load_test(num_requests=20):
    """Generate load to create more traces"""
    print(f"\n[*] Generating {num_requests} requests for load testing...")
    
    def make_request():
        endpoint = [test_users, test_process][int(time.time()) % 2]()
        time.sleep(0.1)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        for i, future in enumerate(futures):
            try:
                future.result()
            except Exception as e:
                print(f"    Request {i+1} failed: {e}")
    
    print("[*] Load test completed")

def main():
    """Run all tests"""
    print("=" * 60)
    print("OTEL Demo App - Test Suite")
    print("=" * 60)
    
    # Check if app is running
    try:
        test_health()
    except Exception as e:
        print(f"\n[!] Error: App is not responding at {BASE_URL}")
        print("    Make sure docker-compose is running: docker-compose up -d")
        sys.exit(1)
    
    print("\n[*] Running functional tests...")
    test_index()
    test_users()
    test_process()
    test_error()
    
    print("\n[*] Running load tests...")
    load_test(30)
    
    print("\n" + "=" * 60)
    print("[✓] Tests completed!")
    print("[*] View traces at: http://localhost:16686")
    print("=" * 60)
