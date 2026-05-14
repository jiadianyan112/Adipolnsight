#!/usr/bin/env python3
import argparse, json, random, time, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phenotype", default="Liver_PDFF")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    time.sleep(0.5)
    n_snps = 12

    tsv = "SNP\tCHR\tBP\tEA\tOA\tBETA\tSE\tP\n"
    for i in range(n_snps):
        tsv += f"rs{i+1000}\t{random.randint(1,22)}\t{random.randint(100000,250000000)}\tA\tG\t{round(random.uniform(-0.3, 0.3), 4)}\t{round(random.uniform(0.01, 0.05), 4)}\t{random.uniform(1e-8, 1e-4):.2e}\n"

    with open(os.path.join(args.output_dir, "gwas_summary_stats.tsv"), "w") as f:
        f.write(tsv)

    with open(os.path.join(args.output_dir, "lead_snps.csv"), "w") as f:
        f.write("SNP,CHR,BP,P\n")
        f.write("rs1001,3,123456,1.2e-10\n")

    with open(os.path.join(args.output_dir, "significant_loci.csv"), "w") as f:
        f.write("locus,chr,start,end,lead_snp,n_snps\n")
        f.write("1,3,100000,200000,rs1001,50\n")

    summary = {
        "phenotype": args.phenotype,
        "sample_size": 40484,
        "significant_loci_count": 18,
        "lead_snps_count": n_snps,
        "lambda_gc": round(random.uniform(1.00, 1.05), 2),
    }
    with open(os.path.join(args.output_dir, "gwas_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[mock_gwas] Task {args.task_id} completed")
    output = {
        "task_id": args.task_id, "status": "success", "summary": summary,
        "output_files": ["gwas_summary_stats.tsv", "lead_snps.csv", "significant_loci.csv", "gwas_summary.json"],
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
