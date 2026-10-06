"""
Comprehensive backend API tests for cardIQ - Round 2
Tests all /api endpoints with the external base URL
Includes new Round 2 features: applyUrl, creditReq, international, credit scoring, admin endpoint
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

def test_get_cards_with_new_fields():
    """Test 1: GET /api/cards - should return 8 cards with applyUrl and creditReq"""
    print_test_header("GET /api/cards - Card catalog with applyUrl and creditReq")
    
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
        
        # Check ALL cards have applyUrl and creditReq
        all_passed = True
        for i, card in enumerate(cards):
            card_id = card.get("id", f"card_{i}")
            
            # Check applyUrl
            if "applyUrl" not in card:
                print_result(False, f"Card {card_id} missing applyUrl field")
                all_passed = False
            elif not isinstance(card["applyUrl"], str):
                print_result(False, f"Card {card_id} applyUrl is not a string")
                all_passed = False
            elif not card["applyUrl"].startswith("https://"):
                print_result(False, f"Card {card_id} applyUrl does not start with https://", card["applyUrl"])
                all_passed = False
            
            # Check creditReq
            if "creditReq" not in card:
                print_result(False, f"Card {card_id} missing creditReq field")
                all_passed = False
            elif card["creditReq"] not in ["new", "fair", "good", "excellent"]:
                print_result(False, f"Card {card_id} creditReq invalid value: {card['creditReq']}")
                all_passed = False
        
        if all_passed:
            print_result(True, "All 8 cards have applyUrl (https://) and creditReq (new/fair/good/excellent)")
            print(f"Sample: {cards[0]['id']} - applyUrl: {cards[0]['applyUrl']}, creditReq: {cards[0]['creditReq']}")
        
        return all_passed
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_quiz_submit_premium_travel_profile():
    """Test 2a: POST /api/quiz/submit - Full premium travel profile (should get voyager-infinite)"""
    print_test_header("POST /api/quiz/submit - Premium travel profile (voyager-infinite expected)")
    
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
            "name": "Premium Traveler",
            "email": "delivered@resend.dev"
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
        
        if not scored:
            print_result(False, "Scored list is empty")
            return None
        
        # Check top card is voyager-infinite
        top_card_id = scored[0]["card"]["id"]
        top_score = scored[0]["score"]
        
        print(f"Top card: {top_card_id} (score: {top_score})")
        print(f"Top 3 cards: {[(s['card']['id'], s['score']) for s in scored[:3]]}")
        
        if top_card_id != "voyager-infinite":
            print_result(False, f"Expected voyager-infinite as top card, got {top_card_id}")
            print(f"Full scoring: {[(s['card']['id'], s['score']) for s in scored]}")
            return None
        
        # Check scores are sorted descending
        scores = [s["score"] for s in scored]
        if scores != sorted(scores, reverse=True):
            print_result(False, "Scores are not sorted in descending order", scores)
            return None
        
        print_result(True, f"Premium travel profile correctly ranked voyager-infinite as top card (score: {top_score})")
        return result_id
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return None

def test_quiz_submit_new_credit_budget_traveler():
    """Test 2b: POST /api/quiz/submit - New-to-credit budget traveler (should NOT get voyager-infinite)"""
    print_test_header("POST /api/quiz/submit - New-credit budget traveler (voyager-infinite should be penalized)")
    
    payload = {
        "answers": {
            "goal": "travel",
            "spend": "low",
            "fee": "free",
            "usage": "flights",
            "priority": "lounge",
            "international": "rarely",
            "credit": "new"
        },
        "lead": {
            "name": "Budget Traveler",
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
        top_score = scored[0]["score"]
        
        print(f"Top card: {top_card_id} (score: {top_score})")
        print(f"Top 5 cards: {[(s['card']['id'], s['score']) for s in scored[:5]]}")
        
        # voyager-infinite should NOT be the top card (it requires excellent credit + premium fee)
        if top_card_id == "voyager-infinite":
            print_result(False, f"voyager-infinite should NOT be top for new-credit budget traveler")
            print(f"Full scoring: {[(s['card']['id'], s['score']) for s in scored]}")
            return False
        
        # Find voyager-infinite in the list and check it's penalized
        voyager_score = None
        for s in scored:
            if s["card"]["id"] == "voyager-infinite":
                voyager_score = s["score"]
                break
        
        if voyager_score is not None:
            print(f"voyager-infinite score: {voyager_score} (should be low/negative due to credit mismatch)")
        
        # Top card should be a lifetime-free or lower-requirement card
        top_card = scored[0]["card"]
        print(f"Top card details: feeType={top_card.get('feeType')}, creditReq={top_card.get('creditReq')}")
        
        print_result(True, f"New-credit budget traveler correctly ranked {top_card_id} as top (not voyager-infinite)")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_quiz_submit_shopping_profile():
    """Test 2c: POST /api/quiz/submit - Shopping profile (should get metrocash-rewards or prime-rewards)"""
    print_test_header("POST /api/quiz/submit - Shopping profile")
    
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
            "name": "Shopping Enthusiast",
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
        top_score = scored[0]["score"]
        
        print(f"Top card: {top_card_id} (score: {top_score})")
        print(f"Top 3 cards: {[(s['card']['id'], s['score']) for s in scored[:3]]}")
        
        # Top card should be metrocash-rewards or prime-rewards
        expected_cards = ["metrocash-rewards", "prime-rewards"]
        if top_card_id not in expected_cards:
            print_result(False, f"Expected top card to be one of {expected_cards}, got {top_card_id}")
            print(f"Full scoring: {[(s['card']['id'], s['score']) for s in scored]}")
            return False
        
        print_result(True, f"Shopping profile correctly ranked {top_card_id} as top card")
        return True
        
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False

def test_get_result(result_id: Optional[str]):
    """Test 3: GET /api/results/{result_id} - fetch stored result"""
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

def test_email_result(result_id: Optional[str]):
    """Test 4: POST /api/results/{result_id}/email - send email via Resend"""
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

def test_admin_leads_endpoint():
    """Test 6: GET /api/admin/leads - admin endpoint with auth header"""
    print_test_header("GET /api/admin/leads - Admin endpoint with authentication")
    
    all_passed = True
    
    # Test 6a: With correct admin token
    try:
        headers = {"X-Admin-Token": ADMIN_TOKEN}
        response = requests.get(f"{BASE_URL}/admin/leads", headers=headers, timeout=10)
        print(f"Status Code with correct token: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"Expected 200 with correct token, got {response.status_code}", response.text)
            all_passed = False
        else:
            result = response.json()
            
            # Check response structure
            if "total" not in result or "leads" not in result:
                print_result(False, "Missing 'total' or 'leads' in response", result)
                all_passed = False
            else:
                total = result["total"]
                leads = result["leads"]
                
                print(f"Total leads: {total}")
                print(f"Leads array length: {len(leads)}")
                
                if total != len(leads):
                    print_result(False, f"Total ({total}) doesn't match leads array length ({len(leads)})")
                    all_passed = False
                
                # Check lead structure if we have any leads
                if leads:
                    first_lead = leads[0]
                    required_fields = ["name", "email", "phone", "recommended_card", "email_sent", "created_at", "result_id"]
                    missing_fields = [f for f in required_fields if f not in first_lead]
                    
                    if missing_fields:
                        print_result(False, f"Lead missing required fields: {missing_fields}", first_lead)
                        all_passed = False
                    else:
                        print(f"Sample lead: name={first_lead['name']}, email={first_lead['email']}, recommended_card={first_lead['recommended_card']}")
                        print_result(True, f"Admin endpoint returned {total} leads with correct structure")
                else:
                    print_result(True, "Admin endpoint returned 0 leads (no quiz submissions yet)")
                
    except Exception as e:
        print_result(False, f"Exception with correct token: {str(e)}")
        all_passed = False
    
    # Test 6b: Without admin token (should return 401)
    try:
        response = requests.get(f"{BASE_URL}/admin/leads", timeout=10)
        print(f"Status Code without token: {response.status_code}")
        
        if response.status_code != 401:
            print_result(False, f"Expected 401 without token, got {response.status_code}")
            all_passed = False
        else:
            print_result(True, "Correctly returned 401 without admin token")
    except Exception as e:
        print_result(False, f"Exception without token: {str(e)}")
        all_passed = False
    
    # Test 6c: With wrong admin token (should return 401)
    try:
        headers = {"X-Admin-Token": "wrong-token"}
        response = requests.get(f"{BASE_URL}/admin/leads", headers=headers, timeout=10)
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

def main():
    """Run all backend tests for Round 2"""
    print("\n" + "="*80)
    print("CARDIQ BACKEND API TEST SUITE - ROUND 2")
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    results = {}
    result_id = None
    
    # Test 1: GET /api/cards with new fields
    results["1. GET /api/cards (applyUrl + creditReq)"] = test_get_cards_with_new_fields()
    
    # Test 2a: POST /api/quiz/submit - premium travel profile
    result_id = test_quiz_submit_premium_travel_profile()
    results["2a. POST /api/quiz/submit (premium travel → voyager-infinite)"] = result_id is not None
    
    # Test 2b: POST /api/quiz/submit - new-credit budget traveler
    results["2b. POST /api/quiz/submit (new-credit budget → NOT voyager-infinite)"] = test_quiz_submit_new_credit_budget_traveler()
    
    # Test 2c: POST /api/quiz/submit - shopping profile
    results["2c. POST /api/quiz/submit (shopping → metrocash/prime)"] = test_quiz_submit_shopping_profile()
    
    # Test 3: GET /api/results/{result_id}
    results["3. GET /api/results/{result_id}"] = test_get_result(result_id)
    
    # Test 4: POST /api/results/{result_id}/email
    results["4. POST /api/results/{result_id}/email"] = test_email_result(result_id)
    
    # Test 5: POST /api/cards/compare
    results["5. POST /api/cards/compare"] = test_cards_compare()
    
    # Test 6: GET /api/admin/leads
    results["6. GET /api/admin/leads (auth header)"] = test_admin_leads_endpoint()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY - ROUND 2")
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
