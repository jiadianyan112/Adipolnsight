#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposure", default="Liver_PDFF")
    parser.add_argument("--outcome", default="Osteoporosis")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    beta = round(random.uniform(0.1, 0.3), 3)
    se = round(random.uniform(0.05, 0.1), 3)

    csv = "method,beta,se,or,ci_lower,ci_upper,p_value\n"
    csv += f"IVW,{beta},{se},{round(random.uniform(1.1, 1.4), 2)},{round(random.uniform(1.02, 1.1), 2)},{round(random.uniform(1.2, 1.5), 2)},{random.uniform(0.001, 0.02):.4f}\n"
    with open(os.path.join(args.output_dir, "mr_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "heterogeneity.csv"), "w") as f:
        f.write("method,Q,Q_df,Q_pval\nIVW,15.2,10,0.12\n")

    with open(os.path.join(args.output_dir, "pleiotropy.csv"), "w") as f:
        f.write("egger_intercept,se,pval\n0.002,0.004,0.62\n")

    summary = {
        "exposure": args.exposure, "outcome": args.outcome, "method": "IVW",
        "beta": beta, "or": round(random.uniform(1.1, 1.4), 2),
        "ci_lower": round(random.uniform(1.02, 1.1), 2),
        "ci_upper": round(random.uniform(1.2, 1.5), 2),
        "p_value": round(random.uniform(0.001, 0.02), 4),
        "cochran_q_p": round(random.uniform(0.1, 0.5), 2),
        "egger_intercept_p": round(random.uniform(0.3, 0.7), 2),
    }
    with open(os.path.join(args.output_dir, "mr_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_mr] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["mr_results.csv", "heterogeneity.csv", "pleiotropy.csv", "mr_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
