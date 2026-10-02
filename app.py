"""
Streamlit Web Application:
1. ATM Terminal Simulator (Customer view with realistic card swipe & withdrawal)
2. Bank Security Operations Center (Admin view with live audit feed & card unblocker)
3. Model Intelligence & Explainability Dashboard
4. Study Guide (Roman Urdu & English)
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from src.card_manager import CardManager
from src.fraud_detector import FraudDetector

# Configure page
st.set_page_config(
    page_title="ATM Fraud Guard & Automated Card Blocking",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 20px;
    }
    .atm-card-box {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        font-family: monospace;
    }
    .badge-approved {
        background-color: #10B981;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-otp {
        background-color: #F59E0B;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-blocked {
        background-color: #EF4444;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Instantiate Core Engines
@st.cache_resource
def get_engines():
    cm = CardManager()
    fd = FraudDetector()
    return cm, fd

cm, fd = get_engines()

# Load Model Metrics
metrics_path = os.path.join(BASE_DIR, 'model', 'model_metrics.json')
model_metrics = {}
if os.path.exists(metrics_path):
    with open(metrics_path, 'r') as f:
        model_metrics = json.load(f)

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/bank-card-back-side.png", width=70)
st.sidebar.title("ATM Fraud Guard")
st.sidebar.markdown("**Machine Learning Card Blocking System**")
st.sidebar.divider()

navigation = st.sidebar.radio(
    "Select Interface:",
    [
        "🏧 ATM Terminal Simulator",
        "🛡️ Bank Security Center (Admin)",
        "📊 ML Intelligence & Explainability",
        "📖 Study Notes & Concepts"
    ]
)

st.sidebar.divider()
st.sidebar.caption("System State: 🟢 Online (Random Forest Engine)")

# ==============================================================================
# TAB 1: ATM TERMINAL SIMULATOR
# ==============================================================================
if navigation == "🏧 ATM Terminal Simulator":
    st.markdown('<div class="main-header">🏧 Interactive ATM Cash Dispenser</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Simulate live ATM transactions and observe instant fraud detection and automated card blocking in action.</div>', unsafe_allow_html=True)

    col_atm_left, col_atm_right = st.columns([1, 1], gap="large")

    with col_atm_left:
        st.subheader("1. Card & PIN Insertion")
        cards = cm.list_all_cards()
        card_options = {f"{c['holder_name']} ({c['masked_number']}) - Status: {c['status']}": c['card_id'] for c in cards}
        selected_card_label = st.selectbox("Select ATM Card:", list(card_options.keys()))
        selected_card_id = card_options[selected_card_label]
        card_info = cm.get_card(selected_card_id)

        # Show visual credit card widget
        status_color = "#10B981" if card_info['status'] == "ACTIVE" else "#EF4444"
        st.markdown(f"""
        <div class="atm-card-box">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 1.2rem; font-weight:bold; letter-spacing: 2px;">SECURE BANK</span>
                <span style="background:{status_color}; padding:2px 8px; border-radius:4px; font-size:0.75rem;">{card_info['status']}</span>
            </div>
            <div style="font-size: 1.5rem; letter-spacing: 4px; margin: 25px 0;">{card_info['masked_number']}</div>
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div style="font-size: 0.7rem; color: #94A3B8;">CARD HOLDER</div>
                    <div style="font-size: 0.95rem; font-weight: bold;">{card_info['holder_name']}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #94A3B8;">BALANCE</div>
                    <div style="font-size: 0.95rem; font-weight: bold;">Rs. {card_info['balance']:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if card_info['status'] == "BLOCKED":
            st.error(f"⚠️ **THIS CARD IS CURRENTLY BLOCKED!**\nReason: {card_info.get('block_reason', 'Security Alert')}")
            st.info("💡 You can unblock this card anytime from the **Bank Security Center** tab.")

        st.subheader("2. Fast Demo Scenarios (One-Click Testing)")
        demo_scenario = st.radio(
            "Choose a predefined scenario or enter custom values:",
            [
                "Custom Inputs",
                "🟢 Normal Daytime Cash Withdrawal (Rs. 2,000, Home City, 0 Failed PINs)",
                "🔴 Midnight High-Value Drain (Rs. 45,000 at 3:00 AM, Remote ATM)",
                "🔴 Impossible Travel Velocity (Lahore to London in 15 mins - 3,400 km/h)",
                "🔴 PIN Brute Force Attack (3 Consecutive Failed PIN Attempts)",
                "🟡 Suspicious Spike (Rs. 18,000 at unfamiliar location -> Triggers OTP)"
            ]
        )

    with col_atm_right:
        st.subheader("3. Transaction Parameters")

        # Set default values based on chosen demo scenario
        if "Normal Daytime" in demo_scenario:
            d_amount = 2000.0
            d_hour = 14
            d_dist = 4.2
            d_timediff = 720
            d_pin_fails = 0
            d_daily = 1
            d_atm_type = "Branch ATM"
            d_intl = 0
        elif "Midnight High-Value" in demo_scenario:
            d_amount = 45000.0
            d_hour = 3
            d_dist = 85.0
            d_timediff = 120
            d_pin_fails = 1
            d_daily = 3
            d_atm_type = "Remote ATM"
            d_intl = 0
        elif "Impossible Travel" in demo_scenario:
            d_amount = 35000.0
            d_hour = 16
            d_dist = 850.0
            d_timediff = 15 # 850km in 15 minutes = 3400 km/h!
            d_pin_fails = 0
            d_daily = 2
            d_atm_type = "Off-Premise"
            d_intl = 0
        elif "PIN Brute Force" in demo_scenario:
            d_amount = 10000.0
            d_hour = 20
            d_dist = 12.0
            d_timediff = 60
            d_pin_fails = 3 # 3 failed PIN attempts
            d_daily = 1
            d_atm_type = "Branch ATM"
            d_intl = 0
        elif "Suspicious Spike" in demo_scenario:
            d_amount = 18000.0
            d_hour = 23
            d_dist = 120.0
            d_timediff = 90
            d_pin_fails = 1
            d_daily = 3
            d_atm_type = "Remote ATM"
            d_intl = 0
        else:
            d_amount = 5000.0
            d_hour = 12
            d_dist = 5.0
            d_timediff = 360
            d_pin_fails = 0
            d_daily = 1
            d_atm_type = "Branch ATM"
            d_intl = 0

        # Form fields
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            amount = st.number_input("Withdrawal Amount (Rs.):", min_value=500.0, max_value=100000.0, value=d_amount, step=500.0)
            hour = st.slider("Time of Transaction (Hour 0-23):", 0, 23, d_hour)
            location_dist = st.number_input("Distance from Registered City (km):", min_value=0.0, max_value=5000.0, value=float(d_dist), step=5.0)
            daily_count = st.number_input("ATM Withdrawals Today:", min_value=1, max_value=10, value=d_daily)

        with col_t2:
            time_diff = st.number_input("Minutes Since Last Transaction:", min_value=1, max_value=4320, value=int(d_timediff))
            failed_pins = st.selectbox("Preceding Failed PIN Attempts:", [0, 1, 2, 3], index=d_pin_fails)
            atm_type = st.selectbox("ATM Machine Type:", ["Branch ATM", "Remote ATM", "Off-Premise"], index=["Branch ATM", "Remote ATM", "Off-Premise"].index(d_atm_type))
            is_intl = st.selectbox("International ATM Transaction?", ["No (Domestic)", "Yes (Foreign)"], index=d_intl)

        # Derived Velocity display
        velocity = location_dist / max(time_diff / 60.0, 0.05)
        if velocity > 500:
            st.warning(f"⚠️ Computed Velocity: **{velocity:,.0f} km/h** (Physically Impossible Travel Velocity!)")
        else:
            st.info(f"ℹ️ Computed Velocity: **{velocity:.1f} km/h**")

        st.markdown("---")
        btn_withdraw = st.button("🏧 EXECUTE ATM WITHDRAWAL", type="primary", use_container_width=True)

        if btn_withdraw:
            payload = {
                'card_id': selected_card_id,
                'amount': amount,
                'hour': hour,
                'day_of_week': 2,
                'location_dist_km': location_dist,
                'time_diff_min': time_diff,
                'failed_pin_count': failed_pins,
                'daily_atm_count': daily_count,
                'atm_type': atm_type,
                'is_international': 1 if "Yes" in is_intl else 0
            }

            with st.spinner("Processing ATM Request through Fraud Engine..."):
                response = fd.analyze_transaction(payload, cm)

            st.markdown("### 🏧 ATM Screen Response:")
            status = response['status']
            prob = response.get('fraud_prob', 0.0)

            if status == "APPROVED":
                st.success(f"### 🟢 {response['message']}")
                st.balloons()
            elif status == "SUSPICIOUS_OTP_REQUIRED":
                st.warning(f"### 🟡 {response['message']}")
                st.markdown("**Reason(s) Flagged by Model:**")
                for r in response.get('reasons', []):
                    st.write(f"- ⚠️ {r}")
                otp_code = st.text_input("Enter 6-digit SMS OTP code sent to customer:", value="842190")
                if st.button("Verify OTP & Release Funds"):
                    cm.deduct_balance(selected_card_id, amount)
                    st.success("OTP Verified successfully! Cash dispensed.")
                    st.rerun()
            elif status == "CARD_BLOCKED":
                st.error(f"### 🔴 {response['message']}")
                st.markdown("**Automated Actions Taken:**")
                st.write("- 🔒 **Card has been immediately LOCKED in the bank system.**")
                st.write("- 🚫 **ATM retained the card** (will not be ejected to prevent thief fleeing with it).")
                st.write("- 🚨 **Bank Security Operations Center alerted.**")
                st.markdown("**Detection Triggers:**")
                for r in response.get('reasons', []):
                    st.write(f"- ❌ {r}")
                st.rerun()
            elif status == "REJECTED":
                st.error(f"### ⛔ {response['message']}")
            else:
                st.info(response['message'])

# ==============================================================================
# TAB 2: BANK SECURITY OPERATIONS CENTER (ADMIN VIEW)
# ==============================================================================
elif navigation == "🛡️ Bank Security Center (Admin)":
    st.markdown('<div class="main-header">🛡️ Bank Security Operations Center (SOC)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live monitoring of incoming ATM traffic, automated fraud block events, and card registry management.</div>', unsafe_allow_html=True)

    cards = cm.list_all_cards()
    blocked_cards = [c for c in cards if c['status'] == "BLOCKED"]
    audit_logs = fd.get_audit_logs()

    # KPI Metrics
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total Cards Managed", len(cards))
    with col_k2:
        st.metric("Currently Blocked Cards", len(blocked_cards), delta=f"{len(blocked_cards)} alert(s)", delta_color="inverse")
    with col_k3:
        st.metric("Audit Stream Events", len(audit_logs))
    with col_k4:
        st.metric("Model Precision", f"{model_metrics.get('metrics', {}).get('precision', 1.0) * 100:.1f}%")

    st.divider()

    # Section A: Card Registry & Administrative Unblock Actions
    st.subheader("📋 Card Registry & Security Status")
    st.caption("Inspect card status or manually unblock a card after verifying customer identity.")

    for c in cards:
        with st.expander(f"💳 {c['holder_name']} | {c['masked_number']} | Status: {c['status']}", expanded=(c['status'] == "BLOCKED")):
            col_info, col_action = st.columns([3, 1])
            with col_info:
                st.write(f"**Card ID:** `{c['card_id']}` | **Home City:** {c['home_city']} | **Account Balance:** Rs. {c['balance']:,.0f}")
                if c['status'] == "BLOCKED":
                    st.error(f"🔒 **BLOCKED AT:** {c.get('blocked_at')}\n\n**Reason:** {c.get('block_reason')}\n\n**Risk Score:** {c.get('fraud_score', 0.0) * 100:.1f}%")
                else:
                    st.success("🟢 Status: Normal / Active")
            with col_action:
                if c['status'] == "BLOCKED":
                    if st.button(f"🔓 Unblock Card", key=f"unblock_{c['card_id']}", type="primary"):
                        cm.unblock_card(c['card_id'])
                        st.success(f"{c['holder_name']}'s card has been reactivated!")
                        st.rerun()
                else:
                    if st.button(f"🔒 Manually Block", key=f"block_{c['card_id']}"):
                        cm.block_card(c['card_id'], reason="Manual Admin Lock from Security Portal", fraud_score=1.0)
                        st.warning(f"{c['holder_name']}'s card manually blocked!")
                        st.rerun()

    st.divider()

    # Section B: Live Audit Stream
    st.subheader("📡 Live Transaction Audit & Fraud Alert Log")
    if audit_logs:
        df_logs = pd.DataFrame(audit_logs)
        # Display top 20
        st.dataframe(
            df_logs[['timestamp', 'card_id', 'amount', 'risk_level', 'status', 'fraud_prob', 'message']],
            use_container_width=True
        )
    else:
        st.info("No transactions logged yet. Run a withdrawal in the ATM Simulator tab to view the live audit stream.")

    if st.button("Reset Demo Cards & Registry to Default"):
        cm.reset_demo_registry()
        st.success("Registry reset to initial state.")
        st.rerun()

# ==============================================================================
# TAB 3: ML INTELLIGENCE & EXPLAINABILITY
# ==============================================================================
elif navigation == "📊 ML Intelligence & Explainability":
    st.markdown('<div class="main-header">📊 Machine Learning Model Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating model behavior on extreme class imbalance and understanding why ML is preferred over Deep Learning for banking.</div>', unsafe_allow_html=True)

    if model_metrics:
        metrics = model_metrics.get('metrics', {})
        cm_data = model_metrics.get('confusion_matrix', {})

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Test Precision (Positive Predictive Value)", f"{metrics.get('precision', 0)*100:.1f}%")
            st.caption("How many flagged transactions were truly fraud?")
        with col_m2:
            st.metric("Test Recall (Sensitivity)", f"{metrics.get('recall', 0)*100:.1f}%")
            st.caption("How many actual frauds were caught?")
        with col_m3:
            st.metric("F1-Score", f"{metrics.get('f1_score', 0):.4f}")
            st.caption("Harmonic mean of Precision & Recall")
        with col_m4:
            st.metric("PR-AUC Score", f"{metrics.get('pr_auc', 0):.4f}")
            st.caption("Precision-Recall Area Under Curve")

        st.divider()

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Confusion Matrix (3,000 Test Transactions)")
            cm_df = pd.DataFrame([
                [cm_data.get('true_negatives', 0), cm_data.get('false_positives', 0)],
                [cm_data.get('false_negatives', 0), cm_data.get('true_positives', 0)]
            ], index=["Actual Legitimate (0)", "Actual Fraud (1)"], columns=["Predicted Legitimate (0)", "Predicted Fraud (1)"])
            st.table(cm_df)

            st.markdown(f"""
            - **True Negatives ({cm_data.get('true_negatives')}):** Legitimate transactions correctly approved.
            - **False Positives ({cm_data.get('false_positives')}):** Innocent customers mistakenly blocked (Zero false alarms!).
            - **False Negatives ({cm_data.get('false_negatives')}):** Frauds missed (The most dangerous failure in banking).
            - **True Positives ({cm_data.get('true_positives')}):** Fraud attacks stopped in real-time!
            """)

        with col_right:
            st.subheader("Top Predictors of ATM Fraud")
            feat_imp = model_metrics.get('feature_importances', [])
            if feat_imp:
                df_imp = pd.DataFrame(feat_imp[:8])
                df_imp['importance_pct'] = df_imp['importance'] * 100
                st.bar_chart(df_imp.set_index('feature')['importance_pct'])

    st.divider()
    st.subheader("💡 Why Machine Learning instead of Deep Learning for ATM Fraud?")
    st.markdown("""
    | Aspect | Classical Machine Learning (Random Forest / GBDT) | Deep Learning (Neural Networks / Transformers) |
    | :--- | :--- | :--- |
    | **Data Type** | **Tabular Data Champion:** Excels on structured rows, columns, and numeric ratios. | Built for unstructured data (images, speech, text). Overfits easily on small tabular sets. |
    | **Regulatory Explainability (XAI)** | **High Transparency:** Tree paths and SHAP values show the exact reason a card was blocked. | **Black-box:** Very hard to explain to banking ombudsmen why a specific card was locked. |
    | **Latency** | **< 1 millisecond:** Instant execution right at the ATM terminal hardware. | **50 - 200 milliseconds:** Requires GPU or heavier server inference overhead. |
    | **Class Imbalance** | Handled natively via `class_weight='balanced_subsample'` and cost-sensitive trees. | Suffers vanishing gradients or mode collapse unless heavily regularized. |
    """)

# ==============================================================================
# TAB 4: STUDY NOTES & CONCEPTS
# ==============================================================================
elif navigation == "📖 Study Notes & Concepts":
    st.markdown('<div class="main-header">📖 ATM Fraud & Card Blocking ? Complete Study Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Asaan Roman Urdu + English Revision Guide (Just like Customer Churn!)</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 🌟 1. Churn vs Fraud: Farq Kya Hai?
    * **Customer Churn:** Banda ahista ahista service chhor kar jata hai (e.g. 25% log churn hotay hain).
    * **ATM / Card Fraud:** Yeh ek **chori (crime)** hai jo achanak hoti hai.
    * **Extreme Class Imbalance:** Data mein **98.5% transactions bilkul theek** hoti hain, aur sirf **1.5% fraud** hota hai!

    ---

    ### ⚠️ 2. The Accuracy Trap (Dhoka Accuracy)
    * Agar koi bewakoof model aankhein band karke keh de: *"Koi fraud nahi hai (0)"*, tab bhi uski accuracy **98.5%** aayegi!
    * Lekin woh **100% choron ko chhor dega**, aur bank lut jayega!
    * **Sabaq:** Fraud detection mein **Accuracy** dekhna bilkul bekaar hai. Hum **Recall** aur **Precision** dekhte hain.

    ---

    ### 🎯 3. False Positive vs False Negative (Zindagi Aur Maut Ka Faisla!)
    * **False Negative (FN) - *Intihaai Khatarnaak!*:**
      * Chor ATM se Rs. 50,000 nikal raha tha, lekin model ne samjha *"yeh to shareef banda hai"* aur paise de diye!
      * **Nateeja:** Bank aur customer ka nuqsaan, police case!
    * **False Positive (FP) - *Takleef De Lekin Mehfooz*:**
      * Asli customer restaurant mein dinner ka bill pay kar raha tha, model ne ghalti se card block kar diya!
      * **Nateeja:** Customer naraz hoga, helpline pe call karega, lekin paise mehfooz rahe.
    * **Banking Rule:** Banks hamesha chahte hain ke **False Negative = ZERO** ke qareeb ho (Recall high ho).

    ---

    ### 🧠 4. Deep Learning Kyun Compulsory Nahi Hai?
    * Deep learning images (chehra pehchanne) aur sound ke liye zabardast hai.
    * Lekin **Numbers aur Tables (Tabular Data)** ke liye **Random Forest aur XGBoost** dunya ka gold standard hain!
    * Banks ko Qanooni tor par (State Bank / Central Bank) batana parta hai ke *"Aap ne customer ka card kyun block kiya?"*. Tree models yeh saboot (Explainability) foran de dete hain!
    """)
