"""
Automated Verification Script for ATM Fraud Detector & Card Manager
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.card_manager import CardManager
from src.fraud_detector import FraudDetector

def run_tests():
    print("=== Starting System Verification ===")
    cm = CardManager()
    cm.reset_demo_registry()
    detector = FraudDetector()

    # Test 1: Normal Legitimate Transaction
    print("\n[Test 1] Legitimate ATM Withdrawal...")
    normal_txn = {
        'card_id': 'CARD_1001',
        'amount': 2000.0,
        'hour': 14,
        'day_of_week': 2,
        'location_dist_km': 3.5,
        'time_diff_min': 480, # 8 hours
        'failed_pin_count': 0,
        'daily_atm_count': 1,
        'atm_type': 'Branch ATM',
        'is_international': 0
    }
    res1 = detector.analyze_transaction(normal_txn, cm)
    print(f"Result: {res1['status']} | Risk: {res1['risk_level']} | Prob: {res1['fraud_prob']}")
    assert res1['status'] == 'APPROVED', f"Expected APPROVED, got {res1['status']}"
    print("[PASS] Test 1 Passed!")

    # Test 2: Impossible Velocity / High Distance Fraud -> Should Auto-Block
    print("\n[Test 2] High Velocity Impossible Travel Fraud...")
    fraud_txn = {
        'card_id': 'CARD_1002',
        'amount': 45000.0,
        'hour': 3, # 3 AM
        'day_of_week': 3,
        'location_dist_km': 850.0, # 850 km away
        'time_diff_min': 15,       # 15 minutes later -> 3400 km/h
        'failed_pin_count': 1,
        'daily_atm_count': 3,
        'atm_type': 'Off-Premise',
        'is_international': 0
    }
    res2 = detector.analyze_transaction(fraud_txn, cm)
    print(f"Result: {res2['status']} | Risk: {res2['risk_level']} | Prob: {res2['fraud_prob']}")
    print(f"Reasons: {res2['reasons']}")
    assert res2['status'] == 'CARD_BLOCKED', f"Expected CARD_BLOCKED, got {res2['status']}"
    assert cm.is_blocked('CARD_1002') is True, "Card 1002 should now be in BLOCKED state"
    print("[PASS] Test 2 Passed: Card 1002 was automatically blocked!")

    # Test 3: Attempting withdrawal on newly blocked card
    print("\n[Test 3] Attempting another transaction on blocked CARD_1002...")
    res3 = detector.analyze_transaction(normal_txn | {'card_id': 'CARD_1002'}, cm)
    print(f"Result: {res3['status']} | Action: {res3['action_taken']}")
    assert res3['status'] == 'REJECTED', f"Expected REJECTED, got {res3['status']}"
    print("[PASS] Test 3 Passed: Blocked card successfully rejected!")

    # Test 4: Admin Unblock
    print("\n[Test 4] Admin unblocks CARD_1002...")
    unblock_success = cm.unblock_card('CARD_1002')
    assert unblock_success is True
    assert cm.is_blocked('CARD_1002') is False
    print("[PASS] Test 4 Passed: Admin unblock operational!")

    # Test 5: 3 Consecutive Failed PIN Attempts
    print("\n[Test 5] Brute Force PIN Lockout (3 failed PINs)...")
    bruteforce_txn = {
        'card_id': 'CARD_1003',
        'amount': 5000.0,
        'hour': 12,
        'day_of_week': 1,
        'location_dist_km': 2.0,
        'time_diff_min': 60,
        'failed_pin_count': 3, # 3 failed attempts
        'daily_atm_count': 1,
        'atm_type': 'Branch ATM',
        'is_international': 0
    }
    res5 = detector.analyze_transaction(bruteforce_txn, cm)
    print(f"Result: {res5['status']} | Action: {res5['action_taken']}")
    assert res5['status'] == 'CARD_BLOCKED', f"Expected CARD_BLOCKED, got {res5['status']}"
    assert cm.is_blocked('CARD_1003') is True
    print("[PASS] Test 5 Passed: 3 Failed PINs triggered auto-block!")

    print("\n==========================================")
    print(" ALL 5 AUTOMATED VERIFICATION TESTS PASSED!")
    print("==========================================")

if __name__ == '__main__':
    run_tests()
