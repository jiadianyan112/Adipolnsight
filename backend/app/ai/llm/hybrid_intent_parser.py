"""
Hybrid Intent Parser — rule → LLM → fallback

作为 Agent Orchestrator 的唯一 parser 入口。

执行策略:
1. ruleBasedIntentParser 优先（快、免费、确定性高）
2. 规则结果不满足阈值 → llmIntentParser
3. LLM 失败 → fallback 到 rule 结果
4. 所有结果标记 source
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.app.ai.intent_parser import (
    intent_parser as rule_parser,
    IntentParseResult,
)

logger = logging.getLogger("adipoinsight.hybrid_parser")

# ===== 阈值配置 =====

RULE_CONFIDENCE_THRESHOLD = 0.85      # 规则 parser 直接采用的置信度阈值
LLM_CONFIDENCE_THRESHOLD = 0.70       # LLM 结果采纳的最低置信度
FINAL_CONFIDENCE_THRESHOLD = 0.70     # 最终结果的最低置信度（低于此返回 need_more_info）
MAJOR_MISSING_PARAMS_LIMIT = 2        # "严重参数缺失"的判定：缺失超过此数量


class HybridIntentParser:
    """
    Hybrid Intent Parser — rule + LLM + fallback。

    先尝试规则（快速、免费），规则不确定时调用 LLM，
    LLM 失败时 fallback 到规则结果。
    """

    def __init__(self):
        self._rule = rule_parser

    def parse(self, text: str) -> IntentParseResult:
        """
        解析用户输入。

        返回的 IntentParseResult.source 标记解析来源:
        - "rule": 规则 parser 高置信度命中
        - "llm": 规则不足，LLM 成功解析
        - "hybrid": 规则不足，LLM 也失败，使用规则结果兜底
        """
        if not text or not text.strip():
            return IntentParseResult(
                intent="unsupported",
                confidence=0.0,
                source="rule",
                user_message="请输入您想要执行的分析任务描述",
                raw_input=text,
            )

        # === Step 1: 规则 parser ===
        rule_result = self._rule.parse(text)

        # 如果规则结果满足阈值，直接返回
        if self._is_rule_result_strong(rule_result):
            rule_result.source = "rule"
            logger.info(
                "Hybrid: rule parser matched (intent=%s conf=%.2f)",
                rule_result.intent, rule_result.confidence,
            )
            return rule_result

        logger.info(
            "Hybrid: rule result weak (intent=%s conf=%.2f), trying LLM",
            rule_result.intent, rule_result.confidence,
        )

        # === Step 2: LLM parser ===
        try:
            from backend.app.ai.llm import llm_intent_parser
            llm_result = llm_intent_parser.parse(text)

            if self._is_llm_result_valid(llm_result):
                llm_result.source = "llm"
                logger.info(
                    "Hybrid: LLM parser matched (intent=%s conf=%.2f)",
                    llm_result.intent, llm_result.confidence,
                )
                # 合并规则提取的参数（规则可能提取了 LLM 遗漏的）
                llm_result = self._merge_params(llm_result, rule_result)
                return llm_result
            else:
                logger.warning(
                    "Hybrid: LLM result rejected (intent=%s conf=%.2f warnings=%s)",
                    llm_result.intent, llm_result.confidence, llm_result.warnings,
                )

        except Exception as exc:
            logger.warning("Hybrid: LLM parser failed: %s", exc)

        # === Step 3: Fallback 到规则结果 ===
        rule_result.source = "hybrid"
        logger.info(
            "Hybrid: fallback to rule (intent=%s conf=%.2f)",
            rule_result.intent, rule_result.confidence,
        )
        return rule_result

    # ===== 判定方法 =====

    def _is_rule_result_strong(self, result: IntentParseResult) -> bool:
        """规则结果是否足够强，无需 LLM"""
        if result.intent == "unsupported":
            return False
        if result.confidence < RULE_CONFIDENCE_THRESHOLD:
            return False
        if len(result.missing_params) > MAJOR_MISSING_PARAMS_LIMIT:
            return False
        return True

    def _is_llm_result_valid(self, result: IntentParseResult) -> bool:
        """LLM 结果是否有效可采纳"""
        if result.intent == "unsupported":
            return False
        if result.confidence < LLM_CONFIDENCE_THRESHOLD:
            return False
        if result.warnings and any("invalid intent" in w.lower() for w in result.warnings):
            return False
        # extractedParams 基础校验
        if not isinstance(result.extracted_params, dict):
            return False
        return True

    def _merge_params(
        self, llm_result: IntentParseResult, rule_result: IntentParseResult
    ) -> IntentParseResult:
        """合并规则 parser 提取的参数到 LLM 结果（规则提取的参数更可靠）"""
        merged = dict(rule_result.extracted_params)
        # LLM 提取的参数作为补充（不覆盖规则结果）
        for key, value in llm_result.extracted_params.items():
            if key not in merged and value:
                merged[key] = value

        # 重新计算缺失参数
        all_required = rule_result.missing_params + llm_result.missing_params
        missing = [p for p in all_required if p not in merged]

        llm_result.extracted_params = merged
        llm_result.missing_params = list(dict.fromkeys(missing))  # 去重保序
        llm_result.warnings.extend(rule_result.warnings)
        return llm_result

    # ===== 便捷方法 =====

    def parse_with_threshold(self, text: str) -> IntentParseResult:
        """
        解析用户输入，并对最终结果做置信度判断。

        如果最终 confidence < FINAL_CONFIDENCE_THRESHOLD，
        将 intent 设为 chat 且 next_action 设为 clarify。
        """
        result = self.parse(text)
        if result.confidence < FINAL_CONFIDENCE_THRESHOLD and result.intent != "unsupported":
            result.next_action = "clarify"
            result.user_message = (
                f"无法确定您的意图（置信度 {result.confidence:.0%}），"
                f"请提供更详细的分析需求描述。"
            )
        return result


# 全局单例
hybrid_intent_parser = HybridIntentParser()
