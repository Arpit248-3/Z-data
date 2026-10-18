"""Tests for SignalGate Evaluation Metrics Module."""

import numpy as np
import pytest
from eval.metrics import (
    calculate_binary_metrics,
    calculate_policy_metrics,
    recall_at_touched,
    value_missed,
    value_caught,
    ece,
    calculate_pr_auc,
)


def test_recall_at_touched_hand_calculated():
    # 5 transactions, 2 frauds (indices 1, 3)
    y_true = [0, 1, 0, 1, 0]
    # Touched mask escalates indices 1 and 2 (1 fraud caught, 1 false alarm)
    touched = [False, True, True, False, False]
    rec = recall_at_touched(y_true, touched)
    # Total fraud = 2, caught = 1 -> recall = 0.5
    assert rec == pytest.approx(0.5, abs=1e-6)

    # Edge case: zero fraud
    assert recall_at_touched([0, 0, 0], [True, False, True]) == 0.0


def test_value_caught_and_missed_hand_calculated():
    # Frauds at index 0 ($100), index 2 ($250), index 4 ($50)
    y_true = [1, 0, 1, 0, 1]
    amounts = [100.0, 500.0, 250.0, 30.0, 50.0]
    # Escalate index 0 and 1
    touched = [True, True, False, False, False]

    # Caught fraud: index 0 ($100)
    caught = value_caught(y_true, amounts, touched)
    assert caught == pytest.approx(100.0, abs=1e-5)

    # Missed fraud: index 2 ($250) + index 4 ($50) = $300
    missed = value_missed(y_true, amounts, touched)
    assert missed == pytest.approx(300.0, abs=1e-5)


def test_calculate_binary_metrics_contingency():
    # 10 rows: 3 frauds (indices 0, 1, 2), 7 non-frauds
    y_true = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    # Escalated: 0 (TP), 1 (TP), 3 (FP), 4 (FP)
    # Not escalated: 2 (FN), 5 (TN), 6 (TN), 7 (TN), 8 (TN), 9 (TN)
    escalated = [True, True, False, True, True, False, False, False, False, False]

    m = calculate_binary_metrics(y_true, escalated)
    assert m["total_transactions"] == 10
    assert m["total_positives"] == 3
    assert m["total_negatives"] == 7
    assert m["tp"] == 2
    assert m["fp"] == 2
    assert m["fn"] == 1
    assert m["tn"] == 5
    assert m["recall"] == pytest.approx(2 / 3, abs=1e-5)
    assert m["missed_fraud_rate"] == pytest.approx(1 / 3, abs=1e-5)
    assert m["precision"] == pytest.approx(2 / 4, abs=1e-5)
    assert m["fpr"] == pytest.approx(2 / 7, abs=1e-5)


def test_calculate_policy_metrics_multi_action_and_governor_discipline():
    # 8 transactions: frauds at indices 0, 1, 2
    y_true = [1, 1, 1, 0, 0, 0, 0, 0]
    amounts = [100.0, 200.0, 300.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    # Actions: 1 alert, 2 reviews, 1 deferred, 4 routine
    actions = [
        "FRAUD_ALERT",     # idx 0: fraud (TP)
        "MANUAL_REVIEW",    # idx 1: fraud (TP)
        "ROUTINE",          # idx 2: fraud (FN, confident miss!)
        "MANUAL_REVIEW",    # idx 3: non-fraud (FP)
        "DEFERRED",         # idx 4: non-fraud (overflow, not touched!)
        "ROUTINE",          # idx 5: non-fraud (TN)
        "ROUTINE",          # idx 6: non-fraud (TN)
        "ROUTINE",          # idx 7: non-fraud (TN)
    ]
    p_scores = [0.95, 0.75, 0.05, 0.72, 0.65, 0.02, 0.03, 0.01]

    m = calculate_policy_metrics(y_true, actions, amounts=amounts, p_scores=p_scores)

    # Action counts
    assert m["alert_count"] == 1
    assert m["review_count"] == 2
    assert m["routine_count"] == 4
    assert m["deferred_count"] == 1

    # Touched count strictly ALERT + REVIEW = 3
    assert m["touched_count"] == 3
    assert m["touched_rate"] == pytest.approx(3 / 8, abs=1e-5)
    assert m["deferred_rate"] == pytest.approx(1 / 8, abs=1e-5)

    # Contingency (touched = alert | review)
    assert m["tp"] == 2  # idx 0, 1
    assert m["fp"] == 1  # idx 3
    assert m["fn"] == 1  # idx 2
    assert m["recall_at_touched"] == pytest.approx(2 / 3, abs=1e-5)
    assert m["precision"] == pytest.approx(2 / 3, abs=1e-5)

    # Confident miss (fraud in ROUTINE lane): idx 2
    assert m["confident_miss_count"] == 1
    # Routine fraud rate: 1 fraud out of 4 routine = 0.25
    assert m["routine_fraud_rate"] == pytest.approx(1 / 4, abs=1e-5)

    # Amount metrics: Total fraud = $100 + $200 + $300 = $600
    assert m["amount_total_fraud"] == 600.0
    # Caught fraud = $100 + $200 = $300
    assert m["amount_fraud_caught"] == 300.0
    # Missed fraud = $300
    assert m["amount_fraud_missed"] == 300.0
    assert m["amount_caught_pct"] == pytest.approx(0.5, abs=1e-5)

    # Probabilistic metrics exist
    assert "pr_auc" in m
    assert "ece" in m
