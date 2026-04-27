---
name: stock-research-sop
description: "当用户说"使用股票分析sop，从零开始分析XXX股票"、"使用股票研究SOP，从零开始研究XXX股票"、"按股票分析sop研究某只股票"时触发。用于为单只股票建立长期研究档案，优先用脚本完成可脚本化环节，按固定 SOP 采集原始数据、沉淀结构化 JSON、输出研究母版、执行内容级与结构级自审计。适用于 A 股、港股、美股。"
---

# Stock Research SOP (Open Source)

> 将"研究一支股票"变成可持续追加的档案流，而不是一次性聊天回答。

## 配置说明（使用前需自定义）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `STOCK_WORKSPACE_DIR` | `./stocks/` | 研究数据存储目录 |
| `SKILLS_DIR` | `~/skills/` | OpenClaw skills 安装路径 |
| `REPORT_SCRIPTS_PATH` | `./scripts/` | 分析脚本所在路径 |

## 工作目录结构

```
stocks/<TICKER>/
├── 00_meta/          # 元数据与状态追踪
│   ├── stock.json    # 标的基本信息
│   └── phase-status.json
├── 01_sources/       # 原始来源记录
│   └── source-log.md
├── 02_raw/           # 原始采集数据
├── 03_normalized/    # 标准化摘要 (JSON)
├── 04_analysis/      # 分析报告草稿
├── 05_reports/       # 最终报告与审计
│   ├── report-master.md
│   ├── release-report.md
│   └── audit/
└── 06_tracking/      # 增量更新追踪
    └── next-steps.md
```

## 触发后执行流程

当用户明确要求使用股票研究 SOP 时：

1. **识别标的** — 确认股票代码、名称、市场（A股/港股/美股）
2. **创建目录** — 调用 `scripts/create_stock_workspace.py` 建档
3. **按阶段采集数据** — 分 2A(基础)、2B(行情)、2C(财务)、2D(资讯) 四步
4. **生成研究母版** — `05_reports/report-master.md`
5. **执行审计闭环** — 脚本化自审计（最多3次）→ 通过后发布
6. **输出最终报告** — release-report.md + audit report

## 分阶段执行规则

### 阶段 1：建档与识别
- 确认标的信息，创建研究目录
- 生成问题清单（如信息不完整时）

### 阶段 2A：基础标的信息采集
- 公司基本介绍、行业分类、市场定位
- 固化方式：优先调用 `save_basic_profile.py`

### 阶段 2B：行情与技术原始数据采集  
- 当前价、52周高低、均线、趋势判断
- 固化方式：优先调用 `save_market_snapshot.py`

### 阶段 2C：财务原始数据采集
- 收入、利润、估值、现金流数据
- 固化方式：优先调用 `save_financial_summary.py`

### 阶段 2D：新闻公告与参考资料采集
- 公告、新闻、研报链接逐条记录
- 固化方式：使用 `append_source_item.py` 追加

## 强制完成标准

一份完整研究必须包含：

- [x] 明确结论（看多/看空/中性）
- [x] 推理过程与假设说明
- [x] 基本面分析（财务健康度、成长性）
- [x] 技术分析（趋势、支撑位、压力位）
- [x] 投资建议与仓位建议
- [x] 止盈线与止损线（含计算方法）
- [x] 风险因素与反证
- [x] 参考资料来源链接

## 推荐技能协作顺序

### 1. 数据源 (采集阶段)
| 技能 | 用途 |
|------|------|
| `akshare-stock` | A股行情/财务数据 |
| `mx-finance-data` | 多维度金融数据 |
| `ths-financial-data` | 同花顺数据源 |
| `tavily` / `web_search` | 新闻与资讯搜索 |

### 2. 分析引擎 (分析阶段)  
| 技能 | 用途 |
|------|------|
| `fundamental-stock-analysis` | 基本面深度分析 |
| `technical-analyst` | 技术面量化分析 |
| `stock-analyst` | 综合分析框架 |

## 执行约束（重要）

- **一次只推进一个阶段**，不要跨阶段跳跃
- **单个 tool-call 参数保持简短**，复杂逻辑交给脚本文件
- **大块内容优先写入文件**，不直接塞进聊天回复
- **如果某次调用失败**，先固化已确认部分，再进入下一阶段

## 总控脚本（推荐用法）

```bash
python3 scripts/research_workflow_controller.py --dir <STOCK_DIR> \
    --ticker <TICKER> \
    --market <CN|HK|US> \
    --name "<股票名称>"
```

自动执行：审计 → 回补（最多3次）→ 生成报告 → 发布

## 输出风格要求

- 事实和判断分开陈述
- 先结构化，后总结
- 每次更新保留时间戳和来源
- 允许使用专业型 emoji（📈、📊、✅、⚠️）提升可读性

---
*本 SOP 设计目标是可追溯、可接力、可长期维护的研究流程。*
