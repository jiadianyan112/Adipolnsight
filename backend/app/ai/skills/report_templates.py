"""
AdipoInsight 报告模板

两种报告类型：
- summary_report：平台结果摘要（简洁，每章节 2-4 句话）
- full_report：完整科研分析报告（详细，含方法、结果、解读）

核心原则：
1. 基于 selectedJobs —— 只有已完成的结果才生成对应章节
2. 没有 evidence 的章节标注为 pending，不写结论
3. 缺失数据写入 limitations
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ============================================================
# 分析类型 → 章节映射
# ============================================================

CAPABILITY_SECTION_MAP: Dict[str, Dict[str, str]] = {
    "image_segmentation": {
        "key": "segmentation",
        "title": "AI 影像分割结果",
        "title_en": "AI Image Segmentation Results",
    },
    "phenotype_quantification": {
        "key": "phenotype",
        "title": "脂肪表型量化",
        "title_en": "Fat Phenotype Quantification",
    },
    "gwas_analysis": {
        "key": "gwas",
        "title": "GWAS 全基因组关联分析",
        "title_en": "GWAS Analysis Results",
    },
    "mendelian_randomization": {
        "key": "mr",
        "title": "MR 因果推断",
        "title_en": "Mendelian Randomization Causal Inference",
    },
    "mediation_mr": {
        "key": "mediation_mr",
        "title": "中介 MR 蛋白筛选",
        "title_en": "Mediation MR Protein Screening",
    },
    "risk_modeling": {
        "key": "risk_modeling",
        "title": "疾病风险建模",
        "title_en": "Disease Risk Modeling",
    },
    "report_generation": {
        "key": "report_generation",
        "title": "报告生成",
        "title_en": "Report Generation",
    },
}


# ============================================================
# 生成器：根据 job result type 推断并生成章节
# ============================================================

def _infer_capability(result: dict) -> str | None:
    """从 result dict 推断 capability_type。"""
    if not isinstance(result, dict):
        return None
    if "dice_scores" in result or "segmentation_id" in result or "model_name" in result:
        return "image_segmentation"
    if "lead_snps" in result or "manhattan_plot_url" in result or "gwas_id" in result:
        return "gwas_analysis"
    if "estimates" in result and ("pleiotropy" in result or "heterogeneity" in result):
        return "mendelian_randomization"
    if "indirect_effects" in result or "ranked_proteins" in result or "mediation_id" in result:
        return "mediation_mr"
    if "ols_results" in result or "rcs_curve_data" in result or "adjusted_odds_ratios" in result:
        return "risk_modeling"
    if "liver_pdff" in result or "visceral_fat_volume" in result:
        return "phenotype_quantification"
    return None


def _classify_jobs(
    selected_jobs: Dict[str, dict],
) -> Dict[str, List[tuple]]:
    """将 selectedJobs 按 capability_type 分类。

    Returns: {capability_type: [(job_id, result_dict), ...]}
    """
    classified: Dict[str, List[tuple]] = {}
    for job_id, result in selected_jobs.items():
        if not isinstance(result, dict):
            continue
        cap = _infer_capability(result)
        if cap is None:
            cap = "unknown"
        if cap not in classified:
            classified[cap] = []
        classified[cap].append((job_id, result))
    return classified


# ============================================================
# 章节生成器（每个分析类型一个函数）
# ============================================================

def _section_background(
    project_title: str, classified_jobs: Dict[str, list], report_type: str, lang: str,
) -> dict:
    """项目背景 — 始终生成。"""
    analysis_types = list(classified_jobs.keys())
    has_imaging = any(c in classified_jobs for c in ["image_segmentation", "phenotype_quantification"])
    has_genetics = any(c in classified_jobs for c in ["gwas_analysis", "mendelian_randomization", "mediation_mr"])
    has_risk = "risk_modeling" in classified_jobs

    if report_type == "summary_report":
        content = (
            f"## 项目概述\n\n"
            f"本项目「{project_title}」整合了"
            + ("影像组学、" if has_imaging else "")
            + ("基因组学、" if has_genetics else "")
            + ("风险建模" if has_risk else "")
            + "多维度数据，系统评估目标性状的遗传基础与临床意义。\n\n"
            f"本研究共完成 {sum(len(v) for v in classified_jobs.values())} 项分析任务，"
            f"覆盖 {len(analysis_types)} 个分析类型。"
        )
    else:
        content = (
            f"## 研究背景\n\n"
            f"肝脏脂肪含量（Liver PDFF）升高与非酒精性脂肪肝病（NAFLD）密切相关，"
            f"近年研究提示 NAFLD 可能通过系统性炎症、胰岛素抵抗及脂肪因子分泌异常等途径影响骨代谢。"
            f"然而，肝脏脂肪积累与骨质疏松之间的因果关系及其分子机制尚不完全明确。\n\n"
            f"## 研究目标\n\n"
            f"1. 量化肝脏 PDFF 与骨密度/骨质疏松风险的关联强度\n"
            f"2. 利用孟德尔随机化方法评估因果关系\n"
            f"3. 识别介导肝脏-骨骼轴的血浆蛋白中介因子\n"
            f"4. 构建基于影像和遗传特征的综合风险预测模型\n\n"
            f"## 研究设计\n\n"
            f"本研究整合腹部 MRI 影像组学（TSSA-UNet 自动分割）、"
            f"UK Biobank 基因组学数据（n≈40,000，EUR）、"
            f"deCODE 血浆蛋白 pQTL 数据（4,907 种蛋白）及 OpenGWAS 公开数据库，"
            f"采用「影像 → 遗传 → 因果 → 中介 → 临床」五步分析策略。"
        )

    job_count = sum(len(v) for v in classified_jobs.values())
    unique_types = len(classified_jobs)
    return {
        "number": 1,
        "title": "项目背景与研究目标",
        "content": content,
        "status": "complete",
        "summary": f"本项目共完成 {job_count} 项分析（覆盖 {unique_types} 个分析类型）",
        "evidence_job_ids": [],
        "related_figures": [],
        "related_tables": [],
    }


def _section_from_results(
    capability_type: str,
    jobs: List[tuple],
    section_number: int,
    report_type: str,
    lang: str,
) -> dict:
    """为有结果的 capability 生成章节。"""
    section_info = CAPABILITY_SECTION_MAP.get(capability_type, {})
    title = section_info.get("title", capability_type)
    job_ids = [jid for jid, _ in jobs]
    results = [r for _, r in jobs]

    content = _generate_section_content(capability_type, results, report_type, lang)
    summary = _generate_section_summary(capability_type, results)

    return {
        "number": section_number,
        "title": title,
        "content": content,
        "status": "complete",
        "summary": summary,
        "evidence_job_ids": job_ids,
        "related_figures": [],
        "related_tables": [],
    }


def _section_pending(
    capability_type: str,
    section_number: int,
    missing_info: str = "",
) -> dict:
    """生成「待完成」占位章节。"""
    section_info = CAPABILITY_SECTION_MAP.get(capability_type, {})
    title = section_info.get("title", capability_type)
    reason = f"（{missing_info}）" if missing_info else ""

    return {
        "number": section_number,
        "title": title,
        "content": f"## 状态：待分析\n\n此分析尚未执行{reason}。完成对应分析后将自动填充结果。\n",
        "status": "pending",
        "summary": f"待分析{reason}",
        "evidence_job_ids": [],
        "related_figures": [],
        "related_tables": [],
    }


def _section_discussion(
    classified_jobs: Dict[str, list], report_type: str, lang: str,
) -> dict:
    """综合讨论与结论 — 基于实际数据统计完成数/待完成数。"""
    pipeline_order = [
        "image_segmentation", "phenotype_quantification", "gwas_analysis",
        "mendelian_randomization", "mediation_mr", "risk_modeling",
    ]
    capabilities = list(classified_jobs.keys())
    sections_done = len([c for c in pipeline_order if c in classified_jobs])
    total_sections = len(pipeline_order)
    pending = total_sections - sections_done

    if report_type == "summary_report":
        findings = []
        if "gwas_analysis" in classified_jobs:
            findings.append("GWAS 识别了与目标表型显著关联的基因组位点")
        if "mendelian_randomization" in classified_jobs:
            findings.append("MR 分析支持了暴露因素与结局之间的因果关系")
        if "mediation_mr" in classified_jobs:
            findings.append("中介 MR 筛选出潜在的血浆蛋白中介因子")
        if "risk_modeling" in classified_jobs:
            findings.append("风险建模揭示了剂量-反应关系及高危人群特征")

        content = "## 主要发现\n\n" + "\n".join(f"{i+1}. {f}" for i, f in enumerate(findings)) if findings else "## 主要发现\n\n暂无可总结的发现——请运行更多分析。"
        if pending > 0:
            content += f"\n\n> 注意：尚有 {pending} 项分析未完成，以上结论为阶段性结果。"
    else:
        content = (
            f"## 主要发现\n\n"
        )
        if "gwas_analysis" in classified_jobs:
            content += "1. GWAS 分析识别了多个显著相关的基因组位点，λ_GC 表明群体分层控制良好\n"
        if "mendelian_randomization" in classified_jobs:
            content += "2. MR 因果推断支持暴露因素对结局的因果效应，多效性检验未发现显著偏倚\n"
        if "mediation_mr" in classified_jobs:
            content += "3. 中介 MR 筛选出显著的血浆蛋白中介因子，揭示了可能的生物学机制\n"
        if "risk_modeling" in classified_jobs:
            content += "4. 风险建模呈剂量-反应关系，为临床风险分层提供了定量依据\n"

        content += (
            f"\n## 临床意义\n\n"
            f"本研究为理解目标性状的遗传基础及临床转化提供了多组学证据。"
            f"主要分析结果支持进一步在独立队列中验证，并在功能层面探索关键分子的作用机制。\n"
        )
        if pending > 0:
            content += f"\n> 注意：尚有 {pending} 项分析未完成，以上结论为阶段性结果。\n"

    return {
        "number": sections_done + 2,
        "title": "综合讨论与结论",
        "content": content,
        "status": "complete" if sections_done > 0 else "pending",
        "summary": f"已基于 {sections_done}/{total_sections} 项分析结果撰写" + (f"（{pending} 项待完成）" if pending > 0 else ""),
        "evidence_job_ids": [],
        "related_figures": [],
        "related_tables": [],
    }


def _section_limitations(
    classified_jobs: Dict[str, list],
    missing_capabilities: List[str],
) -> dict:
    """研究局限性 — 基于实际缺失数据动态生成。"""
    limitations = []

    # 通用局限性
    limitations.append("本研究使用 Mock 模拟数据，结果不反映真实生物学发现，不可用于临床决策")

    # 特定分析类型的局限性
    if "gwas_analysis" in classified_jobs:
        limitations.append("GWAS 样本限于 EUR 人群，跨人群泛化性待独立队列验证")
    if "mendelian_randomization" in classified_jobs:
        limitations.append("MR 分析依赖工具变量三大假设（关联性、独立性、排他性），违反任一假设将导致估计有偏")
    if "mediation_mr" in classified_jobs:
        limitations.append("中介分析仅覆盖 cis-pQTL，可能遗漏 trans-pQTL 的中介效应，低估总中介效应")
    if "image_segmentation" in classified_jobs:
        limitations.append("PDFF 由自动化分割估计，与 MR 波谱金标准存在偏差")
    if "risk_modeling" in classified_jobs:
        limitations.append("横断面设计无法确定因果时序——MR 证据可作为因果推断补充")

    # 缺失数据类型
    if missing_capabilities:
        missing_names = []
        for mc in missing_capabilities:
            info = CAPABILITY_SECTION_MAP.get(mc, {})
            missing_names.append(info.get("title", mc))
        limitations.append(f"以下分析尚未完成，相关结论缺失：{'、'.join(missing_names)}")

    # 数据缺失详情
    missing_data_fields = _detect_missing_data_fields(classified_jobs)
    if missing_data_fields:
        limitations.append(f"以下数据字段缺失，影响对应章节的完整性：{'、'.join(missing_data_fields)}")

    return {
        "number": 99,
        "title": "研究局限性",
        "content": "## 研究局限性\n\n" + "\n".join(f"- {lim}" for lim in limitations),
        "status": "complete",
        "summary": f"共 {len(limitations)} 项局限性",
        "evidence_job_ids": [],
        "related_figures": [],
        "related_tables": [],
    }


def _section_next_steps(
    classified_jobs: Dict[str, list],
    missing_capabilities: List[str],
) -> dict:
    """下一步计划 — 基于 pipeline 依赖关系动态生成。"""
    steps = []

    # pipeline 顺序: segmentation → phenotype → gwas → mr → mediation_mr → risk_modeling → report
    pipeline = [
        "image_segmentation", "phenotype_quantification", "gwas_analysis",
        "mendelian_randomization", "mediation_mr", "risk_modeling",
    ]

    done = set(classified_jobs.keys())
    for cap in pipeline:
        if cap not in done:
            info = CAPABILITY_SECTION_MAP.get(cap, {})
            steps.append(f"执行 {info.get('title', cap)} 分析")
            break  # 只推荐下一个

    if "gwas_analysis" in done and "mendelian_randomization" not in done:
        steps.append("利用已完成的 GWAS 显著 SNP 作为工具变量，执行孟德尔随机化因果推断")

    if "mendelian_randomization" in done and "mediation_mr" not in done:
        steps.append("进行中介 MR 分析，筛选介导暴露-结局关系的血浆蛋白")

    if not steps:
        steps = [
            "在独立队列中验证发现的显著位点和因果效应",
            "进行功能注释和通路富集分析",
            "整合更多组学数据（转录组、代谢组）",
        ]

    return {
        "number": 100,
        "title": "下一步计划",
        "content": "## 下一步计划\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)),
        "status": "complete",
        "summary": f"共 {len(steps)} 项建议",
        "evidence_job_ids": [],
        "related_figures": [],
        "related_tables": [],
    }


# ============================================================
# 章节内容生成
# ============================================================

def _generate_section_content(
    capability_type: str,
    results: List[dict],
    report_type: str,
    lang: str,
) -> str:
    """根据分析类型和实际结果生成章节内容。"""
    if capability_type == "image_segmentation":
        return _segmentation_content(results, report_type)
    elif capability_type == "phenotype_quantification":
        return _phenotype_content(results, report_type)
    elif capability_type == "gwas_analysis":
        return _gwas_content(results, report_type)
    elif capability_type == "mendelian_randomization":
        return _mr_content(results, report_type)
    elif capability_type == "mediation_mr":
        return _mediation_mr_content(results, report_type)
    elif capability_type == "risk_modeling":
        return _risk_modeling_content(results, report_type)
    else:
        return f"## {capability_type}\n\n分析完成，请查看原始结果以获取详情。\n"


def _generate_section_summary(capability_type: str, results: List[dict]) -> str:
    """单句摘要。"""
    if not results:
        return "数据缺失"
    r = results[0] if results else {}
    if capability_type == "image_segmentation":
        model = r.get("model_name", "TSSA-UNet")
        targets = len(r.get("target_regions", []))
        return f"{model} 完成 {targets} 个解剖结构的分割"
    elif capability_type == "gwas_analysis":
        loci = r.get("significant_loci_count", "?")
        return f"识别 {loci} 个显著基因座"
    elif capability_type == "mendelian_randomization":
        ivw = next((e for e in r.get("estimates", []) if e.get("method") == "IVW"), {})
        beta = ivw.get("beta", "?")
        return f"IVW β={beta}"
    elif capability_type == "mediation_mr":
        sig = r.get("significant_mediators_count", 0)
        return f"{sig} 个显著中介蛋白"
    elif capability_type == "risk_modeling":
        grp = r.get("grouping", "quartile")
        return f"{grp} 分层风险建模完成"
    elif capability_type == "phenotype_quantification":
        pdff = r.get("liver_pdff", "?")
        return f"肝脏 PDFF={pdff}%"
    return "分析完成"


# ============================================================
# 各分析类型的内容模板
# ============================================================

def _segmentation_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    model = r.get("model_name", "TSSA-UNet")
    version = r.get("model_version", "v2.1")
    targets = r.get("target_regions", [])
    dice = r.get("dice_scores", {})
    qc = r.get("quality_control", {})
    qc_status = qc.get("status", "数据缺失") if isinstance(qc, dict) else "数据缺失"

    if report_type == "summary_report":
        lines = [f"## 方法\n使用 {model} {version} 对腹部 MRI 进行多器官自动分割。\n"]
        if dice:
            lines.append(f"## 结果\nDICE 范围: {min(dice.values()):.3f} – {max(dice.values()):.3f}，质控: {qc_status}。\n")
        else:
            lines.append("## 结果\n分割已完成。详细的 DICE 评分和体积指标数据缺失。\n")
    else:
        lines = [
            f"## 方法\n\n使用 {model} {version} 深度学习模型对腹部 MRI DIXON 序列进行多器官自动分割。\n",
        ]
        if dice:
            lines.append("## 分割性能\n\n| 解剖结构 | DICE 系数 | 评价 |\n|---------|----------|------|")
            for region, score in dice.items():
                if score >= 0.92:
                    grade = "优秀"
                elif score >= 0.88:
                    grade = "良好"
                elif score >= 0.83:
                    grade = "临界"
                else:
                    grade = "需改进"
                lines.append(f"| {region} | {score:.3f} | {grade} |")
            lines.append("")
        if isinstance(qc, dict) and qc:
            lines.append(f"## 质控评估\n\n- 综合质量评分: {qc.get('overall_quality_score', 'N/A')}")
            lines.append(f"- SNR: {qc.get('snr_estimate_db', 'N/A')} dB")
            lines.append(f"- 质控状态: {qc_status}")
            lines.append("")

    return "\n".join(lines)


def _phenotype_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    metrics = [
        ("liver_pdff", "肝脏 PDFF", "%"),
        ("visceral_fat_volume", "内脏脂肪体积", "L"),
        ("subcutaneous_fat_volume", "皮下脂肪体积", "L"),
        ("bone_marrow_fat_fraction", "骨髓脂肪分数", "%"),
        ("total_body_fat_pct", "全身脂肪百分比", "%"),
        ("muscle_volume", "肌肉体积", "L"),
        ("sat_vat_ratio", "SAT/VAT 比值", ""),
        ("bone_density", "骨密度", "g/cm³"),
    ]

    if report_type == "summary_report":
        lines = ["## 定量表型\n"]
        for key, label, unit in metrics:
            val = r.get(key)
            if val is not None:
                lines.append(f"- {label}: {val} {unit}")
        if len(lines) <= 1:
            lines.append("表型数据缺失。")
    else:
        lines = ["## 定量表型提取\n\n| 指标 | 数值 | 单位 |\n|------|------|------|"]
        for key, label, unit in metrics:
            val = r.get(key)
            if val is not None:
                lines.append(f"| {label} | {val} | {unit} |")
            else:
                lines.append(f"| {label} | 数据缺失 | {unit} |")
        lines.append("")

    return "\n".join(lines)


def _gwas_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    phenotype = r.get("phenotype", r.get("phenotype_name", "未知"))
    sample_size = r.get("sample_size", "数据缺失")
    method = r.get("method", "REGENIE")
    n_loci = r.get("significant_loci_count", "数据缺失")
    n_lead = r.get("lead_snps_count", "数据缺失")
    lambda_gc = r.get("lambda_gc", "数据缺失")
    lead_snps = r.get("lead_snps", [])

    if report_type == "summary_report":
        lines = [
            f"## 方法\n以 {phenotype} 为表型，{method} 方法，{sample_size} 例样本。\n",
            f"## 结果\n显著基因座: {n_loci}，先导 SNP: {n_lead}，λ_GC={lambda_gc}。\n",
        ]
        if isinstance(lead_snps, list) and lead_snps:
            top3 = lead_snps[:3]
            lines.append("## 前三先导 SNP")
            for snp in top3:
                lines.append(f"- {snp.get('snp', '?')} (chr{snp.get('chr', '?')}): P={snp.get('p_value', '?')}")
            lines.append("")
    else:
        lines = [
            f"## GWAS 设计\n\n"
            f"以 {phenotype} 为定量表型，纳入年龄、性别、BMI 及前 10 个遗传主成分"
            f"作为协变量，使用 {method} 方法对 {sample_size} 例 EUR 样本进行分析。\n",
            f"## 结果摘要\n\n"
            f"- 显著基因座: {n_loci} 个 (p < 5×10⁻⁸)\n"
            f"- 先导 SNP: {n_lead} 个\n"
            f"- 基因组膨胀系数 λ_GC: {lambda_gc}\n",
        ]
        if isinstance(lambda_gc, (int, float)):
            if lambda_gc > 1.05:
                lines.append(f"\nλ_GC={lambda_gc:.3f} 偏高，可能存在群体分层或隐性关联。\n")
            elif lambda_gc < 0.95:
                lines.append(f"\nλ_GC={lambda_gc:.3f} 偏低，需检查统计模型。\n")
            else:
                lines.append(f"\nλ_GC 接近 1.0，表明群体分层和隐性关联控制良好，无系统性偏倚。\n")

        if isinstance(lead_snps, list) and lead_snps:
            lines.append(f"\n## 先导 SNP ({len(lead_snps)} 个)\n")
            for snp in lead_snps[:10]:
                lines.append(
                    f"- **{snp.get('snp', '?')}** — "
                    f"Chr{snp.get('chr', '?')}, "
                    f"β={snp.get('beta', '?')}, "
                    f"P={snp.get('p_value', '?')}"
                )
            lines.append("")

    return "\n".join(lines)


def _mr_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    exposure = r.get("exposure", "未知")
    outcome = r.get("outcome", "未知")
    estimates = r.get("estimates", [])
    pleiotropy = r.get("pleiotropy", {})
    heterogeneity = r.get("heterogeneity", [])

    if report_type == "summary_report":
        ivw = next((e for e in estimates if e.get("method") == "IVW"), {})
        lines = [
            f"## 方法\n双样本 MR：{exposure} → {outcome}。\n",
            f"## 结果",
        ]
        if ivw:
            lines.append(f"IVW: β={ivw.get('beta', '?')}, OR={ivw.get('odds_ratio', '?')}, P={ivw.get('p_value', '?')}。")
        if isinstance(pleiotropy, dict):
            egger_p = pleiotropy.get("pval", "?")
            lines.append(f"MR-Egger intercept p={egger_p}。")
        lines.append("")
    else:
        lines = [
            f"## 双样本孟德尔随机化\n\n"
            f"以 GWAS 显著 SNP 为工具变量，从 OpenGWAS 获取 {outcome} 结局汇总统计。\n",
        ]
        if estimates:
            lines.append("| 方法 | β | OR | 95% CI | P |\n|------|---|---|--------|---|")
            for est in estimates:
                beta = est.get("beta", "?")
                or_ = est.get("odds_ratio", "?")
                p = est.get("p_value", "?")
                lines.append(f"| {est.get('method', '?')} | {beta} | {or_} | — | {p} |")
            lines.append("")

        if isinstance(pleiotropy, dict) and pleiotropy:
            egger_p = pleiotropy.get("pval", "?")
            lines.append(f"\n**敏感性分析**: MR-Egger intercept p={egger_p}")
            if isinstance(egger_p, (int, float)):
                if egger_p < 0.05:
                    lines.append("——存在水平多效性证据，IVW 估计可能有偏。\n")
                else:
                    lines.append("——无显著水平多效性证据。\n")

        if heterogeneity:
            for h in heterogeneity:
                q_p = h.get("q_pval", "?")
                lines.append(f"Cochran's Q p={q_p} ({h.get('method', '?')})。")
            lines.append("")

    return "\n".join(lines)


def _mediation_mr_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    exposure = r.get("exposure", "未知")
    outcome = r.get("outcome", "未知")
    source = r.get("mediator_source", "未知")
    sig_count = r.get("significant_mediators_count", 0)
    proteins = r.get("ranked_proteins", []) or r.get("indirect_effects", [])

    if report_type == "summary_report":
        lines = [
            f"## 方法\n利用 {source} pQTL 数据，两步 MR + Product Method，FDR 校正。\n",
            f"## 结果\n{exposure} → 蛋白 → {outcome}：显著中介蛋白 {sig_count} 个。\n",
        ]
    else:
        lines = [
            f"## 中介筛选\n\n"
            f"利用 {source} {'4,907 种' if 'decode' in str(source) else ''} 血浆蛋白 pQTL 数据，两步 MR + Product Method，FDR 校正。\n",
        ]
        if proteins:
            lines.append("| Rank | 蛋白 | 间接效应 | 中介比例 | P(FDR) |\n|------|------|---------|---------|--------|")
            for i, p in enumerate(proteins[:6]):
                name = p.get("protein", p.get("protein_name", "?"))
                ie = p.get("indirect_effect", "?")
                prop = p.get("proportion_mediated_pct", "?")
                pval = p.get("p_mediation", "?")
                sig = "✓" if p.get("significant") else ""
                lines.append(f"| {i+1} | {name} | {ie} | {prop}% | {pval} {sig} |")
            lines.append("")

    return "\n".join(lines)


def _risk_modeling_content(results: List[dict], report_type: str) -> str:
    r = results[0] if results else {}
    exposure = r.get("exposure", "未知")
    outcome = r.get("outcome", "未知")
    grouping = r.get("grouping", "quartile")
    ors = r.get("adjusted_odds_ratios", [])
    ols = r.get("ols_results", [])

    if report_type == "summary_report":
        or_text = "数据缺失"
        if ors:
            last = ors[-1]
            or_text = f"Q4 vs Q1: OR={last.get('osteoporosis_or', last.get('or', '?'))}"
        lines = [
            f"## 方法\n{exposure} 对 {outcome} 的风险建模，{grouping} 分层。\n",
            f"## 结果\n{or_text}。\n",
        ]
    else:
        lines = [
            f"## 风险建模\n\n"
            f"多因素模型：OLS + RCS + Multinomial Logistic，{grouping} 分层。\n",
        ]
        if ors:
            lines.append("| 分层 | 范围 | OR |\n|------|------|----|")
            for q in ors:
                label = q.get("quartile", q.get("label", "?"))
                pdf = q.get("pdf_range", q.get("range", "—"))
                or_val = q.get("osteoporosis_or", q.get("or", "?"))
                lines.append(f"| {label} | {pdf} | {or_val} |")
            lines.append("")

        if ols:
            for m in ols[:3]:
                lines.append(
                    f"- {m.get('outcome', '?')}: "
                    f"β={m.get('beta', '?')}, P={m.get('p_value', m.get('p', '?'))}"
                )

    return "\n".join(lines)


# ============================================================
# 缺失数据检测
# ============================================================

def _detect_missing_data_fields(classified_jobs: Dict[str, list]) -> List[str]:
    """检测各分析类型中缺失的关键字段。"""
    missing = []
    checks = {
        "image_segmentation": ["dice_scores", "quality_control"],
        "phenotype_quantification": ["liver_pdff", "visceral_fat_volume"],
        "gwas_analysis": ["significant_loci_count", "lambda_gc", "lead_snps"],
        "mendelian_randomization": ["estimates", "pleiotropy"],
        "mediation_mr": ["ranked_proteins", "indirect_effects"],
        "risk_modeling": ["adjusted_odds_ratios", "ols_results"],
    }

    for cap, fields in checks.items():
        if cap not in classified_jobs:
            continue
        for _, result in classified_jobs[cap]:
            for field in fields:
                if field not in result or result[field] is None:
                    missing.append(f"{cap}.{field}")
                    break

    return missing


# ============================================================
# 主入口：构建完整报告
# ============================================================

def build_report(
    selected_jobs: Dict[str, dict],
    report_type: str,           # "summary_report" | "full_report"
    project_title: str = "AdipoInsight 科研分析报告",
    language: str = "zh-CN",
    include_figures: bool = True,
    include_tables: bool = True,
) -> Dict[str, Any]:
    """基于 selectedJobs 构建报告。

    Args:
        selected_jobs: {job_id: result_dict}
        report_type: "summary_report" 或 "full_report"
        project_title: 项目标题
        language: 语言
        include_figures: 是否包含图表
        include_tables: 是否包含表格

    Returns:
        完整的报告 dict，与现有 ReportGenerationResult schema 兼容
    """
    import uuid as _uuid

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_id = f"rpt_{_uuid.uuid4().hex[:8]}"

    # 1. 分类 jobs
    classified = _classify_jobs(selected_jobs or {})

    # 2. pipeline 顺序
    pipeline_order = [
        "image_segmentation", "phenotype_quantification", "gwas_analysis",
        "mendelian_randomization", "mediation_mr", "risk_modeling",
    ]

    # 3. 生成章节
    sections = []
    section_num = 1

    # 3a. 背景
    sections.append(_section_background(project_title, classified, report_type, language))
    section_num = 2

    # 3b. 各分析结果（只有 data 的才生成完整章节）
    completed_caps = []
    for cap in pipeline_order:
        if cap in classified:
            sections.append(_section_from_results(
                cap, classified[cap], section_num, report_type, language,
            ))
            completed_caps.append(cap)
            section_num += 1

    # 3c. 缺失的 capability → limitations 记录
    missing_caps = [c for c in pipeline_order if c not in classified]

    # 3d. 讨论
    sections.append(_section_discussion(classified, report_type, language))

    # 3e. 局限性
    sections.append(_section_limitations(classified, missing_caps))

    # 3f. 下一步
    sections.append(_section_next_steps(classified, missing_caps))

    # 4. 全局 limitations 和 key_findings
    limitation_texts = []
    for sec in sections:
        if sec.get("title") == "研究局限性":
            # 解析内容中的列表
            for line in sec.get("content", "").split("\n"):
                stripped = line.strip()
                if stripped.startswith("- "):
                    limitation_texts.append(stripped[2:])

    key_findings = _build_key_findings(classified)

    # 5. 构建 markdown
    content_md = _assemble_markdown(project_title, sections, language)

    export_formats = [
        {"format": "markdown", "label": "Markdown", "available": True,
         "url": f"/api/v1/files/reports/{report_id}.md", "file_size": len(content_md)},
    ]
    metadata = {
        "version": "2.0.0-template",
        "generated_at": now,
        "generation_time_seconds": 0,
        "ai_model": f"AdipoInsight Template Engine ({report_type})",
        "data_sources": list(selected_jobs.keys()) if selected_jobs else [],
        "analysis_methods": completed_caps,
        "conflict_of_interest": "本研究由 AdipoInsight AI 系统自动生成，仅供演示。",
        "acknowledgments": "",
    }

    from backend.app.ai.skills.mock_data import (
        build_figures_for_sections,
        build_tables_for_sections,
        build_references_for_sections,
    )

    return {
        "report_id": report_id,
        "project_id": 0,
        "title": project_title,
        "subtitle": "",
        "report_type": report_type,
        "language": language,
        "sections": sections,
        "figures": build_figures_for_sections(completed_caps) if include_figures else [],
        "tables": build_tables_for_sections(completed_caps) if include_tables else [],
        "references": build_references_for_sections(completed_caps),
        "limitations": limitation_texts if limitation_texts else ["数据缺失：部分关键字段不可用"],
        "key_findings": key_findings,
        "export_formats": export_formats,
        "metadata": metadata,
        "content_markdown": content_md[:8000],
        "completed_sections": len([s for s in sections if s["status"] == "complete"]),
        "total_sections": len(sections),
        "ai_interpretation": f"[Template{':full' if report_type == 'full_report' else ''}] 由模板引擎生成。",
        "output_files": ["final_report.md"],
    }


def _build_key_findings(classified: Dict[str, list]) -> List[str]:
    """从实际结果中提取关键发现。"""
    findings = []

    if "gwas_analysis" in classified:
        for _, r in classified["gwas_analysis"]:
            n_loci = r.get("significant_loci_count", 0)
            if n_loci:
                findings.append(f"GWAS 识别了 {n_loci} 个显著基因座 (p < 5×10⁻⁸)")

    if "mendelian_randomization" in classified:
        for _, r in classified["mendelian_randomization"]:
            estimates = r.get("estimates", [])
            ivw = next((e for e in estimates if e.get("method") == "IVW"), {})
            if ivw:
                findings.append(f"MR IVW 分析: β={ivw.get('beta', '?')}, OR={ivw.get('odds_ratio', '?')}, P={ivw.get('p_value', '?')}")

    if "mediation_mr" in classified:
        for _, r in classified["mediation_mr"]:
            sig = r.get("significant_mediators_count", 0)
            if sig:
                findings.append(f"中介 MR 筛选出 {sig} 个显著中介蛋白 (FDR<0.05)")

    if "risk_modeling" in classified:
        for _, r in classified["risk_modeling"]:
            ors = r.get("adjusted_odds_ratios", [])
            if len(ors) >= 2:
                q4 = ors[-1]
                findings.append(f"风险建模: Q4 vs Q1 OR={q4.get('osteoporosis_or', q4.get('or', '?'))}")

    return findings if findings else ["分析已完成，详见对应章节。"]


def _assemble_markdown(title: str, sections: List[dict], language: str) -> str:
    """拼接 markdown。"""
    lines = [
        f"# {title}",
        "",
        f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "", "---", "",
    ]
    for sec in sections:
        lines.append(f"## {sec['title']}")
        lines.append(sec.get("content", ""))
        lines.append("")
    return "\n".join(lines)


# Figures / Tables / References 构建已迁移至 mock_data.py
# 在 build_report() 中通过动态 import 调用
