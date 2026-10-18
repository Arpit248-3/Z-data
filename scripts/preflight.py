"""
SignalGate Phase 1 Environment and Data Preflight
Executes automated preflight checks for:
1. System architecture, OS, Python runtime, CPU cores, RAM.
2. Required and optional package dependencies and versions.
3. Git containment verification (verifying local repository scope).
4. Real IEEE-CIS dataset check & fallback to deterministic synthetic fixture.
5. Schema validation, column manifest, row count, fraud prevalence, and SHA-256 checksum.
6. Scikit-learn smoke fit on 10,000 rows (HistGradientBoostingClassifier).
7. Version-safe calibration API probe (FrozenEstimator + CalibratedClassifierCV).
8. Optional SHAP and Snap ML capability probes.
9. Structured reporting to logs/environment.txt with explicit missing-artifact representation.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import yaml

from data.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    TIME_COLUMN,
    FORBIDDEN_MODEL_COLUMNS,
    CATEGORICAL_COLUMNS,
    validate_schema,
    get_feature_columns,
)
from data.generate_fixture import (
    generate_and_save_fixture,
    compute_file_sha256,
    FIXTURE_STATUS,
)


def run_command_capture(cmd: list) -> str:
    """Run a shell command and return trimmed output or 'unavailable'."""
    try:
        # Use shell=True on Windows to support batch/cmd scripts like npm.cmd
        use_shell = platform.system() == "Windows"
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=use_shell)
        return res.stdout.strip()
    except Exception:
        return "unavailable"


def audit_system_environment() -> dict:
    """Collect platform, OS, CPU, memory, and runtime metadata."""
    mem_total_gb = None
    try:
        import psutil
        mem_total_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        # Fallback for Windows systeminfo or wmic
        try:
            out = subprocess.run(
                ["powershell", "-Command", "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB"],
                capture_output=True,
                text=True,
            )
            if out.stdout.strip():
                mem_total_gb = round(float(out.stdout.strip()), 2)
        except Exception:
            mem_total_gb = None

    cpu_count = os.cpu_count()
    processor = platform.processor()

    # Git containment check
    git_root = run_command_capture(["git", "rev-parse", "--show-toplevel"])
    is_git_contained = False
    if git_root != "unavailable":
        git_root_path = Path(git_root).resolve()
        is_git_contained = (git_root_path == PROJECT_ROOT)

    # Check LinuxONE environment
    is_linuxone = (platform.machine().lower() in ["s390x", "s390"])

    return {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": processor,
        "cpu_logical_cores": cpu_count,
        "total_ram_gb": mem_total_gb,
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "project_root": str(PROJECT_ROOT),
        "git_root": git_root,
        "git_contained_in_project": is_git_contained,
        "is_linuxone_runtime": is_linuxone,
        "linuxone_status": "AVAILABLE" if is_linuxone else "NOT_AVAILABLE (x86_64 local dev)",
    }


def audit_dependencies() -> dict:
    """Inspect required and optional Python and Node packages."""
    dep_results = {}

    packages = [
        ("pandas", True),
        ("numpy", True),
        ("scipy", True),
        ("sklearn", True),
        ("joblib", True),
        ("yaml", True),
        ("pytest", True),
        ("fastapi", True),
        ("pydantic", True),
        ("uvicorn", True),
        ("shap", False),
        ("snapml", False),
    ]

    for pkg_name, required in packages:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "installed")
            dep_results[pkg_name] = {
                "installed": True,
                "version": ver,
                "required": required,
                "status": "OK",
            }
        except ImportError:
            dep_results[pkg_name] = {
                "installed": False,
                "version": None,
                "required": required,
                "status": "MISSING" if required else "OPTIONAL_NOT_INSTALLED",
            }

    # Node.js and npm
    node_ver = run_command_capture(["node", "--version"])
    npm_ver = run_command_capture(["npm", "--version"])

    dep_results["node"] = {
        "installed": node_ver != "unavailable",
        "version": node_ver if node_ver != "unavailable" else None,
        "required": True,
        "status": "OK" if node_ver != "unavailable" else "MISSING",
    }
    dep_results["npm"] = {
        "installed": npm_ver != "unavailable",
        "version": npm_ver if npm_ver != "unavailable" else None,
        "required": True,
        "status": "OK" if npm_ver != "unavailable" else "MISSING",
    }

    return dep_results


def check_dataset_and_fixture() -> dict:
    """
    Check for real IEEE-CIS dataset files.
    If unavailable, load/generate the deterministic synthetic smoke fixture.
    """
    # Look for candidate real IEEE-CIS dataset paths
    candidate_real_paths = [
        PROJECT_ROOT / "data" / "train_transaction.csv",
        PROJECT_ROOT / "train_transaction.csv",
        Path.home() / "Downloads" / "train_transaction.csv",
    ]

    real_data_path = None
    for p in candidate_real_paths:
        if p.exists() and p.is_file():
            real_data_path = p
            break

    if real_data_path is not None:
        file_hash = compute_file_sha256(str(real_data_path))
        df = pd.read_csv(real_data_path, nrows=5000)
        is_valid, errors = validate_schema(df, is_synthetic=False)
        return {
            "dataset_type": "REAL_IEEE_CIS",
            "status": "READY",
            "path": str(real_data_path),
            "file_size_bytes": real_data_path.stat().st_size,
            "sha256": file_hash,
            "sample_rows_probed": len(df),
            "schema_valid": is_valid,
            "schema_errors": errors,
            "benchmark_claims_allowed": True,
        }

    # IEEE-CIS is unavailable -> enforce synthetic smoke fixture
    fixture_csv = PROJECT_ROOT / "data" / "synthetic_smoke_fixture.csv"
    fixture_meta_file = PROJECT_ROOT / "data" / "synthetic_smoke_fixture_meta.json"

    if not fixture_csv.exists() or not fixture_meta_file.exists():
        meta = generate_and_save_fixture(n_rows=10000, seed=42, output_dir=str(PROJECT_ROOT / "data"))
    else:
        with open(fixture_meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

    # Verify existing fixture
    df = pd.read_csv(fixture_csv)
    is_valid, errors = validate_schema(df, is_synthetic=True)
    current_hash = compute_file_sha256(str(fixture_csv))

    reproducibility_ok = (current_hash == meta.get("sha256"))

    return {
        "dataset_type": "SYNTHETIC_SMOKE_FIXTURE",
        "status": FIXTURE_STATUS,
        "path": str(fixture_csv),
        "file_size_bytes": fixture_csv.stat().st_size,
        "sha256": current_hash,
        "declared_seed": meta.get("seed", 42),
        "rows": len(df),
        "columns": len(df.columns),
        "target_col": TARGET_COLUMN,
        "fraud_count": int(df[TARGET_COLUMN].sum()),
        "fraud_prevalence": round(float(df[TARGET_COLUMN].mean()), 6),
        "schema_valid": is_valid,
        "schema_errors": errors,
        "reproducibility_verified": reproducibility_ok,
        "benchmark_claims_allowed": False,
        "benchmark_blocker_reason": (
            "Actual IEEE-CIS dataset is not present in workspace or local storage. "
            "All pipeline development and smoke fits operate strictly under SYNTHETIC_SMOKE_ONLY status."
        ),
    }


def run_smoke_fit_and_calibration_probe(fixture_path: str) -> dict:
    """
    Execute smoke fit on the 10,000-row fixture:
    1. Chronological split (60% train, 40% test) by TransactionDT.
    2. HistGradientBoostingClassifier fit.
    3. FrozenEstimator + CalibratedClassifierCV probe (scikit-learn 1.8 compatibility).
    4. SHAP TreeExplainer compatibility probe (non-blocking).
    """
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.preprocessing import OrdinalEncoder
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import brier_score_loss, roc_auc_score

    df = pd.read_csv(fixture_path)
    df = df.sort_values(TIME_COLUMN).reset_index(drop=True)

    split_idx = int(len(df) * 0.6)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    feature_cols = get_feature_columns(df)
    # Ensure forbidden columns are completely excluded
    for col in FORBIDDEN_MODEL_COLUMNS:
        assert col not in feature_cols, f"Leakage violation: {col} present in feature columns!"

    cat_cols = [c for c in CATEGORICAL_COLUMNS if c in feature_cols]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    # Preprocess categoricals via OrdinalEncoder
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    train_cats = encoder.fit_transform(train_df[cat_cols].astype(str))
    test_cats = encoder.transform(test_df[cat_cols].astype(str))

    X_train = np.hstack([train_df[num_cols].values, train_cats])
    y_train = train_df[TARGET_COLUMN].values
    X_test = np.hstack([test_df[num_cols].values, test_cats])
    y_test = test_df[TARGET_COLUMN].values

    # Smoke fit
    t0 = time.perf_counter()
    hgb = HistGradientBoostingClassifier(random_state=42, max_iter=50)
    hgb.fit(X_train, y_train)
    fit_time_ms = round((time.perf_counter() - t0) * 1000, 2)

    raw_probs = hgb.predict_proba(X_test)[:, 1]
    raw_brier = round(float(brier_score_loss(y_test, raw_probs)), 6)
    raw_auc = round(float(roc_auc_score(y_test, raw_probs)), 6)

    # Calibration probe (scikit-learn 1.8 path via FrozenEstimator)
    calibration_info = {}
    try:
        from sklearn.frozen import FrozenEstimator

        cal_split = int(len(train_df) * 0.8)
        X_sub_train = X_train[:cal_split]
        y_sub_train = y_train[:cal_split]
        X_calib = X_train[cal_split:]
        y_calib = y_train[cal_split:]

        sub_model = HistGradientBoostingClassifier(random_state=42, max_iter=50)
        sub_model.fit(X_sub_train, y_sub_train)

        # In sklearn 1.8+, FrozenEstimator signifies prefit status without deprecated cv='prefit'
        frozen_sub = FrozenEstimator(sub_model)
        calibrator = CalibratedClassifierCV(estimator=frozen_sub, method="sigmoid")
        calibrator.fit(X_calib, y_calib)

        cal_probs = calibrator.predict_proba(X_test)[:, 1]
        cal_brier = round(float(brier_score_loss(y_test, cal_probs)), 6)

        calibration_info = {
            "api_path": "sklearn.frozen.FrozenEstimator + CalibratedClassifierCV(method='sigmoid')",
            "method": "sigmoid",
            "compatible": True,
            "calibrated_brier_score": cal_brier,
            "status": "VERIFIED_SUPPORTED",
            "notes": "sklearn 1.8 FrozenEstimator prefit pattern verified",
        }
    except Exception as e:
        # Fallback to standard cross-validated calibration
        try:
            fallback_cal = CalibratedClassifierCV(estimator=HistGradientBoostingClassifier(random_state=42, max_iter=30), method="sigmoid", cv=3)
            fallback_cal.fit(X_train, y_train)
            cal_probs = fallback_cal.predict_proba(X_test)[:, 1]
            cal_brier = round(float(brier_score_loss(y_test, cal_probs)), 6)
            calibration_info = {
                "api_path": "CalibratedClassifierCV(cv=3) fallback",
                "method": "sigmoid",
                "compatible": True,
                "calibrated_brier_score": cal_brier,
                "status": "FALLBACK_VERIFIED",
                "notes": f"Primary FrozenEstimator raised: {e}",
            }
        except Exception as e_fallback:
            calibration_info = {
                "api_path": "none",
                "method": "sigmoid",
                "compatible": False,
                "status": "CALIBRATION_FAILED",
                "error": str(e_fallback),
            }

    # Optional SHAP probe (non-blocking)
    shap_info = {}
    try:
        import shap

        t_shap_0 = time.perf_counter()
        explainer = shap.TreeExplainer(hgb)
        sample_batch = X_test[:10]
        shap_values = explainer.shap_values(sample_batch)
        shap_time_ms = round((time.perf_counter() - t_shap_0) * 1000, 2)
        shap_info = {
            "available": True,
            "version": shap.__version__,
            "explainer": "TreeExplainer",
            "sample_batch_size": len(sample_batch),
            "attribution_latency_ms": shap_time_ms,
            "status": "VERIFIED_COMPATIBLE",
        }
    except Exception as e_shap:
        shap_info = {
            "available": False,
            "version": None,
            "status": "SHAP_PROBE_INCOMPATIBLE_OR_SKIPPED",
            "details": str(e_shap),
        }

    return {
        "model": "HistGradientBoostingClassifier",
        "training_rows": len(train_df),
        "test_rows": len(test_df),
        "feature_count": len(feature_cols),
        "forbidden_columns_excluded": True,
        "fit_time_ms": fit_time_ms,
        "raw_test_brier_score": raw_brier,
        "raw_test_roc_auc": raw_auc,
        "evidence_classification": "SYNTHETIC_DEVELOPMENT_EVIDENCE_ONLY",
        "calibration": calibration_info,
        "shap": shap_info,
    }


def write_environment_log(
    system_env: dict,
    dependencies: dict,
    dataset_info: dict,
    smoke_results: dict,
    output_path: str = "logs/environment.txt",
):
    """Write exhaustive environment report adhering to missing-artifact semantics."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    lines = []
    lines.append("=" * 80)
    lines.append("SIGNALGATE ENVIRONMENT AUDIT & PHASE 1 PREFLIGHT REPORT")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    lines.append(f"Status: {dataset_info['status']}")
    lines.append("")

    lines.append("1. SYSTEM & PLATFORM")
    lines.append(f"  Operating System      : {system_env['os_name']} {system_env['os_release']} ({system_env['os_version']})")
    lines.append(f"  Architecture          : {system_env['architecture']}")
    lines.append(f"  Processor             : {system_env['processor']}")
    lines.append(f"  Logical CPU Cores     : {system_env['cpu_logical_cores']}")
    lines.append(f"  Total RAM (GB)        : {system_env['total_ram_gb']}")
    lines.append(f"  Python Version        : {system_env['python_version']}")
    lines.append(f"  Python Executable     : {system_env['python_executable']}")
    lines.append(f"  Project Root          : {system_env['project_root']}")
    lines.append(f"  Git Root              : {system_env['git_root']}")
    lines.append(f"  Git Scope Contained   : {system_env['git_contained_in_project']}")
    lines.append(f"  LinuxONE Community VM : {system_env['linuxone_status']}")
    lines.append("")

    lines.append("2. INSTALLED DEPENDENCY MATRIX")
    for dep, info in dependencies.items():
        ver_str = info["version"] if info["version"] is not None else "null"
        lines.append(f"  - {dep:<14}: version={ver_str:<12} status={info['status']:<15} required={info['required']}")
    lines.append("")

    lines.append("3. DATASET AND FIXTURE STATUS")
    lines.append(f"  Dataset Type          : {dataset_info['dataset_type']}")
    lines.append(f"  Status Tag            : {dataset_info['status']}")
    lines.append(f"  Path                  : {dataset_info['path']}")
    lines.append(f"  SHA-256 Checksum      : {dataset_info['sha256']}")
    lines.append(f"  Row Count             : {dataset_info.get('rows', 'null')}")
    lines.append(f"  Column Count          : {dataset_info.get('columns', 'null')}")
    lines.append(f"  Fraud Count           : {dataset_info.get('fraud_count', 'null')}")
    lines.append(f"  Fraud Prevalence      : {dataset_info.get('fraud_prevalence', 'null')}")
    lines.append(f"  Schema Validated      : {dataset_info['schema_valid']}")
    lines.append(f"  Reproducibility Check : {dataset_info.get('reproducibility_verified', 'null')}")
    lines.append(f"  Benchmark Claims OK   : {dataset_info['benchmark_claims_allowed']}")
    if "benchmark_blocker_reason" in dataset_info:
        lines.append(f"  Blocker Notice        : {dataset_info['benchmark_blocker_reason']}")
    lines.append("")

    lines.append("4. SMOKE FIT & CALIBRATION RESULTS (SYNTHETIC EVIDENCE ONLY)")
    lines.append(f"  Evidence Classification : {smoke_results['evidence_classification']}")
    lines.append(f"  Model Tested            : {smoke_results['model']}")
    lines.append(f"  Train Rows / Test Rows  : {smoke_results['training_rows']} / {smoke_results['test_rows']}")
    lines.append(f"  Feature Count Evaluated : {smoke_results['feature_count']}")
    lines.append(f"  Forbidden Leakage Check : PASSED (Excluded: {', '.join(FORBIDDEN_MODEL_COLUMNS)})")
    lines.append(f"  Smoke Fit Latency (ms)  : {smoke_results['fit_time_ms']}")
    lines.append(f"  Raw Test Brier Score    : {smoke_results['raw_test_brier_score']}")
    lines.append(f"  Raw Test ROC-AUC        : {smoke_results['raw_test_roc_auc']}")
    lines.append(f"  Calibration API Status  : {smoke_results['calibration']['status']}")
    lines.append(f"  Calibration Path        : {smoke_results['calibration']['api_path']}")
    lines.append(f"  Calibrated Brier Score  : {smoke_results['calibration'].get('calibrated_brier_score', 'null')}")
    lines.append(f"  SHAP Probe Status       : {smoke_results['shap']['status']}")
    if smoke_results['shap'].get('attribution_latency_ms') is not None:
        lines.append(f"  SHAP Latency (10 rows)  : {smoke_results['shap']['attribution_latency_ms']} ms")
    lines.append("")

    lines.append("5. MISSING-ARTIFACT READINESS MATRIX")
    lines.append("  - Real IEEE-CIS Dataset  : null [STATUS: PENDING_USER_SUPPLY]")
    lines.append("  - Trained Policy Router  : null [STATUS: PHASE_4_SCHEDULED]")
    lines.append("  - Results JSON Artifact  : null [STATUS: PHASE_5_SCHEDULED]")
    lines.append("  - FastAPI Endpoints      : null [STATUS: PHASE_6_SCHEDULED]")
    lines.append("  - React Frontend         : null [STATUS: PHASE_7_SCHEDULED]")
    lines.append("  - IBM Snap ML Engine     : null [STATUS: NOT_APPLICABLE_ON_X86]")
    lines.append("=" * 80)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    print("=" * 70)
    print("SignalGate Phase 1 Preflight Verification")
    print("=" * 70)

    # 1. System environment
    print("[1/5] Auditing system environment and git scope...")
    sys_env = audit_system_environment()
    print(f"      OS: {sys_env['os_name']} {sys_env['os_release']} | Arch: {sys_env['architecture']} | Cores: {sys_env['cpu_logical_cores']}")
    print(f"      RAM: {sys_env['total_ram_gb']} GB | Python: {sys_env['python_version']}")
    print(f"      Git Contained in Project Root: {sys_env['git_contained_in_project']} ({sys_env['project_root']})")
    if not sys_env["git_contained_in_project"]:
        print("      [WARNING] Git root is not scoped to project root!")

    # 2. Dependencies
    print("[2/5] Inspecting dependency matrix...")
    deps = audit_dependencies()
    missing_required = [k for k, v in deps.items() if v["required"] and not v["installed"]]
    if missing_required:
        print(f"      [ERROR] Required dependencies missing: {missing_required}")
        sys.exit(1)
    print(f"      scikit-learn: {deps['sklearn']['version']} | pandas: {deps['pandas']['version']} | numpy: {deps['numpy']['version']}")
    print(f"      Node.js: {deps['node']['version']} | npm: {deps['npm']['version']}")

    # 3. Dataset & synthetic fixture
    print("[3/5] Checking IEEE-CIS dataset and synthetic development fixture...")
    data_info = check_dataset_and_fixture()
    print(f"      Dataset: {data_info['dataset_type']} | Status: {data_info['status']}")
    print(f"      Path: {data_info['path']} ({data_info['file_size_bytes']} bytes)")
    print(f"      Rows: {data_info.get('rows')} | Cols: {data_info.get('columns')} | Fraud: {data_info.get('fraud_count')} ({data_info.get('fraud_prevalence', 0)*100:.2f}%)")
    print(f"      SHA-256: {data_info['sha256']}")
    if not data_info["schema_valid"]:
        print(f"      [ERROR] Schema errors: {data_info['schema_errors']}")
        sys.exit(1)
    print("      Schema validation: PASSED")
    print(f"      Reproducibility: {data_info.get('reproducibility_verified')}")

    # 4. Smoke fit & calibration probe
    print("[4/5] Executing smoke fit on 10,000-row fixture & probing calibration...")
    smoke_res = run_smoke_fit_and_calibration_probe(data_info["path"])
    print(f"      Model: {smoke_res['model']} | Train: {smoke_res['training_rows']} rows | Fit time: {smoke_res['fit_time_ms']} ms")
    print(f"      Raw Test Brier: {smoke_res['raw_test_brier_score']} | ROC-AUC: {smoke_res['raw_test_roc_auc']}")
    print(f"      Calibration: {smoke_res['calibration']['status']} via {smoke_res['calibration']['api_path']}")
    print(f"      SHAP Compatibility: {smoke_res['shap']['status']}")

    # 5. Write environment report
    print("[5/5] Generating logs/environment.txt audit artifact...")
    env_log_path = PROJECT_ROOT / "logs" / "environment.txt"
    write_environment_log(sys_env, deps, data_info, smoke_res, str(env_log_path))
    print(f"      Preflight report written to: {env_log_path}")

    print("=" * 70)
    print("Phase 1 Preflight COMPLETED SUCCESSFULLY (SYNTHETIC_SMOKE_ONLY)")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
