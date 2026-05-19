# AdipoInsight 回归测试清单

> 版本: v0.3.0  
> 最后更新: 2026-05-19

## 自动化测试命令

```bash
# 前端纯函数单元测试
cd frontend && npx vitest run

# 前端构建检查
cd frontend && npm run build

# 后端 API 冒烟测试 (需要后端运行中)
bash scripts/smoke-test.sh
```

## P0 回归问题与对应验收项

### Bug 1: 报告生成 UI 卡在 70%

**修复位置**: `frontend/src/pages/ReportPage.tsx`, `frontend/src/hooks/usePolling.ts`

**验收步骤**:
1. 创建新项目 → 进入工作区
2. 运行完整分析流水线（等待完成）
3. 点击"生成报告"或导航到报告页面
4. ✅ 观察页面从"正在生成"过渡到"科研报告"预览
5. ✅ 进度条不再卡在 70%
6. ✅ 报告内容（标题、章节、导出按钮）正确显示

**自动化检查**: `scripts/smoke-test.sh` 测试 7、8

### Bug 2: 进度超过 100% (114% / 8/7)

**修复位置**: `frontend/src/pages/ProjectWorkspacePage.tsx`, `frontend/src/utils/pipelineProgress.ts`

**验收步骤**:
1. 项目工作区 → 单独运行 GWAS
2. 等待 GWAS 完成 → 点击"运行全部"
3. ✅ 流水线概览显示 `100%` 和 `7/7`（不是 `114%` 或 `8/7`）
4. ✅ 进度条填充不超过 100%

**自动化检查**: `npx vitest run` — "Regression guards: progress never exceeds 100%" 测试组

### Bug 3: Recharts 图表 width/height=-1 警告

**修复位置**: `frontend/src/components/charts/SafeChartContainer.tsx`

**验收步骤**:
1. 打开任意项目工作区
2. 打开浏览器控制台
3. ✅ 无 `width(-1) and height(-1) of chart should be greater than 0` 警告
4. ✅ 切换到 GWAS/MR tab 仍无该警告

**自动化检查**: 浏览器控制台筛选 `width(-1)` → 应为 0 条

### Bug 4: Mock 数据不一致

**修复位置**: `backend/app/ai/mock_result_factory.py`, `backend/app/ai/skills/gwas_analysis.py`

**验收步骤**:
1. 创建项目 A: exposure=LDL_Cholesterol, outcome=Osteoporosis
2. 运行 GWAS
3. ✅ GWAS 结果 phenotype 显示为 `LDL_Cholesterol`
4. 创建项目 B: exposure=Different_Trait, outcome=Different_Outcome
5. 运行 GWAS
6. ✅ 项目 B 的 GWAS phenotype 显示为 `Different_Trait`

**自动化检查**: `scripts/smoke-test.sh` 测试 10

### Bug 5: 重复轮询

**修复位置**: `frontend/src/hooks/pollingController.ts`, `frontend/src/hooks/usePolling.ts`

**验收步骤**:
1. 打开项目工作区，所有任务已完成
2. 打开 Network 面板
3. ✅ 初始加载后 5 秒内轮询自动停止
4. ✅ 不再出现 70+ 次重复 `/tasks` 请求

### Bug 6: 报告生成路径双轨

**修复位置**: `backend/app/api/reports.py`

**验收步骤**:
1. ✅ `POST /api/v1/projects/:id/reports/generate` 返回 `{job_id: "..."}`
2. ✅ JobManager 中可查询到此 job
3. ✅ 报告结果可读取

## 手动验收流程 (比赛展示前)

### 完整走查 (15 分钟)

- [ ] 1. 首页加载 — 项目列表可见
- [ ] 2. 创建新项目 — 填写 exposure/outcome/mediator，创建成功
- [ ] 3. AI Chat 输入 — 输入 "做 GWAS 分析" 能收到回复
- [ ] 4. 运行 GWAS — 参数中 phenotype = 项目 exposure
- [ ] 5. 查看 GWAS 结果 — 显示 Manhattan 图、先导 SNP 表
- [ ] 6. 运行完整流水线 — 7 步全部完成，进度 100%
- [ ] 7. 进度显示 7/7 — 不是 8/7
- [ ] 8. 流程总览 WorkflowStepper — 所有步骤 ✔ 已完成
- [ ] 9. 生成报告 — 过渡到预览页，不再卡 70%
- [ ] 10. 报告内容完整 — 项目背景、讨论、局限性章节
- [ ] 11. Tab 导航切换 — 所有 7 个 tab 可点击
- [ ] 12. Toast 通知 — 流水线启动/完成时有通知
- [ ] 13. 控制台无红色错误 — 0 errors
- [ ] 14. 控制台无图表宽高警告 — 0 chart width/height warnings

### 跨项目数据隔离

- [ ] 创建 project A → 运行 GWAS → 结果中 phenotype = A.exposure
- [ ] 创建 project B → 运行 GWAS → 结果中 phenotype = B.exposure
- [ ] Project A 和 B 数据不串

### 长期运行稳定性

- [ ] 5 分钟后轮询请求 ≤ 3 次（管道完成后）
- [ ] 无内存泄漏（切换项目后无遗留请求）
- [ ] 页面刷新后状态恢复正确

## 后端启动顺序

```bash
# 1. 启动后端
cd /e/Adipolnsight
uvicorn backend.app.main:app --reload --port 8000

# 2. 启动前端 (新终端)
cd /e/Adipolnsight/frontend
npm run dev

# 3. 运行冒烟测试
cd /e/Adipolnsight
bash scripts/smoke-test.sh
```
