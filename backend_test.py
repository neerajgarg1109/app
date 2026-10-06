"""
Comprehensive backend API tests for cardIQ
Tests all /api endpoints with the external base URL
"""
import requests
import json
from typing import Dict, Any

# Base URL from frontend/.env
BASE_URL = "https://portable-monzy.preview.emergentagent.com/api"

def print_test_header(test_name: str):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(success: bool, message: str, details: Any = None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {json.dumps(details, indent=2)}")

def test_get_cards():
    """Test 1: GET /api/cards - should return 8 cards with expected fields"""
    print_test_header("GET /api/cards - Card catalog")
    
    try:
        response = requests.get(f"{BASE_URL}/cards", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        cards = response.json()
        print(f"Received {len(cards)} cards")
        
        # Check we have exactly 8 cards
        if len(cards) != 8:
            print_result(False, f"Expected 8 cards, got {len(cards)}")
            return False
        
        # Check first card has all required fields
        required_fields = ["id", "name", "network", "palette", "accent", "annualFee", 
                          "rewardLine", "highlights", "bestFor", "feeType", "minSpend", "rating"]
        
        first_card = cards[0]
        missing_fields = [f for f in required_fields if f not in first_card]
        
        if missing_fields:
            print_result(False, f"Missing fields in card: {missing_fields}", first_card)
            return False
        
        # Check palette is array of 2 colors
        if not isinstance(first_card["palette"], list) or len(first_card["palette"]) != 2:
            print_result(False, "Palette should be array of 2 colors", first_card["palette"])
            return False
        
        # Check highlights and bestFor are arrays
        if not isinstance(first_card["highlights"], list):
            print_result(False, "highlights should be an array")
            return False
        
        if not isinstance(first_card["bestFor"], list):
            print_result(False, "bestFor should be an array")
            return False
        
        print_result(True, "All 8 cards returned with correct structure")
        print(f"Sample card IDs: {[c['id'] for c in cards[:3]]}")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_get_card_by_id():
    """Test 2: GET /api/cards/{id} - test valid and invalid card IDs"""
    print_test_header("GET /api/cards/{id} - Single card lookup")
    
    all_passed = True
    
    # Test valid card ID
    try:
        response = requests.get(f"{BASE_URL}/cards/voyager-infinite", timeout=10)
        print(f"Status Code for voyager-infinite: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200 for valid card, got {response.status_code}")
            all_passed = False
        else:
            card = response.json()
            if card.get("id") != "voyager-infinite":
                print_result(False, f"Expected voyager-infinite, got {card.get('id')}")
                all_passed = False
            else:
                print_result(True, f"Successfully retrieved card: {card.get('name')}")
    except Exception as e:
        print_result(False, f"Exception for valid card: {str(e)}")
        all_passed = False
    
    # Test invalid card ID (should return 404)
    try:
        response = requests.get(f"{BASE_URL}/cards/does-not-exist", timeout=10)
        print(f"Status Code for does-not-exist: {response.status_code}")
        
        if response.status_code != 404:
            print_result(False, f"Expected 404 for invalid card, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 404 for non-existent card")
    except Exception as e:
        print_result(False, f"Exception for invalid card: {str(e)}")
        all_passed = False
    
    return all_passed

def test_quiz_submit_travel_profile():
    """Test 3a: POST /api/quiz/submit - travel profile expecting voyager-infinite as top"""
    print_test_header("POST /api/quiz/submit - Travel profile")
    
    payload = {
        "answers": {
            "goal": "travel",
            "spend": "high",
            "fee": "premium",
            "usage": "flights",
            "priority": "lounge"
        },
        "lead": {
            "name": "Test User",
            "email": "delivered@resend.dev",
            "phone": "+910000000000"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=10)
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
        
        # Check scored is not empty
        if not scored:
            print_result(False, "Scored list is empty")
            return None
        
        # Check each scored item has card, score, reasons
        first_scored = scored[0]
        if "card" not in first_scored or "score" not in first_scored or "reasons" not in first_scored:
            print_result(False, "Scored item missing required fields", first_scored)
            return None
        
        # Check top card is voyager-infinite
        top_card_id = first_scored["card"]["id"]
        top_score = first_scored["score"]
        
        print(f"Top card: {top_card_id} (score: {top_score})")
        print(f"Top 3 cards: {[(s['card']['id'], s['score']) for s in scored[:3]]}")
        
        if top_card_id != "voyager-infinite":
            print_result(False, f"Expected voyager-infinite as top card, got {top_card_id}")
            return None
        
        # Check scores are sorted descending
        scores = [s["score"] for s in scored]
        if scores != sorted(scores, reverse=True):
            print_result(False, "Scores are not sorted in descending order", scores)
            return None
        
        print_result(True, f"Travel profile correctly ranked voyager-infinite as top card")
        return result_id
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return None

def test_quiz_submit_shopping_profile():
    """Test 3b: POST /api/quiz/submit - shopping profile"""
    print_test_header("POST /api/quiz/submit - Shopping profile")
    
    payload = {
        "answers": {
            "goal": "shopping",
            "spend": "mid",
            "fee": "worth",
            "usage": "online",
            "priority": "rewards"
        },
        "lead": {
            "name": "Shop User",
            "email": "delivered@resend.dev"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        scored = result.get("scored", [])
        
        if not scored:
            print_result(False, "Scored list is empty")
            return False
        
        top_card_id = scored[0]["card"]["id"]
        print(f"Top card for shopping profile: {top_card_id}")
        print(f"Top 3 cards: {[(s['card']['id'], s['score']) for s in scored[:3]]}")
        
        # Top card should be one of the shopping/online/rewards cards
        expected_cards = ["metrocash-rewards", "prime-rewards"]
        if top_card_id not in expected_cards:
            print_result(False, f"Expected top card to be one of {expected_cards}, got {top_card_id}")
            return False
        
        print_result(True, f"Shopping profile correctly ranked {top_card_id} as top card")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_quiz_submit_validation():
    """Test 3c: POST /api/quiz/submit - validation errors"""
    print_test_header("POST /api/quiz/submit - Validation")
    
    all_passed = True
    
    # Test missing email
    payload_no_email = {
        "answers": {"goal": "travel"},
        "lead": {"name": "Test"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=payload_no_email, timeout=10)
        print(f"Status Code for missing email: {response.status_code}")
        
        if response.status_code != 422:
            print_result(False, f"Expected 422 for missing email, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 422 for missing email")
    except Exception as e:
        print_result(False, f"Exception for missing email: {str(e)}")
        all_passed = False
    
    # Test invalid email
    payload_invalid_email = {
        "answers": {"goal": "travel"},
        "lead": {"name": "Test", "email": "not-an-email"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=payload_invalid_email, timeout=10)
        print(f"Status Code for invalid email: {response.status_code}")
        
        if response.status_code != 422:
            print_result(False, f"Expected 422 for invalid email, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 422 for invalid email")
    except Exception as e:
        print_result(False, f"Exception for invalid email: {str(e)}")
        all_passed = False
    
    return all_passed

def test_get_result(result_id: str):
    """Test 4: GET /api/results/{result_id} - fetch stored result"""
    print_test_header("GET /api/results/{result_id} - Fetch result")
    
    if not result_id:
        print_result(False, "No result_id provided (previous test may have failed)")
        return False
    
    try:
        # Test valid result_id
        response = requests.get(f"{BASE_URL}/results/{result_id}", timeout=10)
        print(f"Status Code for valid result_id: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        
        if "result_id" not in result or "scored" not in result:
            print_result(False, "Missing result_id or scored in response", result)
            return False
        
        print(f"Retrieved result with {len(result['scored'])} scored cards")
        print_result(True, "Successfully retrieved stored result")
        
        # Test invalid result_id (should return 404)
        response = requests.get(f"{BASE_URL}/results/does-not-exist-uuid", timeout=10)
        print(f"Status Code for invalid result_id: {response.status_code}")
        
        if response.status_code != 404:
            print_result(False, f"Expected 404 for invalid result_id, got {response.status_code}")
            return False
        
        print_result(True, "Correctly returned 404 for non-existent result_id")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_cards_compare():
    """Test 5: POST /api/cards/compare - compare multiple cards"""
    print_test_header("POST /api/cards/compare - Card comparison")
    
    all_passed = True
    
    # Test with 3 specific cards in order
    payload = {
        "ids": ["voyager-infinite", "skymiles-plus", "metrocash-rewards"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cards/compare", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            all_passed = False
        else:
            cards = response.json()
            
            if len(cards) != 3:
                print_result(False, f"Expected 3 cards, got {len(cards)}")
                all_passed = False
            else:
                # Check order is preserved
                card_ids = [c["id"] for c in cards]
                expected_order = ["voyager-infinite", "skymiles-plus", "metrocash-rewards"]
                
                if card_ids != expected_order:
                    print_result(False, f"Order not preserved. Expected {expected_order}, got {card_ids}")
                    all_passed = False
                else:
                    print_result(True, f"Cards returned in correct order: {card_ids}")
    except Exception as e:
        print_result(False, f"Exception for valid compare: {str(e)}")
        all_passed = False
    
    # Test with empty ids list (should return 400)
    payload_empty = {"ids": []}
    
    try:
        response = requests.post(f"{BASE_URL}/cards/compare", json=payload_empty, timeout=10)
        print(f"Status Code for empty ids: {response.status_code}")
        
        if response.status_code != 400:
            print_result(False, f"Expected 400 for empty ids, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 400 for empty ids list")
    except Exception as e:
        print_result(False, f"Exception for empty ids: {str(e)}")
        all_passed = False
    
    return all_passed

def test_email_result(result_id: str):
    """Test 6: POST /api/results/{result_id}/email - send email via Resend"""
    print_test_header("POST /api/results/{result_id}/email - Email recommendation")
    
    if not result_id:
        print_result(False, "No result_id provided (previous test may have failed)")
        return False
    
    try:
        # Test valid result_id
        response = requests.post(f"{BASE_URL}/results/{result_id}/email", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200, got {response.status_code}", response.text)
            return False
        
        result = response.json()
        
        # Check response structure
        required_fields = ["status", "email_id", "sent_to"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print_result(False, f"Missing fields in response: {missing_fields}", result)
            return False
        
        if result["status"] != "success":
            print_result(False, f"Expected status 'success', got {result['status']}")
            return False
        
        if result["sent_to"] != "delivered@resend.dev":
            print_result(False, f"Expected sent_to 'delivered@resend.dev', got {result['sent_to']}")
            return False
        
        print(f"Email ID: {result['email_id']}")
        print(f"Sent to: {result['sent_to']}")
        print_result(True, "Email sent successfully via Emergent managed Resend")
        
        # Test invalid result_id (should return 404)
        response = requests.post(f"{BASE_URL}/results/does-not-exist-uuid/email", timeout=10)
        print(f"Status Code for invalid result_id: {response.status_code}")
        
        if response.status_code != 404:
            print_result(False, f"Expected 404 for invalid result_id, got {response.status_code}")
            return False
        
        print_result(True, "Correctly returned 404 for non-existent result_id")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("\n" + "="*80)
    print("CARDIQ BACKEND API TEST SUITE")
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    results = {}
    result_id = None
    
    # Test 1: GET /api/cards
    results["GET /api/cards"] = test_get_cards()
    
    # Test 2: GET /api/cards/{id}
    results["GET /api/cards/{id}"] = test_get_card_by_id()
    
    # Test 3a: POST /api/quiz/submit - travel profile
    result_id = test_quiz_submit_travel_profile()
    results["POST /api/quiz/submit (travel)"] = result_id is not None
    
    # Test 3b: POST /api/quiz/submit - shopping profile
    results["POST /api/quiz/submit (shopping)"] = test_quiz_submit_shopping_profile()
    
    # Test 3c: POST /api/quiz/submit - validation
    results["POST /api/quiz/submit (validation)"] = test_quiz_submit_validation()
    
    # Test 4: GET /api/results/{result_id}
    results["GET /api/results/{result_id}"] = test_get_result(result_id)
    
    # Test 5: POST /api/cards/compare
    results["POST /api/cards/compare"] = test_cards_compare()
    
    # Test 6: POST /api/results/{result_id}/email
    results["POST /api/results/{result_id}/email"] = test_email_result(result_id)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
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
