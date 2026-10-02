"""
ATM Transaction Dataset Generator
Generates realistic banking transaction logs with realistic fraud signatures and class imbalance (~1.5% fraud).
"""

import numpy as np
import pandas as pd
import random
import os

def generate_atm_transactions(num_records=15000, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    
    # 500 unique simulated customer cards
    card_pool = [f"CARD_{1000 + i}" for i in range(500)]
    customer_pool = [f"CUST_{2000 + (i % 350)}" for i in range(500)]
    card_to_cust = dict(zip(card_pool, customer_pool))
    
    records = []
    
    for i in range(num_records):
        txn_id = f"TXN_{100000 + i}"
        card_id = random.choice(card_pool)
        cust_id = card_to_cust[card_id]
        
        # Decide if this transaction will be fraud (~1.8% baseline)
        is_fraud = 1 if np.random.rand() < 0.018 else 0
        
        if is_fraud == 0:
            # Normal Transaction Behaviors
            # Typical hours: 7 AM to 11 PM
            if np.random.rand() < 0.85:
                hour = np.random.randint(7, 23)
            else:
                hour = np.random.randint(0, 7)
                
            day_of_week = np.random.randint(0, 7)
            
            # Normal amounts: typically standard ATM cash increments (e.g. 500 to 10,000)
            amount = float(np.random.choice([500, 1000, 1500, 2000, 3000, 5000, 8000, 10000, 15000, 20000],
                                           p=[0.15, 0.20, 0.10, 0.15, 0.10, 0.15, 0.05, 0.05, 0.03, 0.02]))
            # Small random noise to amount
            if np.random.rand() < 0.1:
                amount += np.random.choice([100, 200, 300])
                
            # Distance from home ATM: usually low (0 to 25 km)
            location_dist_km = round(float(np.random.exponential(scale=6.0)), 2)
            if location_dist_km > 75.0:
                location_dist_km = round(float(np.random.uniform(5.0, 30.0)), 2)
                
            # Time elapsed since last transaction (hours/minutes)
            time_diff_min = int(np.random.exponential(scale=720)) + 15 # avg 12 hours
            time_diff_min = min(time_diff_min, 4320) # cap at 3 days
            
            # Failed PIN attempts: usually 0, occasionally 1
            failed_pin_count = int(np.random.choice([0, 1], p=[0.96, 0.04]))
            
            # Daily ATM withdrawal count: usually 1st or 2nd of the day
            daily_atm_count = int(np.random.choice([1, 2, 3], p=[0.80, 0.16, 0.04]))
            
            # ATM type
            atm_type = np.random.choice(['Branch ATM', 'Remote ATM', 'Off-Premise'], p=[0.60, 0.30, 0.10])
            
            # International transaction: rare for normal ATM cash
            is_international = int(np.random.choice([0, 1], p=[0.985, 0.015]))
            
        else:
            # Fraudulent Transaction Patterns (Multiple realistic fraud vectors)
            fraud_type = np.random.choice([
                'midnight_drain',     # Midnight large withdrawal
                'impossible_travel',  # Massive distance in minutes
                'pin_bruteforce',     # Multiple failed PINs then high amount
                'rapid_burst',        # Repeated high-frequency withdrawals
                'foreign_skim'        # Remote / International clone
            ], p=[0.25, 0.25, 0.20, 0.15, 0.15])
            
            day_of_week = np.random.randint(0, 7)
            
            if fraud_type == 'midnight_drain':
                hour = int(np.random.choice([0, 1, 2, 3, 4, 5]))
                amount = float(np.random.uniform(25000, 50000))
                location_dist_km = round(float(np.random.uniform(30.0, 150.0)), 2)
                time_diff_min = int(np.random.uniform(30, 240))
                failed_pin_count = int(np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1]))
                daily_atm_count = int(np.random.choice([2, 3, 4]))
                atm_type = np.random.choice(['Remote ATM', 'Off-Premise'], p=[0.5, 0.5])
                is_international = int(np.random.choice([0, 1], p=[0.8, 0.2]))
                
            elif fraud_type == 'impossible_travel':
                hour = np.random.randint(0, 24)
                amount = float(np.random.uniform(15000, 45000))
                location_dist_km = round(float(np.random.uniform(400.0, 1200.0)), 2) # e.g. 800km away
                time_diff_min = int(np.random.uniform(10, 45)) # within 10-45 minutes!
                failed_pin_count = int(np.random.choice([0, 1], p=[0.8, 0.2]))
                daily_atm_count = int(np.random.choice([1, 2, 3]))
                atm_type = np.random.choice(['Remote ATM', 'Off-Premise', 'Branch ATM'], p=[0.5, 0.3, 0.2])
                is_international = int(np.random.choice([0, 1], p=[0.7, 0.3]))
                
            elif fraud_type == 'pin_bruteforce':
                hour = np.random.randint(0, 24)
                amount = float(np.random.uniform(20000, 50000))
                location_dist_km = round(float(np.random.uniform(15.0, 80.0)), 2)
                time_diff_min = int(np.random.uniform(1, 20))
                failed_pin_count = int(np.random.choice([2, 3], p=[0.5, 0.5]))
                daily_atm_count = int(np.random.choice([2, 3, 5]))
                atm_type = np.random.choice(['Remote ATM', 'Off-Premise'], p=[0.6, 0.4])
                is_international = int(np.random.choice([0, 1], p=[0.85, 0.15]))
                
            elif fraud_type == 'rapid_burst':
                hour = np.random.randint(0, 24)
                amount = float(np.random.uniform(20000, 40000))
                location_dist_km = round(float(np.random.uniform(20.0, 90.0)), 2)
                time_diff_min = int(np.random.uniform(2, 15)) # 5 mins after previous
                failed_pin_count = int(np.random.choice([0, 1], p=[0.7, 0.3]))
                daily_atm_count = int(np.random.choice([4, 5, 6, 7]))
                atm_type = np.random.choice(['Remote ATM', 'Off-Premise'], p=[0.6, 0.4])
                is_international = 0
                
            else: # foreign_skim
                hour = np.random.randint(0, 24)
                amount = float(np.random.uniform(30000, 50000))
                location_dist_km = round(float(np.random.uniform(1500.0, 5000.0)), 2)
                time_diff_min = int(np.random.uniform(60, 600))
                failed_pin_count = int(np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2]))
                daily_atm_count = int(np.random.choice([1, 2, 3]))
                atm_type = 'Off-Premise'
                is_international = 1

        # Derive physical velocity (km/h)
        # Avoid division by zero
        time_diff_hours = max(time_diff_min / 60.0, 0.05)
        velocity_kmh = round(location_dist_km / time_diff_hours, 2)
        
        # Round amount to 2 decimal places
        amount = round(amount, 2)
        
        records.append({
            'transaction_id': txn_id,
            'card_id': card_id,
            'customer_id': cust_id,
            'amount': amount,
            'hour': hour,
            'day_of_week': day_of_week,
            'location_dist_km': location_dist_km,
            'time_diff_min': time_diff_min,
            'velocity_kmh': velocity_kmh,
            'failed_pin_count': failed_pin_count,
            'daily_atm_count': daily_atm_count,
            'atm_type': atm_type,
            'is_international': is_international,
            'is_fraud': is_fraud
        })
        
    df = pd.DataFrame(records)
    return df

if __name__ == '__main__':
    data_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(data_dir, 'atm_transactions.csv')
    
    print("Generating synthetic ATM transaction dataset...")
    df = generate_atm_transactions(num_records=15000, seed=42)
    df.to_csv(output_path, index=False)
    
    total = len(df)
    frauds = df['is_fraud'].sum()
    fraud_pct = (frauds / total) * 100
    
    print(f"Dataset successfully created: {output_path}")
    print(f"Total Transactions: {total}")
    print(f"Legitimate Transactions: {total - frauds} ({100 - fraud_pct:.2f}%)")
    print(f"Fraudulent Transactions: {frauds} ({fraud_pct:.2f}%)")
