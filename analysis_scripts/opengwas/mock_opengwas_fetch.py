#!/usr/bin/env python3
import argparse, json, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcome-id", default="ukb-b-12141")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)

    tsv = "SNP\tBETA\tSE\tP\n"
    for i in range(12):
        tsv += f"rs{i+1000}\t0.05\t0.02\t0.04\n"
    with open(os.path.join(args.output_dir, "outcome_summary_stats.tsv"), "w") as f:
        f.write(tsv)

    with open(os.path.join(args.output_dir, "harmonised_preview.csv"), "w") as f:
        f.write("SNP,exposure_beta,outcome_beta,harmonised\n")
        f.write("rs1001,0.05,0.04,True\n")

    summary = {
        "outcome_id": args.outcome_id,
        "outcome_name": "Osteoporosis",
        "matched_snps": 12,
        "proxy_snps_used": 0,
        "source": "Mock IEU OpenGWAS",
    }
    with open(os.path.join(args.output_dir, "opengwas_metadata.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_opengwas] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["outcome_summary_stats.tsv", "harmonised_preview.csv", "opengwas_metadata.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
