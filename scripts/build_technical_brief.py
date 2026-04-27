#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def fmt_num(value, suffix='') -> str:
    if value is None or value == '':
        return '待补充'
    if isinstance(value, float):
        text = f'{value:.2f}'.rstrip('0').rstrip('.')
    else:
        text = str(value)
    return f'{text}{suffix}'


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a mechanical technical brief from market-snapshot.json')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--write-analysis', action='store_true', help='Also write 04_analysis/05_technical-facts.md')
    args = parser.parse_args()

    base = Path(args.dir)
    market = read_json(base / '03_normalized' / 'market-snapshot.json')
    if not market:
        raise SystemExit('Missing market-snapshot.json')

    out_json = base / '03_normalized' / 'technical-brief.json'
    out_md = base / '04_analysis' / '05_technical-facts.md'

    facts = {
        'date': market.get('date', ''),
        'price': market.get('price', ''),
        'change_pct': market.get('change_pct', ''),
        'high_52w': market.get('52w_high', ''),
        'low_52w': market.get('52w_low', ''),
        'distance_from_52w_high_pct': market.get('distance_from_52w_high_pct', ''),
        'long_trend': market.get('long_trend', ''),
        'mid_trend': market.get('mid_trend', ''),
        'short_trend': market.get('short_trend', ''),
        'support_levels': market.get('support_levels', []),
        'resistance_levels': market.get('resistance_levels', []),
        'stop_loss_line': market.get('stop_loss_line', ''),
        'take_profit_lines': market.get('take_profit_lines', []),
        'technical_flags': market.get('technical_flags', []),
        'turnover_rate': market.get('turnover_rate', ''),
        'turnover': market.get('turnover', ''),
        'volume': market.get('volume', ''),
    }
    out_json.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    supports = facts['support_levels'] or []
    resistances = facts['resistance_levels'] or []
    take_profits = facts['take_profit_lines'] or []
    flags = facts['technical_flags'] or []

    md = []
    md.append('# Technical Facts Brief')
    md.append('')
    md.append('> 本文件只保留机械归纳后的技术面事实，不做主观判断，供大模型在阶段 4-5 做解释和推演。')
    md.append('')
    md.append('## Facts')
    md.append('')
    md.append(f'- 数据日期：{facts["date"] or "待补充"}')
    md.append(f'- 收盘价：{fmt_num(facts["price"], "元")}')
    md.append(f'- 当日涨跌幅：{fmt_num(facts["change_pct"], "%")}')
    md.append(f'- 52周高点：{fmt_num(facts["high_52w"], "元")}')
    md.append(f'- 52周低点：{fmt_num(facts["low_52w"], "元")}')
    md.append(f'- 距52周高点：{fmt_num(facts["distance_from_52w_high_pct"], "%")}')
    md.append(f'- 长期趋势标签：{facts["long_trend"] or "待补充"}')
    md.append(f'- 中期趋势标签：{facts["mid_trend"] or "待补充"}')
    md.append(f'- 短期趋势标签：{facts["short_trend"] or "待补充"}')
    md.append(f'- 换手率：{fmt_num(facts["turnover_rate"], "%")}')
    md.append(f'- 成交量：{fmt_num(facts["volume"])}')
    md.append(f'- 成交额：{fmt_num(facts["turnover"])}')
    md.append('')
    md.append('## Key Levels')
    md.append('')
    md.append('- 支撑位：')
    if supports:
        md.extend([f'  - S{i + 1}: {fmt_num(v, "元")}' for i, v in enumerate(supports)])
    else:
        md.append('  - 待补充')
    md.append('- 压力位：')
    if resistances:
        md.extend([f'  - R{i + 1}: {fmt_num(v, "元")}' for i, v in enumerate(resistances)])
    else:
        md.append('  - 待补充')
    md.append(f'- 止损线：{fmt_num(facts["stop_loss_line"], "元")}')
    md.append('- 止盈参考：')
    if take_profits:
        md.extend([f'  - TP{i + 1}: {fmt_num(v, "元")}' for i, v in enumerate(take_profits)])
    else:
        md.append('  - 待补充')
    md.append('')
    md.append('## Signals')
    md.append('')
    if flags:
        md.extend([f'- {flag}' for flag in flags])
    else:
        md.append('- 待补充')
    md.append('')
    md.append('## Interpretation Handoff')
    md.append('')
    md.append('- 请大模型基于上述事实完成：趋势解释、关键承压位判断、失效条件、以及乐观/中性/悲观三种技术情景推演。')
    md.append('- 这一层不负责新增事实，只负责解释。')
    md.append('')

    if args.write_analysis:
        out_md.write_text('\n'.join(md), encoding='utf-8')

    print(json.dumps({
        'technical_brief_json': str(out_json),
        'technical_brief_md': str(out_md) if args.write_analysis else '',
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
