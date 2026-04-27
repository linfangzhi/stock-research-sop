#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a compact fact packet for LLM reasoning.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    args = parser.parse_args()

    base = Path(args.dir)
    stock = read_json(base / '00_meta' / 'stock.json')
    company = read_json(base / '03_normalized' / 'company-profile.json')
    market = read_json(base / '03_normalized' / 'market-snapshot.json')
    financial = read_json(base / '03_normalized' / 'financial-summary.json')
    investment = read_json(base / '03_normalized' / 'investment-plan.json')
    events = read_json(base / '03_normalized' / 'event-cards.json')
    tech = read_json(base / '03_normalized' / 'technical-brief.json')
    source_log = read_text(base / '01_sources' / 'source-log.md')

    packet = {
        'stock': {
            'name': stock.get('name', ''),
            'ticker': stock.get('ticker', ''),
            'market': stock.get('market', ''),
            'exchange': stock.get('exchange', ''),
            'industry': stock.get('industry', ''),
        },
        'company_profile': company,
        'market_snapshot': market,
        'financial_summary': financial,
        'investment_plan': investment,
        'technical_brief': tech,
        'event_cards': events.get('events', []),
        'source_log_excerpt': source_log.splitlines()[:12],
    }

    out_json = base / '00_meta' / 'fact-packet.json'
    out_md = base / '05_reports' / 'fact-packet.md'
    out_json.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Pre-compute segment text
    segs = company.get("segments", [])
    if segs and isinstance(segs[0], dict):
        seg_text = ", ".join(f"{s.get('name','')}(~{s.get('revenue_pct','')}%)" for s in segs)
    else:
        seg_text = ", ".join(segs) if segs else "待补充"

    lines = [
        '# Fact Packet',
        '',
        '> 该文件用于给大模型提供紧凑事实包，减少重复读取 raw/normalized 文件的负担。',
        '',
        '## 标的',
        '',
        f'- 名称：{stock.get("name", "")}',
        f'- 代码：{stock.get("ticker", "")}',
        f'- 市场：{stock.get("market", "")}',
        f'- 行业：{stock.get("industry", "")}',
        '',
        '## 公司画像摘要',
        '',
        f'- 业务摘要：{company.get("business_summary", "待补充")}',
        f'- 细分结构：{seg_text or "待补充"}',
        '',
        '## 市场快照摘要',
        '',
        f'- 当前价：{market.get("price", "待补充")}',
        f'- 趋势：{market.get("trend_summary", "待补充")}',
        f'- 支撑位：{market.get("support_levels", []) or "待补充"}',
        f'- 压力位：{market.get("resistance_levels", []) or "待补充"}',
        '',
        '## 财务摘要',
        '',
        f'- 营收增速(1Y)：{financial.get("revenue_growth", {}).get("1y", "待补充")}',
        f'- 毛利率：{financial.get("profitability", {}).get("gross_margin", "待补充")}',
        f'- 净利率：{financial.get("profitability", {}).get("net_margin", "待补充")}',
        f'- ROE：{financial.get("profitability", {}).get("roe", "待补充")}',
        f'- PE_TTM：{financial.get("valuation", {}).get("pe_ttm", "待补充")}',
        '',
        '## 投资计划摘要',
        '',
        f'- 评级：{investment.get("rating", "待补充")}',
        f'- 目标价：{investment.get("target_price_mid", "待补充")} / {investment.get("target_price_high", "待补充")}',
        f'- 止损线：{investment.get("stop_loss", "待补充")}',
        '',
        '## 事件卡片摘要',
        ''
    ]
    events_list = events.get('events', [])
    if events_list:
        lines.extend([f'- {e.get("date", "")} | {e.get("type", "待判断")} | {e.get("title", "")}' for e in events_list[:8]])
    else:
        lines.append('- 暂无事件卡片')
    lines.extend([
        '',
        '## Prompt Handoff',
        '',
        '- 先复述事实，再做判断。',
        '- 明确区分：事实、推理、风险、反证、操作建议。',
        '- 若事实包与报告旧内容冲突，优先以最新 normalized 数据和事件卡片为准。'
    ])
    lines.extend([
        '',
        '## 使用建议',
        '',
        '- 大模型优先基于该事实包做推理、反证和结论汇总。',
        '- 若事实包缺字段，再回到 raw/normalized 文件补查，不要默认重新散读全部材料。'
    ])

    out_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'fact_packet_json': str(out_json), 'fact_packet_md': str(out_md)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
