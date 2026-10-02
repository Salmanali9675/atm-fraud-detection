"""
Card State Management Module
Maintains card registry, active/blocked states, account balances, and administrative unblock actions.
"""

import os
import json
from datetime import datetime

class CardManager:
    def __init__(self, registry_file=None):
        if registry_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_file = os.path.join(base_dir, 'data', 'card_registry.json')
        self.registry_file = registry_file
        self._initialize_registry()

    def _initialize_registry(self):
        """Creates sample demo cards if registry doesn't exist."""
        if not os.path.exists(self.registry_file):
            default_cards = {
                "CARD_1001": {
                    "card_id": "CARD_1001",
                    "holder_name": "Salma Khan",
                    "masked_number": "4532 **** **** 1001",
                    "pin": "1234",
                    "balance": 150000.0,
                    "daily_limit": 50000.0,
                    "status": "ACTIVE",  # ACTIVE or BLOCKED
                    "home_city": "Karachi",
                    "blocked_at": None,
                    "block_reason": None,
                    "fraud_score": 0.0
                },
                "CARD_1002": {
                    "card_id": "CARD_1002",
                    "holder_name": "Hamza Ali",
                    "masked_number": "5241 **** **** 1002",
                    "pin": "4321",
                    "balance": 85000.0,
                    "daily_limit": 50000.0,
                    "status": "ACTIVE",
                    "home_city": "Lahore",
                    "blocked_at": None,
                    "block_reason": None,
                    "fraud_score": 0.0
                },
                "CARD_1003": {
                    "card_id": "CARD_1003",
                    "holder_name": "Ayesha Malik",
                    "masked_number": "4111 **** **** 1003",
                    "pin": "9988",
                    "balance": 320000.0,
                    "daily_limit": 100000.0,
                    "status": "ACTIVE",
                    "home_city": "Islamabad",
                    "blocked_at": None,
                    "block_reason": None,
                    "fraud_score": 0.0
                },
                "CARD_1004": {
                    "card_id": "CARD_1004",
                    "holder_name": "Bilal Ahmed",
                    "masked_number": "5425 **** **** 1004",
                    "pin": "7777",
                    "balance": 45000.0,
                    "daily_limit": 25000.0,
                    "status": "BLOCKED",
                    "home_city": "Rawalpindi",
                    "blocked_at": "2026-10-01 14:22:00",
                    "block_reason": "Automated ML Block: High velocity impossible travel (Lahore -> London in 15 mins)",
                    "fraud_score": 0.94
                }
            }
            self._save(default_cards)

    def _load(self):
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_card(self, card_id):
        cards = self._load()
        return cards.get(card_id)

    def list_all_cards(self):
        return list(self._load().values())

    def is_blocked(self, card_id):
        card = self.get_card(card_id)
        if not card:
            return False
        return card.get("status") == "BLOCKED"

    def block_card(self, card_id, reason, fraud_score=1.0):
        cards = self._load()
        if card_id in cards:
            cards[card_id]["status"] = "BLOCKED"
            cards[card_id]["blocked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cards[card_id]["block_reason"] = reason
            cards[card_id]["fraud_score"] = round(float(fraud_score), 4)
            self._save(cards)
            return True
        return False

    def unblock_card(self, card_id):
        cards = self._load()
        if card_id in cards:
            cards[card_id]["status"] = "ACTIVE"
            cards[card_id]["blocked_at"] = None
            cards[card_id]["block_reason"] = None
            cards[card_id]["fraud_score"] = 0.0
            self._save(cards)
            return True
        return False

    def deduct_balance(self, card_id, amount):
        cards = self._load()
        if card_id in cards and cards[card_id]["status"] == "ACTIVE":
            if cards[card_id]["balance"] >= amount:
                cards[card_id]["balance"] -= amount
                self._save(cards)
                return True, cards[card_id]["balance"]
            else:
                return False, "Insufficient balance"
        return False, "Card not active or does not exist"

    def reset_demo_registry(self):
        if os.path.exists(self.registry_file):
            os.remove(self.registry_file)
        self._initialize_registry()
