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

    proteins = ["ACY1", "H6PD", "SHBG", "ADH1A", "POR", "NAAA"]
    csv = "protein,beta_a,beta_b,indirect_effect,proportion_mediated,p_mediation\n"
    top_mediators = []
    for p in proteins:
        ba = round(random.uniform(0.01, 0.15), 3)
        bb = round(random.uniform(0.005, 0.03), 3)
        ie = round(ba * bb, 4)
        pm = round(random.uniform(0.5, 5.0), 3)
        pval = round(random.uniform(0.0001, 0.01), 4)
        csv += f"{p},{ba},{bb},{ie},{pm},{pval}\n"
        top_mediators.append({"protein": p, "beta_a": ba, "beta_b": bb, "indirect_effect": ie, "proportion_mediated": pm, "p_mediation": pval})

    with open(os.path.join(args.output_dir, "mediation_results.csv"), "w") as f:
        f.write(csv)

    with open(os.path.join(args.output_dir, "candidate_proteins.csv"), "w") as f:
        f.write("protein\n" + "\n".join(proteins) + "\n")

    summary = {
        "exposure": args.exposure, "outcome": args.outcome,
        "mediator_source": "deCODE_plasma_proteins",
        "tested_proteins": 4907, "significant_mediators": len(proteins),
        "top_mediators": top_mediators,
    }
    with open(os.path.join(args.output_dir, "mediation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_mediation_mr] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": {
            "exposure": args.exposure, "outcome": args.outcome,
            "mediator_source": "deCODE_plasma_proteins",
            "tested_proteins": 4907, "significant_mediators": len(proteins),
        },
        "output_files": ["mediation_results.csv", "candidate_proteins.csv", "mediation_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
