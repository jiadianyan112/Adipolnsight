#!/usr/bin/env python3
import argparse, json, time, os, glob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.3)

    md = f"# AdipoInsight Research Report\n\nProject ID: {args.project_id}\n\nAll analysis steps completed.\n"
    out_path = os.path.join(args.output_dir, "final_report.md")
    with open(out_path, "w") as f:
        f.write(md)

    print(f"[mock_report] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success",
        "summary": {"report_path": out_path, "sections": 8},
        "output_files": ["final_report.md"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
