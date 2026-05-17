"""
LLM Provider 本地调用示例

运行: python backend/app/ai/llm/tests/demo_provider.py
"""

import sys
sys.path.insert(0, ".")

from backend.app.schemas.llm import (
    LLMRequest,
    LLMMessage,
    LLMIntentResult,
    LLMResultInterpretation,
    LLMErrorExplanation,
    LLMReportEnhancement,
)
from backend.app.ai.llm.provider import provider_registry
from backend.app.ai.llm.service import llm_service

print("=" * 60)
print("  AdipoInsight LLM Provider Demo")
print("=" * 60)

# 1. 列出已注册 provider
print("\n[1] Registered providers:")
for name in provider_registry.list_all():
    p = provider_registry.get(name)
    print(f"  - {name} (class: {p.__class__.__name__})")

# 2. 意图解析 (JSON)
print("\n[2] Intent Parse (JSON):")
req = LLMRequest(
    messages=[
        LLMMessage(role="system", content="你是意图解析器，将用户输入映射到 AI capability"),
        LLMMessage(role="user", content="帮我做一个 GWAS 分析，表型是 Liver PDFF"),
    ],
    taskType="intent_parse",
    temperature=0.1,
)
resp = llm_service.call_llm_json(req, LLMIntentResult)
if resp.json_data:
    d = resp.json_data if isinstance(resp.json_data, dict) else {}
    print(f"  intent: {d.get('intent', 'N/A')}")
    print(f"  confidence: {d.get('confidence', 'N/A')}")
    print(f"  capability: {d.get('capability_type', 'N/A')}")
    print(f"  params: {d.get('extracted_params', {})}")
    print(f"  provider: {resp.provider}/{resp.model}")
else:
    print(f"  text fallback: {resp.content[:80]}...")

# 3. 结果解读 (JSON)
print("\n[3] Result Interpretation (JSON):")
req = LLMRequest(
    messages=[
        LLMMessage(role="system", content="你是医学科研结果解读专家"),
        LLMMessage(role="user", content="解读以下 GWAS 结果: 18 loci, λ_GC=1.003"),
    ],
    taskType="result_interpretation",
    temperature=0.3,
)
resp = llm_service.call_llm_json(req, LLMResultInterpretation)
if resp.json_data:
    interp = resp.json_data
    print(f"  capability: {interp.get('capability_type', 'N/A')}")
    print(f"  summary: {interp.get('summary', '')[:80]}...")
    print(f"  key_findings: {len(interp.get('key_findings', []))} items")
    print(f"  next_steps: {len(interp.get('suggested_next_steps', []))} items")

# 4. 错误解释 (JSON)
print("\n[4] Error Explanation (JSON):")
req = LLMRequest(
    messages=[
        LLMMessage(role="system", content="你是系统错误解释助手"),
        LLMMessage(role="user", content="TASK_TIMEOUT"),
    ],
    taskType="error_explanation",
)
resp = llm_service.call_llm_json(req, LLMErrorExplanation)
if resp.json_data:
    expl = resp.json_data
    print(f"  error_code: {expl.get('error_code', 'N/A')}")
    print(f"  friendly: {expl.get('friendly_message', '')[:80]}")
    print(f"  causes: {expl.get('possible_causes', [])}")
    print(f"  actions: {expl.get('suggested_actions', [])}")

# 5. 报告增强 (JSON)
print("\n[5] Report Enhancement (JSON):")
req = LLMRequest(
    messages=[
        LLMMessage(role="system", content="你是科研报告撰写专家"),
        LLMMessage(role="user", content="基于 GWAS 和 MR 结果生成讨论章节"),
    ],
    taskType="report_generation",
    temperature=0.3,
)
resp = llm_service.call_llm_json(req, LLMReportEnhancement)
if resp.json_data:
    report = resp.json_data
    print(f"  discussion_len: {len(report.get('discussion_section', ''))}")
    print(f"  conclusion_len: {len(report.get('conclusion_section', ''))}")
    print(f"  clinical: {report.get('clinical_implications', '')[:60]}...")

# 6. 文本对话
print("\n[6] Chat (text):")
req = LLMRequest(
    messages=[
        LLMMessage(role="system", content="你是 AdipoInsight AI 助手"),
        LLMMessage(role="user", content="你好，介绍一下你能做什么"),
    ],
    taskType="chat",
)
resp = llm_service.call_llm(req)
print(f"  response: {resp.content[:120]}...")
print(f"  provider: {resp.provider}")

# 7. 错误处理 — 不存在的 provider
print("\n[7] Fallback on missing provider:")
req = LLMRequest(
    messages=[LLMMessage(role="user", content="test")],
    taskType="chat",
    provider="nonexistent_provider",
)
resp = llm_service.call_llm(req)
print(f"  response: {resp.content[:100]}...")
print(f"  (gracefully fell back to mock provider)")

# 8. 获取默认 provider
print("\n[8] Default provider:")
default = provider_registry.get_default()
print(f"  name: {default.name}")
print(f"  class: {default.__class__.__name__}")
print(f"  has('mock'): {provider_registry.has('mock')}")
print(f"  has('deepseek'): {provider_registry.has('deepseek')}")

print(f"\n{'=' * 60}")
print("  Demo complete. All 8 scenarios executed.")
print(f"{'=' * 60}")
