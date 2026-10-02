"""
Model Training & Evaluation Pipeline for ATM Fraud Detection
Handles severe class imbalance using class weights and evaluates with Precision, Recall, PR-AUC, and Confusion Matrix.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score
)

def train_and_evaluate():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'atm_transactions.csv')
    model_dir = os.path.join(base_dir, 'model')
    os.makedirs(model_dir, exist_ok=True)

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    # Feature definitions
    numerical_features = [
        'amount',
        'hour',
        'day_of_week',
        'location_dist_km',
        'time_diff_min',
        'velocity_kmh',
        'failed_pin_count',
        'daily_atm_count'
    ]
    categorical_features = ['atm_type']
    binary_features = ['is_international']

    feature_cols = numerical_features + categorical_features + binary_features
    X = df[feature_cols]
    y = df['is_fraud']

    # Stratified split to maintain fraud ratio in train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train size: {len(X_train)} (Frauds: {y_train.sum()})")
    print(f"Test size:  {len(X_test)} (Frauds: {y_test.sum()})")

    # Build preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(drop='first', sparse_output=False), categorical_features),
            ('bin', 'passthrough', binary_features)
        ]
    )

    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Get transformed feature names
    cat_encoder = preprocessor.named_transformers_['cat']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()
    all_feature_names = numerical_features + cat_feature_names + binary_features

    # Train Baseline 1: Logistic Regression with balanced class weights
    print("\n--- Training Model 1: Balanced Logistic Regression ---")
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train_proc, y_train)
    lr_preds = lr.predict(X_test_proc)
    lr_probs = lr.predict_proba(X_test_proc)[:, 1]

    lr_prec = precision_score(y_test, lr_preds)
    lr_rec = recall_score(y_test, lr_preds)
    lr_f1 = f1_score(y_test, lr_preds)
    lr_roc = roc_auc_score(y_test, lr_probs)
    lr_pr_auc = average_precision_score(y_test, lr_probs)
    print(f"Logistic Regression -> Precision: {lr_prec:.4f}, Recall: {lr_rec:.4f}, F1: {lr_f1:.4f}, PR-AUC: {lr_pr_auc:.4f}")

    # Train Model 2: Balanced Random Forest Classifier
    print("\n--- Training Model 2: Balanced Random Forest ---")
    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        class_weight='balanced_subsample',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train_proc, y_train)
    rf_preds = rf.predict(X_test_proc)
    rf_probs = rf.predict_proba(X_test_proc)[:, 1]

    rf_prec = precision_score(y_test, rf_preds)
    rf_rec = recall_score(y_test, rf_preds)
    rf_f1 = f1_score(y_test, rf_preds)
    rf_roc = roc_auc_score(y_test, rf_probs)
    rf_pr_auc = average_precision_score(y_test, rf_probs)
    print(f"Random Forest       -> Precision: {rf_prec:.4f}, Recall: {rf_rec:.4f}, F1: {rf_f1:.4f}, PR-AUC: {rf_pr_auc:.4f}")

    cm = confusion_matrix(y_test, rf_preds)
    tn, fp, fn, tp = cm.ravel()
    print("\nRandom Forest Confusion Matrix on Test Set (3000 transactions):")
    print(f"  True Negatives  (Legitimate approved): {tn}")
    print(f"  False Positives (Legitimate blocked) : {fp}")
    print(f"  False Negatives (Fraud missed!)      : {fn}")
    print(f"  True Positives  (Fraud stopped!)     : {tp}")

    # Feature Importance analysis
    importances = rf.feature_importances_
    feat_importance_dict = sorted(
        zip(all_feature_names, importances), key=lambda x: x[1], reverse=True
    )
    print("\nTop Predictors of ATM Fraud:")
    for feat, imp in feat_importance_dict[:6]:
        print(f"  - {feat}: {imp * 100:.2f}%")

    # Serialize Preprocessor & Model
    preprocessor_path = os.path.join(model_dir, 'preprocessor.joblib')
    model_path = os.path.join(model_dir, 'fraud_model.joblib')
    metrics_path = os.path.join(model_dir, 'model_metrics.json')

    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(rf, model_path)

    metrics_payload = {
        'model_name': 'Balanced Random Forest Classifier',
        'test_size': len(y_test),
        'fraud_test_count': int(y_test.sum()),
        'metrics': {
            'precision': round(float(rf_prec), 4),
            'recall': round(float(rf_rec), 4),
            'f1_score': round(float(rf_f1), 4),
            'roc_auc': round(float(rf_roc), 4),
            'pr_auc': round(float(rf_pr_auc), 4)
        },
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        },
        'feature_importances': [
            {'feature': f, 'importance': round(float(imp), 4)} for f, imp in feat_importance_dict
        ],
        'feature_columns': feature_cols,
        'all_feature_names': all_feature_names
    }

    with open(metrics_path, 'w') as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"\nArtifacts successfully saved:")
    print(f"  - {preprocessor_path}")
    print(f"  - {model_path}")
    print(f"  - {metrics_path}")

if __name__ == '__main__':
    train_and_evaluate()
