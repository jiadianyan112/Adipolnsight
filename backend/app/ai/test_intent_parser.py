"""
Intent Parser 测试脚本
运行: python backend/app/ai/test_intent_parser.py
"""

from backend.app.ai.intent_parser import intent_parser

tests = [
    # (input, expected_intent, min_confidence)
    ("帮我做一个 GWAS 分析，表型是 Liver PDFF", "gwas", 0.3),
    ("上传 MRI 影像并分割肝脏和内脏脂肪", "segmentation", 0.3),
    ("做孟德尔随机化，暴露是 Liver_PDFF，结局是 Osteoporosis", "mr", 0.3),
    ("我想看中介 MR 的结果", "mediation_mr", 0.3),
    ("帮我量化脂肪表型", "phenotype", 0.3),
    ("生成分析报告", "report", 0.4),
    ("build a risk model for osteoporosis", "risk_modeling", 0.3),
    ("查询任务进度", "job_status", 0.3),
    ("run GWAS with phenotype Liver_PDFF using REGENIE", "gwas", 0.3),
    ("做全基因组关联分析", "gwas", 0.3),
    ("帮我看看任务状态", "job_status", 0.2),
    ("骨质疏松风险建模", "risk_modeling", 0.3),
    ("蛋白质组中介分析", "mediation_mr", 0.3),
    ("做个MR分析看看", "mr", 0.2),
    ("开始影像分割", "segmentation", 0.2),
    # Low confidence / unsupported
    ("你好", "unsupported", 0.0),
    ("分析数据", "unsupported", 0.0),
    ("", "unsupported", 0.0),
    (None, "unsupported", 0.0),
]

passed = 0
failed = 0
for text, expected, min_conf in tests:
    result = intent_parser.parse(text or "")
    ok = result.intent == expected and result.confidence >= min_conf
    if ok:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"

    kw = ",".join(getattr(result, 'matched_keywords', [])[:3]) if hasattr(result, 'matched_keywords') else "-"
    print(
        f"[{status}] intent={result.intent:<20} conf={result.confidence:.2f} "
        f"source={result.source} next={result.next_action} "
        f"msg={result.user_message[:40]}"
    )
    if not ok:
        print(f"       expected={expected} min_conf>={min_conf}")

print(f"\n{passed}/{passed + failed} tests passed")

# Show extracted params for a high-quality match
print("\n--- Params extraction demo ---")
demo = intent_parser.parse(
    "帮我做 GWAS，表型是 Liver_PDFF，用 REGENIE 方法，人群是 EUR"
)
print(f"intent: {demo.intent}")
print(f"confidence: {demo.confidence:.2f}")
print(f"extracted_params: {demo.extracted_params}")
print(f"missing_params: {demo.missing_params}")

# Show clarification example
print("\n--- Clarification demo ---")
clarify = intent_parser.parse("帮我分析一下")
print(f"intent: {clarify.intent}")
print(f"clarification_needed: {clarify.clarification_needed}")
print(f"question: {clarify.clarification_question}")
