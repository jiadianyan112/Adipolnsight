"""
Agent Orchestrator 测试脚本
运行: python backend/app/ai/test_agent_orchestrator.py
"""

import backend.app.ai.skills  # noqa: F401 — 触发 Skill 注册
from backend.app.ai.agent_orchestrator import agent_orchestrator, OrchestratorResult

ctx = {"project_id": 1, "exposure": "Liver_PDFF", "outcome": "Osteoporosis"}

def show(r: OrchestratorResult, label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  query: {r.raw_query[:80]}")
    print(f"{'='*60}")
    print(f"  answer_type:    {r.answer_type}")
    print(f"  capability:     {r.capability_type}")
    print(f"  job_id:         {r.job_id}")
    print(f"  job_status:     {r.job_status}")
    print(f"  confidence:     {r.intent_confidence:.2f}")
    print(f"  message:        {r.message[:120]}")
    if r.missing_params:
        print(f"  missing:        {r.missing_params}")
    if r.extracted_params:
        # 只显示键，不显示值（避免 sensitive data）
        print(f"  params keys:    {list(r.extracted_params.keys())}")
    if r.next_actions:
        print(f"  next_actions:   {[(a.label, a.action) for a in r.next_actions[:4]]}")
    if r.clarification_question:
        print(f"  clarification:  {r.clarification_question[:100]}")


# ===== 场景 1: 参数齐全 → job_created =====
show(agent_orchestrator.process(
    "帮我做 GWAS，表型是 Liver_PDFF，用 REGENIE 方法，人群选 EUR",
    ctx,
), "Scenario 1: GWAS with full params")

# ===== 场景 2: 缺少 phenotype → need_more_info =====
show(agent_orchestrator.process(
    "做一个 GWAS 分析吧",
    ctx,
), "Scenario 2: GWAS missing phenotype")

# ===== 场景 3: MR with context exposure/outcome → job_created =====
show(agent_orchestrator.process(
    "跑孟德尔随机化分析",
    ctx,
), "Scenario 3: MR with context pre-fill")

# ===== 场景 4: Segmentation without file → need_more_info =====
show(agent_orchestrator.process(
    "帮我做 MRI 影像分割",
    ctx,
), "Scenario 4: Segmentation without file_id")

# ===== 场景 5: Report generation → job_created =====
show(agent_orchestrator.process(
    "生成科研报告",
    ctx,
), "Scenario 5: Report generation")

# ===== 场景 6: 不可识别 → unsupported =====
show(agent_orchestrator.process(
    "今天天气怎么样",
    ctx,
), "Scenario 6: Unsupported query")

# ===== 场景 7: 询问状态 → job_created (query) =====
show(agent_orchestrator.process(
    "查看分析进度",
    ctx,
), "Scenario 7: Query status")

# ===== 场景 8: Risk modeling with context → job_created =====
show(agent_orchestrator.process(
    "做骨质疏松风险建模分析",
    ctx,
), "Scenario 8: Risk modeling")

# ===== 场景 9: Mediation MR → need_more_info (missing mediator_source) =====
show(agent_orchestrator.process(
    "做中介分析",
    ctx,
), "Scenario 9: Mediation MR needs mediator_source")

# ===== 场景 10: Mediation MR with mediator → job_created =====
show(agent_orchestrator.process(
    "做中介 MR，用 deCODE 血浆蛋白数据",
    {**ctx, "mediator_source": "decode_plasma"},
), "Scenario 10: Mediation MR with mediator_source")

# ===== 场景 11: Params 完整但 auto_run=False → need_more_info (确认) =====
show(agent_orchestrator.process(
    "生成报告",
    ctx,
    auto_run=False,
), "Scenario 11: Report with auto_run=False")

# ===== 场景 12: 空 query → unsupported =====
show(agent_orchestrator.process(
    "",
    ctx,
), "Scenario 12: Empty query")

print(f"\n{'='*60}")
print("  All scenarios executed. Check logs for job creation details.")
print(f"{'='*60}")
