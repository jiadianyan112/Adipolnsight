#!/usr/bin/env bash
# AdipoInsight Backend API Smoke Test
# 端到端回归测试脚本 — 覆盖核心流程
#
# 用法:
#   chmod +x scripts/smoke-test.sh
#   bash scripts/smoke-test.sh
#
# 前置条件:
#   1. uvicorn backend.app.main:app --port 8000 (后端运行中)
#   2. curl 可用

set -e
BASE="http://localhost:8000/api/v1"
AI_BASE="http://localhost:8000/api/ai"
PASS=0
FAIL=0

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red()   { printf "\033[31m%s\033[0m\n" "$1"; }
check() {
  local label="$1" expected="$2" actual="$3"
  if echo "$actual" | grep -q "$expected" 2>/dev/null; then
    green "  ✓ $label"
    PASS=$((PASS + 1))
  else
    red "  ✗ $label (expected to contain '$expected', got: '$actual')"
    FAIL=$((FAIL + 1))
  fi
}
check_exact() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    green "  ✓ $label"
    PASS=$((PASS + 1))
  else
    red "  ✗ $label (expected: '$expected', got: '$actual')"
    FAIL=$((FAIL + 1))
  fi
}

echo "=========================================="
echo " AdipoInsight Backend Smoke Test"
echo "=========================================="
echo ""

# ---- 1. Health Check ----
echo "[1] Health Check"
STATUS=$(curl -s "$BASE/health")
check "GET /health returns ok" '"status":"ok"' "$STATUS"

# ---- 2. Create Project ----
echo "[2] Create Project"
PROJ=$(curl -s -X POST "$BASE/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test Project","research_goal":"Regression test","exposure":"LDL_Cholesterol","outcome":"Coronary_Artery_Disease","mediator_set":"Plasma_Proteins"}')
PROJ_ID=$(echo "$PROJ" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
check "Project created" "ok" "$([ -n "$PROJ_ID" ] && echo "ok" || echo "no")"
echo "  Project ID: $PROJ_ID"

# ---- 3. Get Project ----
echo "[3] Get Project Details"
PROJ_DETAIL=$(curl -s "$BASE/projects/$PROJ_ID")
EXPOSURE=$(echo "$PROJ_DETAIL" | grep -o '"exposure":"[^"]*"' | cut -d'"' -f4)
check_exact "Project exposure is LDL_Cholesterol" "LDL_Cholesterol" "$EXPOSURE"

# ---- 4. Task List (empty initially) ----
echo "[4] Task List (empty)"
TASKS=$(curl -s "$BASE/projects/$PROJ_ID/tasks")
TASK_COUNT=$(echo "$TASKS" | grep -o '"tasks":\[.*\]' | grep -o '{' | wc -l)
echo "  Initial task count: $TASK_COUNT"

# ---- 5. Task List Paginated ----
echo "[5] Task List Paginated"
PAGED=$(curl -s "$BASE/projects/$PROJ_ID/tasks?page=1&page_size=3")
check "Paginated response has items" "items" "$PAGED"

# ---- 6. Task List latest_only ----
echo "[6] Lightweight Polling"
LATEST=$(curl -s "$BASE/projects/$PROJ_ID/tasks?latest_only=true&page_size=7")
check "latest_only response has total field" "total" "$LATEST"

# ---- 7. AI Report Generation ----
echo "[7] AI Report Generation"
REPORT_JOB=$(curl -s -X POST "$AI_BASE/report/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": $PROJ_ID, \"parameters\": {\"report_type\": \"full\", \"language\": \"zh-CN\"}}")
JOB_ID=$(echo "$REPORT_JOB" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
check "Report job created" "ok" "$([ -n "$JOB_ID" ] && echo "ok" || echo "no")"
echo "  Job ID: $JOB_ID"

# Poll until completion or timeout (max 60s)
for i in $(seq 1 30); do
  JOB_STATUS=$(curl -s "$AI_BASE/jobs/$JOB_ID" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  if [ "$JOB_STATUS" = "succeeded" ] || [ "$JOB_STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
check "Report job reached terminal state" "succeeded" "$JOB_STATUS"

# ---- 8. Report Result Structure ----
echo "[8] Report Result Structure"
RESULT=$(curl -s "$AI_BASE/jobs/$JOB_ID/result")
check "Report response contains sections" "sections" "$RESULT"
check "Report response contains title" "title" "$RESULT"

# ---- 9. Unified Jobs Endpoint ----
echo "[9] Unified Jobs"
UNIFIED=$(curl -s "$BASE/projects/$PROJ_ID/jobs/unified")
check "Unified response has source stats" "source_stats" "$UNIFIED"

# ---- 10. GWAS AI Job (with project exposure) ----
echo "[10] GWAS with Project Exposure"
GWAS_JOB=$(curl -s -X POST "$AI_BASE/gwas/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": $PROJ_ID, \"parameters\": {\"phenotype_name\": \"$EXPOSURE\", \"method\": \"REGENIE\"}}")
GWAS_JID=$(echo "$GWAS_JOB" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "  GWAS Job: $GWAS_JID"

sleep 4
GWAS_RESULT=$(curl -s "$AI_BASE/jobs/$GWAS_JID/result")
GWAS_PHENO=$(echo "$GWAS_RESULT" | grep -o '"phenotype":"[^"]*"' | cut -d'"' -f4)
check_exact "GWAS phenotype matches project exposure" "$EXPOSURE" "$GWAS_PHENO"

# ---- Summary ----
echo ""
echo "=========================================="
echo " Results: $PASS passed, $FAIL failed"
echo "=========================================="

[ "$FAIL" -eq 0 ] && green "All smoke tests passed!" || red "Some tests failed!"
exit $FAIL
