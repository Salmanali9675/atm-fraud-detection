"""
Fraud Detector & Automated Decision Engine
Combines Machine Learning inference with banking business rules (hard thresholds + ML probability + automated card blocking).
"""

import os
import json
import joblib
import pandas as pd
from datetime import datetime

class FraudDetector:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, 'model', 'fraud_model.joblib')
        self.preprocessor_path = os.path.join(base_dir, 'model', 'preprocessor.joblib')
        self.audit_log_path = os.path.join(base_dir, 'data', 'audit_log.json')
        
        self.model = None
        self.preprocessor = None
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(self.model_path) and os.path.exists(self.preprocessor_path):
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
        else:
            raise FileNotFoundError("Model or Preprocessor not found. Run model/train.py first.")

    def analyze_transaction(self, txn_data, card_manager):
        """
        Evaluates a transaction and determines whether to APPROVE, OTP CHALLENGE, or BLOCK CARD.
        txn_data: dict containing transaction fields
        card_manager: CardManager instance
        """
        card_id = txn_data.get('card_id')
        amount = float(txn_data.get('amount', 0))
        failed_pins = int(txn_data.get('failed_pin_count', 0))
        location_dist = float(txn_data.get('location_dist_km', 0))
        time_diff = float(txn_data.get('time_diff_min', 60))
        hour = int(txn_data.get('hour', 12))
        day_of_week = int(txn_data.get('day_of_week', 2))
        atm_type = txn_data.get('atm_type', 'Branch ATM')
        is_international = int(txn_data.get('is_international', 0))
        daily_count = int(txn_data.get('daily_atm_count', 1))

        # 1. Compute velocity (km/h)
        time_diff_hours = max(time_diff / 60.0, 0.05)
        velocity_kmh = round(location_dist / time_diff_hours, 2)

        # 2. Hard Rule Check: Already Blocked Card
        if card_manager.is_blocked(card_id):
            result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'card_id': card_id,
                'amount': amount,
                'status': 'REJECTED',
                'risk_level': 'CRITICAL',
                'fraud_prob': 1.0,
                'action_taken': 'CARD_RETAINED',
                'reasons': ['Card is currently BLOCKED by security.'],
                'message': 'CARD ALREADY BLOCKED: Transaction aborted. ATM has retained card for owner safety.'
            }
            self._log_audit(result)
            return result

        # 3. Hard Rule Check: 3 Failed PIN attempts
        if failed_pins >= 3:
            reason = "Automated Security Lock: 3 consecutive failed PIN attempts."
            card_manager.block_card(card_id, reason=reason, fraud_score=1.0)
            result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'card_id': card_id,
                'amount': amount,
                'status': 'CARD_BLOCKED',
                'risk_level': 'CRITICAL',
                'fraud_prob': 1.0,
                'action_taken': 'AUTO_BLOCKED',
                'reasons': ['Exceeded maximum allowed PIN attempts (3 failed tries)'],
                'message': 'ALERT: 3 failed PIN attempts detected. Card automatically BLOCKED to prevent brute force theft.'
            }
            self._log_audit(result)
            return result

        # 4. Machine Learning Inference
        row_dict = {
            'amount': [amount],
            'hour': [hour],
            'day_of_week': [day_of_week],
            'location_dist_km': [location_dist],
            'time_diff_min': [time_diff],
            'velocity_kmh': [velocity_kmh],
            'failed_pin_count': [failed_pins],
            'daily_atm_count': [daily_count],
            'atm_type': [atm_type],
            'is_international': [is_international]
        }
        df_input = pd.DataFrame(row_dict)
        processed_input = self.preprocessor.transform(df_input)
        fraud_prob = float(self.model.predict_proba(processed_input)[0][1])

        # 5. Extract explainable risk triggers
        triggers = []
        if velocity_kmh > 400:
            triggers.append(f"Impossible Physical Travel ({velocity_kmh:.0f} km/h between locations)")
        if hour in [0, 1, 2, 3, 4] and amount > 15000:
            triggers.append(f"High withdrawal ({amount:,.0f}) during high-risk midnight hours ({hour:02d}:00)")
        if location_dist > 300:
            triggers.append(f"Anomalous distance ({location_dist:.1f} km away from registered home city)")
        if failed_pins > 0:
            triggers.append(f"{failed_pins} preceding incorrect PIN attempt(s)")
        if daily_count >= 4:
            triggers.append(f"Rapid burst usage ({daily_count} ATM withdrawals today)")
        if is_international:
            triggers.append("Foreign / International ATM transaction")
        if not triggers and fraud_prob > 0.4:
            triggers.append("Statistical deviation from normal customer profile")

        # 6. Automated Tiered Decisioning
        if fraud_prob < 0.35:
            # Low Risk -> Deduct and Approve
            success, balance_info = card_manager.deduct_balance(card_id, amount)
            if success:
                result = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'card_id': card_id,
                    'amount': amount,
                    'status': 'APPROVED',
                    'risk_level': 'LOW',
                    'fraud_prob': round(fraud_prob, 4),
                    'action_taken': 'DISPENSE_CASH',
                    'remaining_balance': balance_info,
                    'reasons': ['Transaction within regular safety bounds'],
                    'message': f"TRANSACTION APPROVED: Please take your cash (Rs. {amount:,.0f}). Remaining Balance: Rs. {balance_info:,.0f}"
                }
            else:
                result = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'card_id': card_id,
                    'amount': amount,
                    'status': 'DECLINED',
                    'risk_level': 'LOW',
                    'fraud_prob': round(fraud_prob, 4),
                    'action_taken': 'NONE',
                    'reasons': [f"Insufficient funds: {balance_info}"],
                    'message': f"DECLINED: {balance_info}. Transaction cancelled."
                }
        elif 0.35 <= fraud_prob < 0.70:
            # Medium Risk -> OTP Step-Up Challenge
            result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'card_id': card_id,
                'amount': amount,
                'status': 'SUSPICIOUS_OTP_REQUIRED',
                'risk_level': 'MEDIUM',
                'fraud_prob': round(fraud_prob, 4),
                'action_taken': 'OTP_CHALLENGE',
                'reasons': triggers,
                'message': "SUSPICIOUS ACTIVITY: An OTP verification code has been sent to your registered mobile number."
            }
        else:
            # High Risk (>= 0.70) -> Automated Instant Card Block
            block_reason = f"ML Fraud Alert (Risk {fraud_prob*100:.1f}%): " + ", ".join(triggers[:2])
            card_manager.block_card(card_id, reason=block_reason, fraud_score=fraud_prob)
            result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'card_id': card_id,
                'amount': amount,
                'status': 'CARD_BLOCKED',
                'risk_level': 'CRITICAL',
                'fraud_prob': round(fraud_prob, 4),
                'action_taken': 'AUTO_BLOCKED',
                'reasons': triggers,
                'message': f"SECURITY ALERT: Fraud probability {fraud_prob*100:.1f}%. CARD INSTANTLY BLOCKED. Please contact bank customer support."
            }

        self._log_audit(result)
        return result

    def _log_audit(self, entry):
        records = []
        if os.path.exists(self.audit_log_path):
            try:
                with open(self.audit_log_path, 'r') as f:
                    records = json.load(f)
            except Exception:
                records = []
        records.insert(0, entry) # Most recent first
        # Keep last 150 transactions
        records = records[:150]
        with open(self.audit_log_path, 'w') as f:
            json.dump(records, f, indent=2)

    def get_audit_logs(self):
        if os.path.exists(self.audit_log_path):
            try:
                with open(self.audit_log_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
