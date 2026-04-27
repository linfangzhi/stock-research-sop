#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a compact model/session usage summary block for final stock report docs.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--model', default='', help='Model name')
    parser.add_argument('--tokens-in', default='', help='Input tokens summary, e.g. 73k')
    parser.add_argument('--tokens-out', default='', help='Output tokens summary, e.g. 4.2k')
    parser.add_argument('--context', default='', help='Context usage summary, e.g. 91k/200k (45%)')
    parser.add_argument('--cache-hit', default='', help='Cache hit summary, e.g. 55%')
    parser.add_argument('--phase', default='6/6', help='Phase progress summary')
    parser.add_argument('--rating', default='', help='Final rating summary')
    parser.add_argument('--price', default='', help='Current price summary')
    parser.add_argument('--target', default='', help='Target price summary')
    parser.add_argument('--stop-loss', default='', dest='stop_loss', help='Stop loss summary')
    parser.add_argument('--audit-verdict', default='待补充', dest='audit_verdict', help='Audit verdict summary')
    args = parser.parse_args()

    base = Path(args.dir)
    stock = read_json(base / '00_meta' / 'stock.json')
    out = base / '05_reports' / 'session-status-summary.md'

    lines = []
    lines.append('# 🧠 模型状态与用量摘要')
    lines.append('')
    lines.append(f'> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('| 项目 | 内容 |')
    lines.append('|---|---|')
    lines.append(f'| 模型 | {args.model or "待补充"} |')
    lines.append(f'| Tokens | {((args.tokens_in or "?") + " in / " + (args.tokens_out or "?") + " out").strip()} |')
    lines.append(f'| 上下文 | {args.context or "待补充"} |')
    lines.append(f'| 缓存命中率 | {args.cache_hit or "待补充"} |')
    lines.append(f'| 研究进度 | ✅ {args.phase} |')
    lines.append(f'| 审计状态 | {args.audit_verdict} |')
    lines.append('')
    lines.append('## 📊 核心结论回顾')
    lines.append('')
    lines.append('| 项目 | 内容 |')
    lines.append('|---|---|')
    lines.append(f'| 标的 | {stock.get("name", "")} ({stock.get("ticker", "")}) |')
    lines.append(f'| 评级 | {args.rating or "待补充"} |')
    lines.append(f'| 当前价 | {args.price or "待补充"} |')
    lines.append(f'| 目标价 | {args.target or "待补充"} |')
    lines.append(f'| 止损线 | {args.stop_loss or "待补充"} |')
    lines.append('')
    lines.append('> 说明：本摘要仅用于记录本次研究生成阶段的大模型状态和产出概况，便于后续复盘与增量更新。')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
