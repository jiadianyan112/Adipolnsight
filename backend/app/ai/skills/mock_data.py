"""
报告生成 Mock 数据 — 集中管理

所有硬编码的章节模板、图表引用、参考文献、AI 解读文本均存放于此。
标注 [MOCK] 的数据仅用于演示，接入真实 LLM 后将由 context_builder 动态生成。

使用方式：
    from backend.app.ai.skills.mock_data import (
        SECTION_DEFS,
        SECTION_CONTENT_TEMPLATES,
        SECTION_ONE_LINERS,
        MOCK_FIGURES,
        MOCK_TABLES,
        MOCK_REFERENCES,
        MOCK_AI_INTERPRETATION,
        build_related_figures,
        build_related_tables,
        build_figures_for_sections,
        build_tables_for_sections,
    )
"""

from typing import Any, Dict, List

# ===== 章节定义 =====

SECTION_DEFS: List[Dict[str, Any]] = [
    {"key": "background", "title": "项目背景与研究目标"},
    {"key": "segmentation", "title": "AI 影像分割结果"},
    {"key": "phenotype", "title": "脂肪表型量化"},
    {"key": "gwas", "title": "GWAS 分析结果"},
    {"key": "mr", "title": "MR 因果推断结果"},
    {"key": "mediation_mr", "title": "中介 MR 蛋白筛选结果"},
    {"key": "risk_modeling", "title": "风险建模结果"},
    {"key": "discussion", "title": "综合讨论与结论"},
    {"key": "limitations", "title": "研究局限性与展望"},
]

# ===== [MOCK] 章节内容模板 =====

SECTION_CONTENT_TEMPLATES: Dict[str, str] = {
    "background": (
        "## 研究背景\n\n"
        "肝脏脂肪含量（Liver PDFF）升高与非酒精性脂肪肝病（NAFLD）密切相关，"
        "近年研究提示 NAFLD 可能通过系统性炎症、胰岛素抵抗及脂肪因子分泌异常等途径影响骨代谢。"
        "然而，肝脏脂肪积累与骨质疏松之间的因果关系及其分子机制尚不完全明确。\n\n"
        "## 研究目标\n\n"
        "1. 量化肝脏 PDFF 与骨密度/骨质疏松风险的关联强度\n"
        "2. 利用孟德尔随机化方法评估因果关系\n"
        "3. 识别介导肝脏-骨骼轴的血浆蛋白中介因子\n"
        "4. 构建基于影像和遗传特征的综合风险预测模型\n\n"
        "## 研究设计\n\n"
        "本研究整合腹部 MRI 影像组学（TSSA-UNet 自动分割）、"
        "UK Biobank 基因组学数据（n≈40,000，EUR）、"
        "deCODE 血浆蛋白 pQTL 数据（4,907 种蛋白）及 OpenGWAS 公开数据库，"
        "采用「影像 → 遗传 → 因果 → 中介 → 临床」五步分析策略。"
    ),
    "segmentation": (
        "## AI 影像分割\n\n"
        "使用 TSSA-UNet v2.1 对腹部 MRI DIXON 序列进行多器官自动分割，覆盖肝脏、内脏脂肪、"
        "皮下脂肪、胰腺和骨髓 5 个解剖区域。\n\n"
        "TSSA-UNet 的 3D 全分辨率训练策略在腹部脂肪组织分割上表现优异，"
        "肝脏 DICE 系数达 0.95，满足高精度体脂定量的临床前研究需求。"
    ),
    "phenotype": (
        "## 脂肪表型量化\n\n"
        "基于分割掩膜提取 9 项定量指标：肝脏 PDFF、内脏/皮下脂肪体积、骨髓脂肪分数、"
        "全身脂肪百分比、肌肉体积、SAT/VAT 比值及骨密度。\n\n"
        "肝脏 PDFF 均值 9.8%，高于一般人群（~5%），提示存在早期脂肪肝。"
    ),
    "gwas": (
        "## GWAS 全基因组关联分析\n\n"
        "以 REGENIE 方法对 40,484 例 EUR 样本进行分析，纳入年龄、性别、BMI "
        "及前 10 个遗传主成分为协变量。质控标准：MAF ≥ 0.01，HWE p ≥ 1×10⁻⁶。\n\n"
        "共识别 18 个独立显著基因座 (p < 5×10⁻⁸)，λ_GC = 1.003，"
        "基因组膨胀系数接近 1.0，表明群体分层和隐性关联控制良好。"
    ),
    "mr": (
        "## 双样本孟德尔随机化\n\n"
        "以 GWAS 显著 SNP 为工具变量，利用 OpenGWAS 公开数据库获取结局 GWAS 汇总统计，"
        "执行双样本 MR 分析。主要分析方法为 IVW，辅以 MR-Egger、加权中位数法和加权众数法。\n\n"
        "IVW 结果显示正向因果效应 (OR = 1.47, 95% CI: 1.21–1.79, p = 4.8×10⁻⁵)。"
        "MR-Egger intercept 检验未发现显著水平多效性 (p > 0.05)。"
        "Cochran's Q 检验显示中等异质性。"
    ),
    "mediation_mr": (
        "## 中介 MR 蛋白筛选\n\n"
        "利用 deCODE 4,907 种血浆蛋白 pQTL 数据，两步 MR 结合 Product Method 评估中介效应，"
        "FDR 校正 (α = 0.05)。\n\n"
        "筛选出 POR (P450 氧化还原酶) 和 NAAA (N-酰基乙醇胺酸酰胺酶) 为显著中介蛋白。"
        "POR 中介效应占比 33.0%，NAAA 占比 15.3%。"
    ),
    "risk_modeling": (
        "## 疾病风险建模\n\n"
        "多因素模型 (OLS + RCS + Multinomial Logistic) 评估 PDFF 对骨质疏松风险的剂量-反应关系。\n\n"
        "Q4 vs Q1 (PDFF ≤ 5.2% vs > 12.8%): OR = 1.59 (95% CI: 1.28–1.98, p < 0.001)。"
        "RCS 曲线无显著非线性证据 (P<sub>nonlinear</sub> = 0.21)。"
        "AUC ≈ 0.72，建议 PDFF ≥ 10% 为高风险筛查阈值。"
    ),
    "discussion": (
        "## 综合讨论\n\n"
        "本研究整合影像组学、基因组学和蛋白质组学多维度数据，"
        "系统评估了肝脏脂肪含量与骨质疏松风险之间的关联。\n\n"
        "GWAS 识别了 18 个显著基因座，MR 提供因果证据 (IVW OR=1.47)，"
        "中介 MR 揭示 POR/NAAA 为潜在机制蛋白，风险建模建议临床筛查阈值。\n\n"
        "四级证据链（GWAS → MR → Mediation → Risk）一致支持肝脏-骨骼轴假说。"
    ),
    "limitations": (
        "## 研究局限性与展望\n\n"
        "1. 本研究使用 Mock 模拟数据，结果不反映真实生物学发现。\n"
        "2. GWAS 样本限于 EUR 人群，跨人群泛化性待独立队列验证。\n"
        "3. MR 分析依赖工具变量三大假设，违反任一假设将导致有偏估计。\n"
        "4. 中介分析仅覆盖 cis-pQTL，可能遗漏 trans-pQTL 的中介效应。\n"
        "5. 横断面设计无法确定因果时序。\n"
        "6. 接入真实数据后将自动更新以上结论。"
    ),
}

# ===== [MOCK] 章节一句话摘要 =====

SECTION_ONE_LINERS: Dict[str, str] = {
    "background": "阐述肝脏-骨骼轴研究背景及多组学整合研究设计",
    "segmentation": "TSSA-UNet v2.1 成功分割 5 个解剖区域，DICE 0.84–0.95",
    "phenotype": "提取 9 项脂肪表型指标，肝脏 PDFF 9.8%",
    "gwas": "REGENIE 识别 18 个显著基因座，λ_GC=1.003",
    "mr": "IVW 支持因果效应 (OR=1.47, p<0.001)",
    "mediation_mr": "POR 和 NAAA 为显著中介蛋白 (FDR<0.05)",
    "risk_modeling": "Q4 PDFF 骨质疏松风险增加 59%，建议 PDFF=10% 为阈值",
    "discussion": "综合多组学证据支持肝脏-骨骼轴假说",
    "limitations": "Mock 数据、单一人群、横断面设计为主要限制",
}

# ===== [MOCK] 图表引用 =====

def build_related_figures(section_key: str) -> List[Dict[str, str]]:
    """按章节 key 返回关联图表引用。"""
    fig_map = {
        "segmentation": [
            {"figure_id": "fig_seg_1", "caption": "Figure 1: 腹部 MRI 多器官分割叠加图", "type": "segmentation_overlay"},
        ],
        "gwas": [
            {"figure_id": "fig_gwas_1", "caption": "Figure 2: Liver PDFF GWAS Manhattan 图", "type": "manhattan"},
            {"figure_id": "fig_gwas_2", "caption": "Figure 3: GWAS Q-Q 图", "type": "qq_plot"},
        ],
        "mr": [
            {"figure_id": "fig_mr_1", "caption": "Figure 4: MR SNP效应散点图", "type": "scatter"},
        ],
        "mediation_mr": [
            {"figure_id": "fig_medmr_1", "caption": "Figure 5: 中介 MR 森林图", "type": "forest"},
            {"figure_id": "fig_medmr_2", "caption": "Figure 6: 肝脏-蛋白-骨骼机制流程图", "type": "mechanism_diagram"},
        ],
        "risk_modeling": [
            {"figure_id": "fig_risk_1", "caption": "Figure 7: PDFF-骨质疏松 RCS 曲线", "type": "rcs_curve"},
        ],
    }
    return fig_map.get(section_key, [])


def build_related_tables(section_key: str) -> List[Dict[str, Any]]:
    """按章节 key 返回关联表格引用。"""
    tbl_map = {
        "segmentation": [
            {"table_id": "tbl_seg_1", "caption": "Table 1: 多器官分割 DICE 评分",
             "columns": ["解剖结构", "DICE", "评价"]},
        ],
        "phenotype": [
            {"table_id": "tbl_pheno_1", "caption": "Table 2: 定量脂肪表型指标",
             "columns": ["指标", "数值", "单位"]},
        ],
        "gwas": [
            {"table_id": "tbl_gwas_1", "caption": "Table 3: 先导 SNP 汇总",
             "columns": ["SNP", "Chr", "BP", "Beta", "P"]},
        ],
        "mr": [
            {"table_id": "tbl_mr_1", "caption": "Table 4: MR 估计值汇总",
             "columns": ["方法", "nSNP", "β", "OR", "95%CI", "P"]},
            {"table_id": "tbl_mr_2", "caption": "Table 5: 敏感性分析",
             "columns": ["检验", "统计量", "P"]},
        ],
        "mediation_mr": [
            {"table_id": "tbl_medmr_1", "caption": "Table 6: 显著中介蛋白排序",
             "columns": ["Rank", "蛋白", "间接效应", "中介比例", "P(FDR)"]},
        ],
        "risk_modeling": [
            {"table_id": "tbl_risk_1", "caption": "Table 7: 四分位风险分层 OR",
             "columns": ["四分位", "PDFF范围", "Osteoporosis OR"]},
            {"table_id": "tbl_risk_2", "caption": "Table 8: 模型性能",
             "columns": ["模型", "AUC", "R²"]},
        ],
        "discussion": [
            {"table_id": "tbl_disc_1", "caption": "Table 9: 关键发现汇总",
             "columns": ["发现", "效应量", "证据等级"]},
        ],
    }
    return tbl_map.get(section_key, [])


# ===== [MOCK] 全文图表清单 =====

MOCK_FIGURES: List[Dict[str, Any]] = [
    {"figure_id": "fig_seg_1", "number": 1, "caption": "Figure 1: 腹部 MRI 多器官分割叠加图",
     "url": "/api/v1/files/report/fig_seg_overlay.png", "type": "segmentation_overlay",
     "section_number": 2, "alt_text": "TSSA-UNet overlay", "source_job_id": "mock_seg"},
    {"figure_id": "fig_gwas_1", "number": 2, "caption": "Figure 2: GWAS Manhattan 图",
     "url": "/api/v1/files/report/fig_manhattan.png", "type": "manhattan",
     "section_number": 4, "alt_text": "Manhattan plot", "source_job_id": "mock_gwas"},
    {"figure_id": "fig_gwas_2", "number": 3, "caption": "Figure 3: GWAS Q-Q 图",
     "url": "/api/v1/files/report/fig_qq.png", "type": "qq_plot",
     "section_number": 4, "alt_text": "QQ plot", "source_job_id": "mock_gwas"},
    {"figure_id": "fig_mr_1", "number": 4, "caption": "Figure 4: MR 散点图",
     "url": "/api/v1/files/report/fig_mr_scatter.png", "type": "scatter",
     "section_number": 5, "alt_text": "MR scatter", "source_job_id": "mock_mr"},
    {"figure_id": "fig_medmr_1", "number": 5, "caption": "Figure 5: 中介 MR 森林图",
     "url": "/api/v1/files/report/fig_medmr_forest.png", "type": "forest",
     "section_number": 6, "alt_text": "Forest plot", "source_job_id": "mock_medmr"},
    {"figure_id": "fig_medmr_2", "number": 6, "caption": "Figure 6: 机制流程图",
     "url": "/api/v1/files/report/fig_mechanism.png", "type": "mechanism_diagram",
     "section_number": 6, "alt_text": "Mechanism diagram", "source_job_id": "mock_medmr"},
    {"figure_id": "fig_risk_1", "number": 7, "caption": "Figure 7: RCS 剂量反应曲线",
     "url": "/api/v1/files/report/fig_rcs.png", "type": "rcs_curve",
     "section_number": 7, "alt_text": "RCS curve", "source_job_id": "mock_risk"},
]

MOCK_TABLES: List[Dict[str, Any]] = [
    {"table_id": "tbl_seg_1", "number": 1, "caption": "Table 1: DICE 评分",
     "columns": [{"key": "organ", "label": "结构"}, {"key": "dice", "label": "DICE", "format": "number", "precision": 3}],
     "rows": [], "section_number": 2, "source_job_id": "mock_seg", "footnotes": []},
    {"table_id": "tbl_mr_1", "number": 2, "caption": "Table 2: MR 估计值",
     "columns": [{"key": "method", "label": "方法"}, {"key": "beta", "label": "β", "format": "number", "precision": 3}],
     "rows": [], "section_number": 5, "source_job_id": "mock_mr", "footnotes": ["Primary: IVW"]},
    {"table_id": "tbl_medmr_1", "number": 3, "caption": "Table 3: 中介蛋白排序",
     "columns": [{"key": "protein", "label": "蛋白"}, {"key": "indirect", "label": "间接效应", "format": "number", "precision": 4}],
     "rows": [], "section_number": 6, "source_job_id": "mock_medmr", "footnotes": ["FDR corrected"]},
    {"table_id": "tbl_risk_1", "number": 4, "caption": "Table 4: 风险分层 OR",
     "columns": [{"key": "quartile", "label": "四分位"}, {"key": "or", "label": "OR", "format": "number", "precision": 2}],
     "rows": [], "section_number": 7, "source_job_id": "mock_risk", "footnotes": ["Adjusted for age, sex, BMI"]},
]

MOCK_REFERENCES: List[Dict[str, Any]] = [
    {"ref_id": "ref_1", "number": 1, "doi": "10.1038/s41586-018-0579-z",
     "text": "Bycroft C, et al. UK Biobank. Nature 2018;562:203–9.", "type": "database", "cited_in_sections": [1, 3, 4]},
    {"ref_id": "ref_2", "number": 2, "doi": "10.1038/s41588-021-00978-w",
     "text": "Ferkingstad E, et al. Plasma proteome genetics. Nat Genet 2021;53:1712–21.", "type": "database", "cited_in_sections": [6]},
    {"ref_id": "ref_3", "number": 3, "doi": "10.7554/eLife.34408",
     "text": "Hemani G, et al. MR-Base. eLife 2018;7:e34408.", "type": "method", "cited_in_sections": [5]},
    {"ref_id": "ref_4", "number": 4, "doi": "10.12688/wellcomeopenres.15555.2",
     "text": "Burgess S, et al. MR guidelines. Wellcome Open Res 2019;4:186.", "type": "method", "cited_in_sections": [5, 6]},
    {"ref_id": "ref_5", "number": 5, "doi": "10.1101/2020.08.10.244293",
     "text": "Elsworth B, et al. OpenGWAS. bioRxiv 2020.", "type": "database", "cited_in_sections": [4, 5]},
    {"ref_id": "ref_6", "number": 6, "doi": "10.1038/s41592-020-01008-z",
     "text": "Isensee F, et al. nnU-Net. Nat Methods 2021;18:203–11.", "type": "method", "cited_in_sections": [2]},
]

MOCK_AI_INTERPRETATION = (
    "## AI 综合分析\n\n"
    "本研究整合影像组学、基因组学和蛋白质组学多维度数据，"
    "系统评估了肝脏 PDFF 与骨质疏松风险的关联。主要结论：\n\n"
    "1. **因果证据链完整**: GWAS → MR → Mediation → Risk Modeling 四级证据一致\n"
    "2. **临床转化潜力**: PDFF=10% 阈值 + Q4 1.59x OR 提供可操作的筛查标准\n"
    "3. **机制可验证性**: POR 和 NAAA 可作为下游实验验证的靶点\n\n"
    "> 本解读由 Mock AI 生成。接入 LLM 后将提供基于实际数据的深度讨论。\n"
)

# ===== 基于已完成 capability 动态构建图表 =====

def build_figures_for_sections(completed_caps: List[str]) -> List[Dict[str, Any]]:
    """仅返回有数据支撑的图表。"""
    figures = []
    fig_map = {
        "image_segmentation": [
            {"figure_id": "fig_seg_1", "number": 1, "caption": "Figure 1: 腹部 MRI 分割叠加图",
             "type": "segmentation_overlay", "section_number": 2, "alt_text": "TSSA-UNet overlay", "source_job_id": ""},
        ],
        "gwas_analysis": [
            {"figure_id": "fig_gwas_1", "number": 2, "caption": "Figure 2: GWAS Manhattan 图",
             "type": "manhattan", "section_number": 4, "alt_text": "Manhattan plot", "source_job_id": ""},
            {"figure_id": "fig_gwas_2", "number": 3, "caption": "Figure 3: GWAS Q-Q 图",
             "type": "qq_plot", "section_number": 4, "alt_text": "QQ plot", "source_job_id": ""},
        ],
        "mendelian_randomization": [
            {"figure_id": "fig_mr_1", "number": 4, "caption": "Figure 4: MR 散点图",
             "type": "scatter", "section_number": 5, "alt_text": "MR scatter", "source_job_id": ""},
        ],
        "mediation_mr": [
            {"figure_id": "fig_medmr_1", "number": 5, "caption": "Figure 5: 中介 MR 森林图",
             "type": "forest", "section_number": 6, "alt_text": "Forest plot", "source_job_id": ""},
        ],
        "risk_modeling": [
            {"figure_id": "fig_risk_1", "number": 6, "caption": "Figure 6: RCS 剂量反应曲线",
             "type": "rcs_curve", "section_number": 7, "alt_text": "RCS curve", "source_job_id": ""},
        ],
    }
    for cap in completed_caps:
        if cap in fig_map:
            figures.extend(fig_map[cap])
    return figures


def build_tables_for_sections(completed_caps: List[str]) -> List[Dict[str, Any]]:
    """仅返回有数据支撑的表格。当前为占位实现，接入真实数据后按 results 动态生成。"""
    return []


def build_references_for_sections(completed_caps: List[str]) -> List[Dict[str, Any]]:
    """仅包含相关方法的参考文献。"""
    all_refs = {
        "image_segmentation": [
            {"ref_id": "ref_nnunet", "number": 1, "doi": "10.1038/s41592-020-01008-z",
             "text": "Isensee F, et al. nnU-Net. Nat Methods 2021;18:203–11.", "type": "method", "cited_in_sections": [2]},
        ],
        "gwas_analysis": [
            {"ref_id": "ref_ukb", "number": 2, "doi": "10.1038/s41586-018-0579-z",
             "text": "Bycroft C, et al. UK Biobank. Nature 2018;562:203–9.", "type": "database", "cited_in_sections": [4]},
        ],
        "mendelian_randomization": [
            {"ref_id": "ref_mrbase", "number": 3, "doi": "10.7554/eLife.34408",
             "text": "Hemani G, et al. MR-Base. eLife 2018;7:e34408.", "type": "method", "cited_in_sections": [5]},
        ],
        "mediation_mr": [
            {"ref_id": "ref_decode", "number": 4, "doi": "10.1038/s41588-021-00978-w",
             "text": "Ferkingstad E, et al. Plasma proteome genetics. Nat Genet 2021;53:1712–21.", "type": "database", "cited_in_sections": [6]},
        ],
    }
    refs = []
    seen = set()
    for cap in completed_caps:
        for ref in all_refs.get(cap, []):
            if ref["ref_id"] not in seen:
                refs.append(ref)
                seen.add(ref["ref_id"])
    for i, ref in enumerate(refs):
        ref["number"] = i + 1
    return refs
