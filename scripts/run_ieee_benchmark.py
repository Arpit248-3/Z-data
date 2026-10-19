"""SignalGate IBM Architecture Integration — IEEE-CIS Benchmark CLI Script.

Executes the Phase 10 benchmark runner, verifying pre-evaluation freeze hashes,
evaluating Baseline B2 and Candidate P5 across budgets, executing 1,000 paired
bootstrap resamples, benchmarking latency, and writing results/ieee_cis_v1/benchmark_results.json.

Governing Specification: docs/ibm_architecture_integration_master_spec.md § N
Requirements Covered: EVAL-02
"""

import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integrations.ibm_architecture.evaluation.benchmark_runner import IeeeBenchmarkRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    print("=" * 75)
    print("SIGNALGATE PHASE 10: IEEE-CIS BENCHMARK EVALUATION & ACCEPTANCE GATES")
    print("=" * 75)

    runner = IeeeBenchmarkRunner(project_root=PROJECT_ROOT)
    results = runner.run_benchmark()

    print("\n" + "=" * 75)
    print("BENCHMARK EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Total Transactions Evaluated: {results['test_partition_summary']['total_transactions']:,}")
    print(f"Total Fraud Cases (Positive): {results['test_partition_summary']['total_frauds']:,} ({results['test_partition_summary']['prevalence']*100:.3f}%)")
    print("\nModel Accuracy on Held-Out Test Partition:")
    ens_acc = results["overall_model_accuracy"]["heterogeneous_ensemble"]
    b2_acc = results["overall_model_accuracy"]["baseline_b2"]
    print(f"  - Ensemble ROC-AUC: {ens_acc['roc_auc']:.4f} | PR-AUC: {ens_acc['pr_auc']:.4f} | ECE: {ens_acc['expected_calibration_error']:.4f}")
    print(f"  - Baseline B2 ROC-AUC: {b2_acc['roc_auc']:.4f} | PR-AUC: {b2_acc['pr_auc']:.4f} | ECE: {b2_acc['expected_calibration_error']:.4f}")

    print("\nBudget Sweep (B2 vs P5, lambda=0.0):")
    for mult, res in results["budget_sweep"].items():
        b2_rec = res["baseline_b2"]["recall_at_touched"] * 100.0
        p5_rec = res["candidate_p5"]["recall_at_touched"] * 100.0
        cap = res["review_capacity_slots"]
        gain = res["recall_gain_percentage_points"]
        print(f"  - {mult:>4} (Slots: {cap:>5}): B2 Recall = {b2_rec:6.2f}% | P5 Recall = {p5_rec:6.2f}% | Gain = {gain:+5.2f} pp")

    print("\nPaired Bootstrap (Primary 1.5x Budget, 1,000 Resamples):")
    boot = results["primary_bootstrap_1_5x"]
    print(f"  - 95% Confidence Interval: [{boot['ci_lower']:+.6f}, {boot['ci_upper']:+.6f}]")
    print(f"  - Point Estimate Diff:     {boot['point_estimate_diff']:+.6f}")
    print(f"  - Conclusive:              {boot['is_conclusive']} ({boot['conclusion']})")

    print("\nHost AMD64 CPU Latency Micro-Benchmark:")
    lat = results["latency_benchmarks"]
    print(f"  - Single-Transaction Mean: {lat['single_transaction']['mean_ms']:.2f} ms | p95: {lat['single_transaction']['p95_ms']:.2f} ms | p99: {lat['single_transaction']['p99_ms']:.2f} ms")
    print(f"  - Batch-of-32 p95:         {lat['batch_of_32']['p95_ms']:.2f} ms ({lat['batch_of_32']['per_row_mean_ms']:.2f} ms/row)")

    print("\nAcceptance Criteria Scorecard (Master Spec § N Truthful Standards):")
    for ac_id, ac in results["acceptance_criteria_scorecard"].items():
        print(f"  [{ac['status']:<5}] {ac_id}: {ac['observed']} (Target: {ac['target']})")

    print("=" * 75)
    print(f"Benchmark results successfully saved to: {PROJECT_ROOT / 'results' / 'ieee_cis_v1' / 'benchmark_results.json'}")
    print("=" * 75)


if __name__ == "__main__":
    main()
