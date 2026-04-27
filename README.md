# Stock Research SOP — OpenClaw Skill

一个结构化的股票研究标准操作流程（SOP），适用于 A 股、港股、美股市场。

## 功能特性

- 📁 **分阶段数据采集** — 将研究拆分为可追踪的独立阶段
- 🔍 **自动化审计闭环** — 内置 3 次脚本化自审计机制
- 📊 **结构化输出** — JSON + Markdown 双格式报告
- 🔄 **增量更新支持** — 同一股票可持续追加分析，无需重建

## 快速开始

### 1. 安装 Skill

```bash
# 从 ClawHub 安装（未来可用）
clawhub install stock-research-sop

# 或手动复制
cp -r stock-research-sop/ ~/.openclaw/workspace/main/skills/
```

### 2. 配置路径

编辑 SKILL.md 中的配置部分：

```markdown
| STOCK_WORKSPACE_DIR | /path/to/your/stocks/ | 自定义工作目录 |
```

### 3. 触发研究

在 OpenClaw 对话中发送：

> "使用股票分析 SOP，从零开始分析腾讯"

## 研究流程

```
阶段1: 建档与识别
     ↓
阶段2A: 基础信息采集 → 2B: 行情采集 → 2C: 财务采集 → 2D: 资讯采集
     ↓
阶段3-4: 分析与母版报告生成
     ↓
阶段5: 审计闭环（最多3次）
     ↓
阶段6: 最终报告发布
```

## 工作目录结构

```
stocks/<TICKER>/
├── 00_meta/       # 元数据
├── 01_sources/    # 来源记录  
├── 02_raw/        # 原始数据
├── 03_normalized/ # 标准化摘要
├── 04_analysis/   # 分析报告
├── 05_reports/    # 最终报告与审计
└── 06_tracking/   # 增量追踪
```

## 推荐 Skill 组合

| 类别 | 技能包 |
|------|--------|
| **数据源** | akshare-stock, mx-finance-data, ths-financial-data |
| **分析引擎** | fundamental-stock-analysis, technical-analyst |
| **搜索补充** | tavily, web_article-search |

## 依赖要求

- Python 3.10+
- OpenClaw Gateway（用于 skill 加载）
- 可选：akshare、tushare 等 A 股数据接口

## 许可证

MIT License — 可以自由使用、修改和分发。

---

<small style="color: #666;">⚠️ **免责声明**：本 Skill 仅供学习研究和自动化工作流参考用途，不构成任何投资建议。股票投资存在风险，过往表现不代表未来收益，用户应自行评估并承担投资决策的全部责任。作者不对因使用本工具导致的任何直接或间接损失承担责任。请在做出任何投资决策前咨询持牌专业顾问。</small>
