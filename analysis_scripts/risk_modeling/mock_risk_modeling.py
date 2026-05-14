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

    csv = "model,beta,se,p_value\nOLS,0.35,0.08,0.0001\n"
    with open(os.path.join(args.output_dir, "ols_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "rcs_results.csv"), "w") as f:
        f.write("knot,estimate,se,p_value\n1,0.30,0.07,0.001\n2,0.40,0.09,0.0005\n")

    summary = {
        "pdff_quartile": "Q4", "osteopenia_aor": round(random.uniform(1.1, 1.2), 2),
        "osteoporosis_aor": round(random.uniform(1.2, 1.3), 2),
        "risk_level": "High", "model_type": "OLS + RCS + Multinomial Logistic",
    }
    with open(os.path.join(args.output_dir, "risk_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_risk_modeling] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["ols_results.csv", "rcs_results.csv", "risk_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
