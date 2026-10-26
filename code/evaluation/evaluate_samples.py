"""
Evaluation script for Ghost Data Still Exists.
Compares a prediction CSV against dataset/sample_output.csv.
Computes case-level status accuracy, step-level precision/recall, field accuracy, and sequence accuracy.
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_GOLD_PATH = REPO_ROOT / "dataset" / "sample_output.csv"


def load_csv(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {r["case_id"]: r for r in csv.DictReader(f)}


def evaluate(pred_path: Path, gold_path: Path = SAMPLE_GOLD_PATH) -> dict:
    gold = load_csv(gold_path)
    pred = load_csv(pred_path)

    total_cases = len(gold)
    status_matches = 0
    exact_step_matches = 0
    total_gold_steps = 0
    total_pred_steps = 0
    matched_steps = 0
    field_counts = {"phase": 0, "system_id": 0, "resource_id": 0, "operation": 0, "state": 0, "evidence_id": 0}
    field_matches = {"phase": 0, "system_id": 0, "resource_id": 0, "operation": 0, "state": 0, "evidence_id": 0}
    sequence_matches = 0

    discrepancies = []

    for cid, g_row in gold.items():
        p_row = pred.get(cid)
        if not p_row:
            discrepancies.append((cid, "MISSING_IN_PREDICTION", "", ""))
            continue

        g_status = g_row["deletion_status"]
        p_status = p_row["deletion_status"]
        st_match = g_status == p_status
        if st_match:
            status_matches += 1

        try:
            g_steps = json.loads(g_row["steps_json"])
        except Exception:
            g_steps = []
        try:
            p_steps = json.loads(p_row["steps_json"])
        except Exception:
            p_steps = []

        total_gold_steps += len(g_steps)
        total_pred_steps += len(p_steps)

        # Check exact sequence match
        seq_match = True
        if len(g_steps) != len(p_steps):
            seq_match = False
        else:
            for gs, ps in zip(g_steps, p_steps):
                for k in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                    field_counts[k] += 1
                    if gs.get(k) == ps.get(k):
                        field_matches[k] += 1
                    else:
                        seq_match = False

        if seq_match and st_match:
            exact_step_matches += 1
            sequence_matches += 1
        elif len(g_steps) == len(p_steps) and seq_match:
            sequence_matches += 1
        else:
            discrepancies.append((cid, f"status: {g_status} vs {p_status}", f"gold_steps={len(g_steps)}", f"pred_steps={len(p_steps)}"))

    status_acc = status_matches / total_cases if total_cases else 0.0
    exact_acc = exact_step_matches / total_cases if total_cases else 0.0
    seq_acc = sequence_matches / total_cases if total_cases else 0.0

    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Cases:               {total_cases}")
    print(f"Status Accuracy:           {status_matches}/{total_cases} ({status_acc*100:.1f}%)")
    print(f"Exact Sequence Accuracy:   {exact_step_matches}/{total_cases} ({exact_acc*100:.1f}%)")
    print(f"Total Gold Steps:          {total_gold_steps}")
    print(f"Total Pred Steps:          {total_pred_steps}")
    print("\nField-Level Accuracy (for cases with equal step count):")
    for k in field_counts:
        c = field_counts[k]
        m = field_matches[k]
        pct = (m / c * 100) if c else 0.0
        print(f"  {k:15s}: {m}/{c} ({pct:.1f}%)")

    if discrepancies:
        print(f"\nDiscrepancies ({len(discrepancies)} cases):")
        for d in discrepancies[:15]:
            print(f"  {d[0]}: {d[1]} | {d[2]} | {d[3]}")
        if len(discrepancies) > 15:
            print(f"  ... and {len(discrepancies) - 15} more.")

    return {
        "status_accuracy": status_acc,
        "exact_accuracy": exact_acc,
        "sequence_accuracy": seq_acc,
        "status_matches": status_matches,
        "exact_step_matches": exact_step_matches,
        "total_cases": total_cases,
    }


if __name__ == "__main__":
    pred_file = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "sample_output_pred.csv"
    evaluate(pred_file)
