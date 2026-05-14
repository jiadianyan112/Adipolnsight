# Mock Skills Reference

Each mock script is a standalone Python CLI:

```bash
python mock_xxx.py --output-dir <path> --task-id <id> [--other-args]
```

## Output Protocol

- stdout: log lines followed by one JSON line at the end
- exit code: 0 = success
- all data files go to --output-dir

## Scripts

| Script | Key Output |
|--------|-----------|
| mock_segmentation.py | segmentation_metrics.json, fat_quantification.csv |
| mock_gwas.py | gwas_summary_stats.tsv, lead_snps.csv, gwas_summary.json |
| mock_opengwas_fetch.py | outcome_summary_stats.tsv, opengwas_metadata.json |
| mock_mr.py | mr_results.csv, mr_summary.json |
| mock_mediation_mr.py | mediation_results.csv, mediation_summary.json |
| mock_risk_modeling.py | ols_results.csv, risk_summary.json |
| mock_report.py | final_report.md |
