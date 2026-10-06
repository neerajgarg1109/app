"""
Comprehensive backend API tests for cardIQ - Round 3
Tests all /api endpoints with the external base URL
Includes Round 3 features: welcome email on submit, CSV export, admin insights
"""
import requests
import json
from typing import Dict, Any, Optional

# Base URL from frontend/.env
BASE_URL = "https://portable-monzy.preview.emergentagent.com/api"
ADMIN_TOKEN = "cardiq-admin-2025"

def print_test_header(test_name: str):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(success: bool, message: str, details: Any = None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {json.dumps(details, indent=2, default=str)}")

def test_quiz_submit_with_welcome_email():
    """Test 1: POST /api/quiz/submit - with welcome email (best-effort, non-fatal)"""
    print_test_header("POST /api/quiz/submit - Welcome email on submit")
    
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
            "name": "Welcome Tester",
            "email": "delivered@resend.dev"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return None
        
        result = response.json()
        
        # Check response structure
        if "result_id" not in result or "scored" not in result:
            print_result(False, "Missing result_id or scored in response", result)
            return None
        
        result_id = result["result_id"]
        scored = result["scored"]
        
        print(f"Result ID: {result_id}")
        print(f"Number of scored cards: {len(scored)}")
        
        if not scored:
            print_result(False, "Scored list is empty")
            return None
        
        # Check top card is voyager-infinite
        top_card_id = scored[0]["card"]["id"]
        top_score = scored[0]["score"]
        
        print(f"Top card: {top_card_id} (score: {top_score})")
        
        if top_card_id != "voyager-infinite":
            print_result(False, f"Expected voyager-infinite as top card, got {top_card_id}")
            return None
        
        print_result(True, f"Quiz submit returned 200 with result_id and scored array. Top card: voyager-infinite (score: {top_score}). Welcome email sent best-effort (non-blocking).")
        return result_id
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return None

def test_admin_leads_csv_query_param():
    """Test 2a: GET /api/admin/leads.csv with query param ?token="""
    print_test_header("GET /api/admin/leads.csv - Query param auth")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/leads.csv?token={ADMIN_TOKEN}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            print_result(False, f"Expected Content-Type text/csv, got {content_type}")
            return False
        
        # Check Content-Disposition
        content_disposition = response.headers.get("Content-Disposition", "")
        if "attachment" not in content_disposition or "cardiq-leads.csv" not in content_disposition:
            print_result(False, f"Expected Content-Disposition with attachment and filename, got {content_disposition}")
            return False
        
        # Check CSV content
        csv_content = response.text
        lines = [line.strip() for line in csv_content.strip().split("\n")]
        
        if not lines:
            print_result(False, "CSV content is empty")
            return False
        
        # Check header row
        expected_header = "Name,Email,Phone,Recommended Card,Email Sent,Created At,Result ID"
        actual_header = lines[0].strip()
        
        if actual_header != expected_header:
            print_result(False, f"CSV header mismatch.\nExpected: {expected_header}\nActual: {actual_header}")
            return False
        
        print(f"CSV rows: {len(lines)} (including header)")
        print(f"Header: {actual_header}")
        if len(lines) > 1:
            print(f"Sample row: {lines[1][:100]}...")
        
        print_result(True, f"CSV export with query param working. Content-Type: text/csv, Content-Disposition: attachment, Header row correct.")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_admin_leads_csv_header_auth():
    """Test 2b: GET /api/admin/leads.csv with header X-Admin-Token"""
    print_test_header("GET /api/admin/leads.csv - Header auth")
    
    try:
        headers = {"X-Admin-Token": ADMIN_TOKEN}
        response = requests.get(f"{BASE_URL}/admin/leads.csv", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            print_result(False, f"Expected Content-Type text/csv, got {content_type}")
            return False
        
        # Check CSV content
        csv_content = response.text
        lines = [line.strip() for line in csv_content.strip().split("\n")]
        
        if not lines:
            print_result(False, "CSV content is empty")
            return False
        
        expected_header = "Name,Email,Phone,Recommended Card,Email Sent,Created At,Result ID"
        actual_header = lines[0].strip()
        
        if actual_header != expected_header:
            print_result(False, f"CSV header mismatch.\nExpected: {expected_header}\nActual: {actual_header}")
            return False
        
        print_result(True, f"CSV export with header auth working. {len(lines)} rows (including header).")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_admin_leads_csv_wrong_token():
    """Test 2c: GET /api/admin/leads.csv with wrong token (should return 401)"""
    print_test_header("GET /api/admin/leads.csv - Wrong token")
    
    all_passed = True
    
    # Test with wrong query param
    try:
        response = requests.get(f"{BASE_URL}/admin/leads.csv?token=nope", timeout=10)
        print(f"Status Code with wrong query token: {response.status_code}")
        
        if response.status_code != 401:
            print_result(False, f"Expected 401 with wrong query token, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 401 with wrong query token")
    except Exception as e:
        print_result(False, f"Exception with wrong query token: {str(e)}")
        all_passed = False
    
    # Test with no token
    try:
        response = requests.get(f"{BASE_URL}/admin/leads.csv", timeout=10)
        print(f"Status Code with no token: {response.status_code}")
        
        if response.status_code != 401:
            print_result(False, f"Expected 401 with no token, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 401 with no token")
    except Exception as e:
        print_result(False, f"Exception with no token: {str(e)}")
        all_passed = False
    
    return all_passed

def test_admin_insights():
    """Test 3: GET /api/admin/insights - admin analytics endpoint"""
    print_test_header("GET /api/admin/insights - Admin analytics")
    
    all_passed = True
    
    # Test 3a: With correct admin token
    try:
        headers = {"X-Admin-Token": ADMIN_TOKEN}
        response = requests.get(f"{BASE_URL}/admin/insights", headers=headers, timeout=10)
        print(f"Status Code with correct token: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200 with correct token, got {response.status_code}", response.text)
            all_passed = False
        else:
            result = response.json()
            
            # Check required keys
            required_keys = ["total_results", "emails_sent", "by_card", "by_goal"]
            missing_keys = [k for k in required_keys if k not in result]
            
            if missing_keys:
                print_result(False, f"Missing required keys: {missing_keys}", result)
                all_passed = False
            else:
                total_results = result["total_results"]
                emails_sent = result["emails_sent"]
                by_card = result["by_card"]
                by_goal = result["by_goal"]
                
                print(f"Total results: {total_results}")
                print(f"Emails sent: {emails_sent}")
                print(f"By card entries: {len(by_card)}")
                print(f"By goal entries: {len(by_goal)}")
                
                # Check types
                if not isinstance(total_results, int):
                    print_result(False, f"total_results should be int, got {type(total_results)}")
                    all_passed = False
                
                if not isinstance(emails_sent, int):
                    print_result(False, f"emails_sent should be int, got {type(emails_sent)}")
                    all_passed = False
                
                if not isinstance(by_card, list):
                    print_result(False, f"by_card should be list, got {type(by_card)}")
                    all_passed = False
                
                if not isinstance(by_goal, list):
                    print_result(False, f"by_goal should be list, got {type(by_goal)}")
                    all_passed = False
                
                # Check by_card structure and sorting
                if by_card:
                    first_card = by_card[0]
                    required_fields = ["label", "count", "pct"]
                    missing_fields = [f for f in required_fields if f not in first_card]
                    
                    if missing_fields:
                        print_result(False, f"by_card entry missing fields: {missing_fields}", first_card)
                        all_passed = False
                    else:
                        # Check pct is 0-100 int
                        if not isinstance(first_card["pct"], int) or first_card["pct"] < 0 or first_card["pct"] > 100:
                            print_result(False, f"pct should be 0-100 int, got {first_card['pct']}")
                            all_passed = False
                        
                        # Check sorting (descending by count)
                        counts = [item["count"] for item in by_card]
                        if counts != sorted(counts, reverse=True):
                            print_result(False, f"by_card not sorted by count desc: {counts}")
                            all_passed = False
                        
                        print(f"Sample by_card: {first_card}")
                
                # Check by_goal structure and sorting
                if by_goal:
                    first_goal = by_goal[0]
                    required_fields = ["label", "count", "pct"]
                    missing_fields = [f for f in required_fields if f not in first_goal]
                    
                    if missing_fields:
                        print_result(False, f"by_goal entry missing fields: {missing_fields}", first_goal)
                        all_passed = False
                    else:
                        # Check pct is 0-100 int
                        if not isinstance(first_goal["pct"], int) or first_goal["pct"] < 0 or first_goal["pct"] > 100:
                            print_result(False, f"pct should be 0-100 int, got {first_goal['pct']}")
                            all_passed = False
                        
                        # Check sorting (descending by count)
                        counts = [item["count"] for item in by_goal]
                        if counts != sorted(counts, reverse=True):
                            print_result(False, f"by_goal not sorted by count desc: {counts}")
                            all_passed = False
                        
                        print(f"Sample by_goal: {first_goal}")
                
                if all_passed:
                    print_result(True, f"Admin insights working correctly. total_results={total_results}, emails_sent={emails_sent}, by_card and by_goal sorted desc with correct structure.")
                
    except Exception as e:
        print_result(False, f"Exception with correct token: {str(e)}")
        all_passed = False
    
    # Test 3b: Without admin token (should return 401)
    try:
        response = requests.get(f"{BASE_URL}/admin/insights", timeout=10)
        print(f"Status Code without token: {response.status_code}")
        
        if response.status_code != 401:
            print_result(False, f"Expected 401 without token, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 401 without admin token")
    except Exception as e:
        print_result(False, f"Exception without token: {str(e)}")
        all_passed = False
    
    # Test 3c: With wrong admin token (should return 401)
    try:
        headers = {"X-Admin-Token": "wrong-token"}
        response = requests.get(f"{BASE_URL}/admin/insights", headers=headers, timeout=10)
        print(f"Status Code with wrong token: {response.status_code}")
        
        if response.status_code != 401:
            print_result(False, f"Expected 401 with wrong token, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 401 with wrong admin token")
    except Exception as e:
        print_result(False, f"Exception with wrong token: {str(e)}")
        all_passed = False
    
    return all_passed

def test_regression_get_cards():
    """Regression: GET /api/cards"""
    print_test_header("REGRESSION: GET /api/cards")
    
    try:
        response = requests.get(f"{BASE_URL}/cards", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        cards = response.json()
        
        if len(cards) != 8:
            print_result(False, f"Expected 8 cards, got {len(cards)}")
            return False
        
        # Check all cards have required fields
        for card in cards:
            if "applyUrl" not in card or "creditReq" not in card:
                print_result(False, f"Card {card.get('id')} missing applyUrl or creditReq")
                return False
        
        print_result(True, f"GET /api/cards working. 8 cards with applyUrl and creditReq.")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_regression_get_result(result_id: Optional[str]):
    """Regression: GET /api/results/{result_id}"""
    print_test_header("REGRESSION: GET /api/results/{result_id}")
    
    if not result_id:
        print_result(False, "No result_id provided")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/results/{result_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        
        if "result_id" not in result or "scored" not in result:
            print_result(False, "Missing result_id or scored in response")
            return False
        
        print_result(True, f"GET /api/results/{{result_id}} working. Retrieved {len(result['scored'])} scored cards.")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_regression_email_result(result_id: Optional[str]):
    """Regression: POST /api/results/{result_id}/email"""
    print_test_header("REGRESSION: POST /api/results/{result_id}/email")
    
    if not result_id:
        print_result(False, "No result_id provided")
        return False
    
    try:
        response = requests.post(f"{BASE_URL}/results/{result_id}/email", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        
        if "status" not in result or result["status"] != "success":
            print_result(False, f"Expected status 'success', got {result.get('status')}")
            return False
        
        print_result(True, f"POST /api/results/{{result_id}}/email working. Email sent successfully.")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_regression_cards_compare():
    """Regression: POST /api/cards/compare"""
    print_test_header("REGRESSION: POST /api/cards/compare")
    
    all_passed = True
    
    # Test with 2 cards
    payload = {"ids": ["voyager-infinite", "skymiles-plus"]}
    
    try:
        response = requests.post(f"{BASE_URL}/cards/compare", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            all_passed = False
        else:
            cards = response.json()
            
            if len(cards) != 2:
                print_result(False, f"Expected 2 cards, got {len(cards)}")
                all_passed = False
            else:
                card_ids = [c["id"] for c in cards]
                if card_ids != ["voyager-infinite", "skymiles-plus"]:
                    print_result(False, f"Order not preserved. Got {card_ids}")
                    all_passed = False
                else:
                    print_result(True, f"POST /api/cards/compare working. 2 cards in correct order.")
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        all_passed = False
    
    # Test with empty ids (should return 400)
    payload_empty = {"ids": []}
    
    try:
        response = requests.post(f"{BASE_URL}/cards/compare", json=payload_empty, timeout=10)
        print(f"Status Code for empty ids: {response.status_code}")
        
        if response.status_code != 400:
            print_result(False, f"Expected 400 for empty ids, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 400 for empty ids")
    except Exception as e:
        print_result(False, f"Exception for empty ids: {str(e)}")
        all_passed = False
    
    return all_passed

def test_regression_admin_leads():
    """Regression: GET /api/admin/leads"""
    print_test_header("REGRESSION: GET /api/admin/leads")
    
    try:
        headers = {"X-Admin-Token": ADMIN_TOKEN}
        response = requests.get(f"{BASE_URL}/admin/leads", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        
        if "total" not in result or "leads" not in result:
            print_result(False, "Missing 'total' or 'leads' in response")
            return False
        
        print_result(True, f"GET /api/admin/leads working. {result['total']} leads.")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def main():
    """Run all backend tests for Round 3"""
    print("\n" + "="*80)
    print("CARDIQ BACKEND API TEST SUITE - ROUND 3")
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    results = {}
    result_id = None
    
    # Round 3 Tests
    print("\n" + "="*80)
    print("ROUND 3 NEW FEATURES")
    print("="*80)
    
    # Test 1: POST /api/quiz/submit with welcome email
    result_id = test_quiz_submit_with_welcome_email()
    results["1. POST /api/quiz/submit (welcome email)"] = result_id is not None
    
    # Test 2a: GET /api/admin/leads.csv with query param
    results["2a. GET /api/admin/leads.csv (query param)"] = test_admin_leads_csv_query_param()
    
    # Test 2b: GET /api/admin/leads.csv with header
    results["2b. GET /api/admin/leads.csv (header auth)"] = test_admin_leads_csv_header_auth()
    
    # Test 2c: GET /api/admin/leads.csv with wrong/no token
    results["2c. GET /api/admin/leads.csv (401 for wrong/no token)"] = test_admin_leads_csv_wrong_token()
    
    # Test 3: GET /api/admin/insights
    results["3. GET /api/admin/insights (analytics)"] = test_admin_insights()
    
    # Regression Tests
    print("\n" + "="*80)
    print("REGRESSION TESTS")
    print("="*80)
    
    results["4. REGRESSION: GET /api/cards"] = test_regression_get_cards()
    results["5. REGRESSION: GET /api/results/{result_id}"] = test_regression_get_result(result_id)
    results["6. REGRESSION: POST /api/results/{result_id}/email"] = test_regression_email_result(result_id)
    results["7. REGRESSION: POST /api/cards/compare"] = test_regression_cards_compare()
    results["8. REGRESSION: GET /api/admin/leads"] = test_regression_admin_leads()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY - ROUND 3")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
