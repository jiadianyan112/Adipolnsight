# Real Module Replacement Guide

Each mock script defines a contract boundary through its CLI interface and output JSON schema.
To replace a mock with a real module:

1. Write the real script with the same CLI arguments
2. Keep the stdout JSON format identical
3. Update the SkillRunner's `script_path` in `backend/app/tasks/`

## Replacement Map

| Module | Mock | Real Replacement |
|--------|------|-----------------|
| Segmentation | mock_segmentation.py | TSSA-UNet inference script |
| GWAS | mock_gwas.py | REGENIE pipeline |
| OpenGWAS | mock_opengwas_fetch.py | IEU OpenGWAS API client |
| MR | mock_mr.py | TwoSampleMR R script |
| Mediation MR | mock_mediation_mr.py | pQTL + TwoStepMR |
| Risk Modeling | mock_risk_modeling.py | Clinical risk model |

The contract remains: accept input JSON, produce output JSON on stdout, write files to output dir.
