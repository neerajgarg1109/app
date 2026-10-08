#!/usr/bin/env python3
"""
Round 4 Backend Testing for cardIQ
Tests confidence field, date filters, partial sessions, reminders, and regression.
"""

import requests
import json
import sys

# Base URL from frontend/.env
BASE_URL = "https://portable-monzy.preview.emergentagent.com/api"
ADMIN_TOKEN = "cardiq-admin-2025"

def print_test(name):
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print('='*80)

def print_result(passed, message):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")
    return passed

def test_confidence_field():
    """Test 1: Confidence field in POST /api/quiz/submit and GET /api/results/{id}"""
    print_test("1. Confidence field (int 35-99) in scored responses")
    
    # Submit a perfect travel profile
    payload = {
        "answers": {
            "goal": "travel",
            "spend": "high",
            "fee": "premium",
            "usage": "flights",
            "priority": "lounge",
            "international": "often",
            "credit": "excellent"
        },
        "lead": {
            "name": "R4 Conf",
            "email": "delivered@resend.dev"
        }
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=30)
        print(f"POST /api/quiz/submit status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        print(f"Response keys: {data.keys()}")
        
        # Check result_id
        if "result_id" not in data:
            print_result(False, "Missing result_id in response")
            return False
        
        result_id = data["result_id"]
        print(f"Result ID: {result_id}")
        
        # Check scored array
        if "scored" not in data or not data["scored"]:
            print_result(False, "Missing or empty scored array")
            return False
        
        scored = data["scored"]
        print(f"Number of scored cards: {len(scored)}")
        
        # Check top card
        top = scored[0]
        print(f"Top card: {top['card']['id']} (name: {top['card']['name']})")
        print(f"Top card score: {top['score']}")
        
        # Verify top card is voyager-infinite
        if top['card']['id'] != 'voyager-infinite':
            print_result(False, f"Expected voyager-infinite as top card, got {top['card']['id']}")
            return False
        
        # Check confidence field exists in all scored items
        all_have_confidence = True
        for i, item in enumerate(scored):
            if 'confidence' not in item:
                print(f"❌ Item {i} ({item['card']['id']}) missing confidence field")
                all_have_confidence = False
            else:
                conf = item['confidence']
                print(f"Card {i+1}: {item['card']['id']} - confidence: {conf}")
                
                # Verify confidence is int between 35 and 99
                if not isinstance(conf, int) or conf < 35 or conf > 99:
                    print(f"❌ Invalid confidence value: {conf} (must be int 35-99)")
                    all_have_confidence = False
        
        if not all_have_confidence:
            print_result(False, "Not all items have valid confidence field")
            return False
        
        # Check top card confidence is ~99 (>=90)
        top_confidence = top['confidence']
        if top_confidence < 90:
            print_result(False, f"Top card confidence {top_confidence} is less than 90 (expected ~99)")
            return False
        
        print_result(True, f"POST /api/quiz/submit: Top card voyager-infinite with confidence {top_confidence} (>=90)")
        
        # Now test GET /api/results/{result_id}
        print(f"\nTesting GET /api/results/{result_id}")
        resp2 = requests.get(f"{BASE_URL}/results/{result_id}", timeout=30)
        print(f"GET /api/results/{result_id} status: {resp2.status_code}")
        
        if resp2.status_code != 200:
            print_result(False, f"Expected 200, got {resp2.status_code}: {resp2.text}")
            return False
        
        data2 = resp2.json()
        
        # Check scored array has confidence
        if "scored" not in data2 or not data2["scored"]:
            print_result(False, "GET /api/results: Missing or empty scored array")
            return False
        
        scored2 = data2["scored"]
        all_have_confidence2 = True
        for i, item in enumerate(scored2):
            if 'confidence' not in item:
                print(f"❌ GET results: Item {i} missing confidence field")
                all_have_confidence2 = False
            else:
                conf = item['confidence']
                if not isinstance(conf, int) or conf < 35 or conf > 99:
                    print(f"❌ GET results: Invalid confidence value: {conf}")
                    all_have_confidence2 = False
        
        if not all_have_confidence2:
            print_result(False, "GET /api/results: Not all items have valid confidence field")
            return False
        
        print_result(True, f"GET /api/results/{result_id}: All scored items include confidence (int 35-99)")
        return True
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False


def test_date_filters():
    """Test 2: Date filters on admin endpoints"""
    print_test("2. Date filters (date_from, date_to) on admin endpoints")
    
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    
    # Test 2a: GET /api/admin/leads?date_from=2030-01-01 should return 0
    print("\n2a. GET /api/admin/leads?date_from=2030-01-01")
    try:
        resp = requests.get(f"{BASE_URL}/admin/leads?date_from=2030-01-01", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        total = data.get("total", -1)
        print(f"Total leads: {total}")
        
        if total != 0:
            print_result(False, f"Expected total=0 for future date, got {total}")
            return False
        
        print_result(True, "GET /api/admin/leads?date_from=2030-01-01 returns total=0")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 2b: GET /api/admin/insights?date_from=2030-01-01 should return empty
    print("\n2b. GET /api/admin/insights?date_from=2030-01-01")
    try:
        resp = requests.get(f"{BASE_URL}/admin/insights?date_from=2030-01-01", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        total_results = data.get("total_results", -1)
        by_card = data.get("by_card", None)
        by_goal = data.get("by_goal", None)
        
        print(f"total_results: {total_results}")
        print(f"by_card: {by_card}")
        print(f"by_goal: {by_goal}")
        
        if total_results != 0:
            print_result(False, f"Expected total_results=0, got {total_results}")
            return False
        
        if by_card != []:
            print_result(False, f"Expected by_card=[], got {by_card}")
            return False
        
        if by_goal != []:
            print_result(False, f"Expected by_goal=[], got {by_goal}")
            return False
        
        print_result(True, "GET /api/admin/insights?date_from=2030-01-01 returns total_results=0, by_card=[], by_goal=[]")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 2c: GET /api/admin/leads.csv?token=...&date_from=2030-01-01 should return only header
    print("\n2c. GET /api/admin/leads.csv?token=...&date_from=2030-01-01")
    try:
        resp = requests.get(f"{BASE_URL}/admin/leads.csv?token={ADMIN_TOKEN}&date_from=2030-01-01", timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        if "text/csv" not in resp.headers.get("Content-Type", ""):
            print_result(False, f"Expected text/csv, got {resp.headers.get('Content-Type')}")
            return False
        
        csv_content = resp.text
        lines = csv_content.strip().split('\n')
        print(f"CSV lines: {len(lines)}")
        print(f"Header: {lines[0] if lines else 'EMPTY'}")
        
        # Should have only header row, no data rows
        if len(lines) != 1:
            print_result(False, f"Expected only header row (1 line), got {len(lines)} lines")
            return False
        
        expected_header = "Name,Email,Phone,Recommended Card,Email Sent,Created At,Result ID"
        if lines[0] != expected_header:
            print_result(False, f"Header mismatch. Expected: {expected_header}, Got: {lines[0]}")
            return False
        
        print_result(True, "GET /api/admin/leads.csv?date_from=2030-01-01 returns only header row")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 2d: GET /api/admin/leads without date filter should return >= 1
    print("\n2d. GET /api/admin/leads (no date filter) should return >= 1")
    try:
        resp = requests.get(f"{BASE_URL}/admin/leads", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        total = data.get("total", 0)
        print(f"Total leads: {total}")
        
        if total < 1:
            print_result(False, f"Expected total >= 1, got {total}")
            return False
        
        print_result(True, f"GET /api/admin/leads (no filter) returns total={total} (>= 1)")
        return True
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False


def test_partial_sessions_and_reminders():
    """Test 3: Partial sessions + reminders flow"""
    print_test("3. Partial sessions + reminders flow")
    
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    partial_email = "partial-r4@resend.dev"
    
    # Test 3a: POST /api/quiz/partial
    print("\n3a. POST /api/quiz/partial (no auth required)")
    try:
        payload = {
            "name": "R4 Abandon",
            "email": partial_email,
            "answers": {"goal": "shopping"},
            "step": 1
        }
        resp = requests.post(f"{BASE_URL}/quiz/partial", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        if data.get("status") != "saved":
            print_result(False, f"Expected status='saved', got {data}")
            return False
        
        print_result(True, "POST /api/quiz/partial returns {status: 'saved'}")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 3b: GET /api/admin/insights should show incomplete_sessions >= 1
    print("\n3b. GET /api/admin/insights should show incomplete_sessions >= 1")
    try:
        resp = requests.get(f"{BASE_URL}/admin/insights", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        incomplete = data.get("incomplete_sessions", 0)
        print(f"incomplete_sessions: {incomplete}")
        
        if incomplete < 1:
            print_result(False, f"Expected incomplete_sessions >= 1, got {incomplete}")
            return False
        
        print_result(True, f"GET /api/admin/insights shows incomplete_sessions={incomplete} (>= 1)")
        incomplete_before = incomplete
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 3c: POST /api/admin/send-reminders (with auth)
    print("\n3c. POST /api/admin/send-reminders (with X-Admin-Token header)")
    try:
        resp = requests.post(f"{BASE_URL}/admin/send-reminders", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        status = data.get("status")
        reminders_sent = data.get("reminders_sent")
        pending = data.get("pending")
        
        print(f"status: {status}")
        print(f"reminders_sent: {reminders_sent}")
        print(f"pending: {pending}")
        
        if status != "success":
            print_result(False, f"Expected status='success', got {status}")
            return False
        
        if not isinstance(reminders_sent, int):
            print_result(False, f"reminders_sent should be int, got {type(reminders_sent)}")
            return False
        
        if reminders_sent < 1:
            print_result(False, f"Expected reminders_sent >= 1, got {reminders_sent}")
            return False
        
        print_result(True, f"POST /api/admin/send-reminders returns status='success', reminders_sent={reminders_sent} (>= 1)")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test without header (should return 401)
    print("\n3c-2. POST /api/admin/send-reminders without header should return 401")
    try:
        resp = requests.post(f"{BASE_URL}/admin/send-reminders", timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 401:
            print_result(False, f"Expected 401, got {resp.status_code}")
            return False
        
        print_result(True, "POST /api/admin/send-reminders without header returns 401")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 3d: Call send-reminders AGAIN (should not re-send)
    print("\n3d. POST /api/admin/send-reminders AGAIN (should not re-send same partial)")
    try:
        resp = requests.post(f"{BASE_URL}/admin/send-reminders", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        reminders_sent = data.get("reminders_sent")
        
        print(f"reminders_sent (2nd call): {reminders_sent}")
        
        # Should be 0 since the partial was already reminded
        if reminders_sent != 0:
            print_result(False, f"Expected reminders_sent=0 (already reminded), got {reminders_sent}")
            return False
        
        print_result(True, "POST /api/admin/send-reminders (2nd call) returns reminders_sent=0 (no re-send)")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 3e: Complete the partial session by submitting with same email
    print("\n3e. Complete partial session: POST /api/quiz/submit with same email")
    try:
        payload = {
            "answers": {
                "goal": "shopping",
                "spend": "mid",
                "fee": "worth",
                "usage": "online",
                "priority": "rewards",
                "international": "sometimes",
                "credit": "good"
            },
            "lead": {
                "name": "R4 Abandon",
                "email": partial_email
            }
        }
        resp = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        if "result_id" not in data:
            print_result(False, "Missing result_id in response")
            return False
        
        print_result(True, f"POST /api/quiz/submit with partial email returns 200 with result_id")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False
    
    # Test 3e-2: Check incomplete_sessions decreased
    print("\n3e-2. GET /api/admin/insights should show incomplete_sessions decreased by 1")
    try:
        resp = requests.get(f"{BASE_URL}/admin/insights", headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}: {resp.text}")
            return False
        
        data = resp.json()
        incomplete_after = data.get("incomplete_sessions", 0)
        print(f"incomplete_sessions before: {incomplete_before}")
        print(f"incomplete_sessions after: {incomplete_after}")
        
        if incomplete_after != incomplete_before - 1:
            print_result(False, f"Expected incomplete_sessions to decrease by 1 (from {incomplete_before} to {incomplete_before-1}), got {incomplete_after}")
            return False
        
        print_result(True, f"incomplete_sessions decreased from {incomplete_before} to {incomplete_after} (completed partial)")
        return True
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False


def test_regression():
    """Test 4: Regression tests"""
    print_test("4. Regression tests")
    
    all_passed = True
    
    # 4a: GET /api/cards (8 cards)
    print("\n4a. GET /api/cards should return 8 cards")
    try:
        resp = requests.get(f"{BASE_URL}/cards", timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}")
            all_passed = False
        else:
            cards = resp.json()
            print(f"Number of cards: {len(cards)}")
            
            if len(cards) != 8:
                print_result(False, f"Expected 8 cards, got {len(cards)}")
                all_passed = False
            else:
                print_result(True, "GET /api/cards returns 8 cards")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4b: POST /api/cards/compare with 2 cards
    print("\n4b. POST /api/cards/compare with 2 cards in order")
    try:
        payload = {"ids": ["voyager-infinite", "skymiles-plus"]}
        resp = requests.post(f"{BASE_URL}/cards/compare", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print_result(False, f"Expected 200, got {resp.status_code}")
            all_passed = False
        else:
            cards = resp.json()
            print(f"Number of cards returned: {len(cards)}")
            
            if len(cards) != 2:
                print_result(False, f"Expected 2 cards, got {len(cards)}")
                all_passed = False
            elif cards[0]["id"] != "voyager-infinite" or cards[1]["id"] != "skymiles-plus":
                print_result(False, f"Cards not in requested order: {[c['id'] for c in cards]}")
                all_passed = False
            else:
                print_result(True, "POST /api/cards/compare returns 2 cards in correct order")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4c: POST /api/cards/compare with empty list (should return 400)
    print("\n4c. POST /api/cards/compare with empty list should return 400")
    try:
        payload = {"ids": []}
        resp = requests.post(f"{BASE_URL}/cards/compare", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 400:
            print_result(False, f"Expected 400, got {resp.status_code}")
            all_passed = False
        else:
            print_result(True, "POST /api/cards/compare with empty list returns 400")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4d: POST /api/results/{result_id}/email (need a valid result_id first)
    print("\n4d. POST /api/results/{result_id}/email should return 200")
    try:
        # First create a result
        payload = {
            "answers": {
                "goal": "travel",
                "spend": "high",
                "fee": "premium",
                "usage": "flights",
                "priority": "lounge",
                "international": "often",
                "credit": "excellent"
            },
            "lead": {
                "name": "Regression Test",
                "email": "delivered@resend.dev"
            }
        }
        resp = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=30)
        
        if resp.status_code != 200:
            print_result(False, f"Failed to create result: {resp.status_code}")
            all_passed = False
        else:
            result_id = resp.json()["result_id"]
            print(f"Created result_id: {result_id}")
            
            # Now test email endpoint
            resp2 = requests.post(f"{BASE_URL}/results/{result_id}/email", timeout=30)
            print(f"POST /api/results/{result_id}/email status: {resp2.status_code}")
            
            if resp2.status_code != 200:
                print_result(False, f"Expected 200, got {resp2.status_code}: {resp2.text}")
                all_passed = False
            else:
                data = resp2.json()
                print(f"Response: {data}")
                
                if data.get("status") != "success":
                    print_result(False, f"Expected status='success', got {data.get('status')}")
                    all_passed = False
                else:
                    print_result(True, f"POST /api/results/{{result_id}}/email returns 200 with status='success'")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4e: GET /api/admin/leads.csv with wrong token (should return 401)
    print("\n4e. GET /api/admin/leads.csv with wrong token should return 401")
    try:
        resp = requests.get(f"{BASE_URL}/admin/leads.csv?token=wrong-token", timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 401:
            print_result(False, f"Expected 401, got {resp.status_code}")
            all_passed = False
        else:
            print_result(True, "GET /api/admin/leads.csv with wrong token returns 401")
        
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed


def main():
    print("="*80)
    print("cardIQ Backend Testing - Round 4")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Token: {ADMIN_TOKEN}")
    
    results = {}
    
    # Run all tests
    results["Test 1: Confidence field"] = test_confidence_field()
    results["Test 2: Date filters"] = test_date_filters()
    results["Test 3: Partial sessions + reminders"] = test_partial_sessions_and_reminders()
    results["Test 4: Regression"] = test_regression()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
