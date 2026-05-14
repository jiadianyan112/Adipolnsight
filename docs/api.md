# AdipoInsight API Reference

Base URL: `http://localhost:8000/api/v1`

## Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects | Create project |
| GET | /projects | List projects |
| GET | /projects/{id} | Get project |
| DELETE | /projects/{id} | Delete project |

## Files

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects/{id}/files | Upload file |
| GET | /projects/{id}/files | List files |
| GET | /files/{id}/download | Download file |

## Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | /tasks | Create and run task |
| GET | /tasks/{id} | Get task status |
| GET | /projects/{id}/tasks | List project tasks |
| POST | /tasks/{id}/rerun | Rerun task |
| POST | /projects/{id}/pipeline/run-all | Run full pipeline |

## Results

| Method | Path | Description |
|--------|------|-------------|
| GET | /tasks/{id}/result | Get task result |
| GET | /projects/{id}/results | List project results |

## Reports

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects/{id}/reports/generate | Generate report |
| GET | /reports/{id} | Get report |

## Demo

| Method | Path | Description |
|--------|------|-------------|
| POST | /demo/seed | Create demo project |

## Task Types

`image_segmentation` | `gwas_analysis` | `opengwas_fetch` | `mendelian_randomization` | `mediation_mr` | `risk_modeling` | `report_generation`

## Error Codes

`SCRIPT_NOT_FOUND` | `SCRIPT_EXECUTION_FAILED` | `OUTPUT_JSON_INVALID` | `OUTPUT_FILE_MISSING` | `TASK_TIMEOUT` | `FILE_NOT_FOUND` | `DATABASE_ERROR`
