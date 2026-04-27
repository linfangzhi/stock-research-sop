#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def main() -> int:
    parser = argparse.ArgumentParser(description='Build peer comparison skeleton for valuation analysis.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--peer', action='append', default=[], help='Peer name, repeatable')
    args = parser.parse_args()

    base = Path(args.dir)
    stock = read_json(base / '00_meta' / 'stock.json')
    company = read_json(base / '03_normalized' / 'company-profile.json')
    financial = read_json(base / '03_normalized' / 'financial-summary.json')
    peer_path = base / '03_normalized' / 'peer-list.json'
    out_md = base / '04_analysis' / '04_valuation-peer-table.md'

    existing = read_json(peer_path)
    existing_peers = existing.get('peers', []) if isinstance(existing, dict) else []
    peers = []
    seen = set()
    default_peers = []
    industry = (company.get('industry') or stock.get('industry') or '').lower()
    if '半导体' in industry or '存储' in industry:
        default_peers = ['北京君正', '普冉股份', '东芯股份']
    elif '白酒' in industry:
        default_peers = ['五粮液', '泸州老窖', '山西汾酒']

    for name in existing_peers + args.peer + default_peers:
        if not name or name in seen:
            continue
        seen.add(name)
        peers.append(name)

    payload = {
        'main': {
            'name': stock.get('name', ''),
            'ticker': stock.get('ticker', ''),
            'industry': company.get('industry', ''),
            'pe_ttm': financial.get('valuation', {}).get('pe_ttm'),
            'pb': financial.get('valuation', {}).get('pb'),
            'revenue_growth_1y': financial.get('revenue_growth', {}).get('1y'),
            'gross_margin': financial.get('profitability', {}).get('gross_margin'),
            'roe': financial.get('profitability', {}).get('roe'),
        },
        'peers': peers,
        'table_fields': ['市值', 'PE_TTM', 'PB', 'PS', '营收增速', '净利增速', '毛利率', 'ROE', '业务定位'],
    }
    peer_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        '# Peer Comparison Skeleton',
        '',
        f'> 主标的：{stock.get("name", "")} ({stock.get("ticker", "")})',
        '',
        '| 公司 | 市值 | PE_TTM | PB | PS | 营收增速 | 净利增速 | 毛利率 | ROE | 业务定位 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|',
        f'| {stock.get("name", "主标的")} | 待补充 | {financial.get("valuation", {}).get("pe_ttm", "待补充")} | {financial.get("valuation", {}).get("pb", "待补充")} | 待补充 | {financial.get("revenue_growth", {}).get("1y", "待补充")} | 待补充 | {financial.get("profitability", {}).get("gross_margin", "待补充")} | {financial.get("profitability", {}).get("roe", "待补充")} | 主标的 |'
    ]
    for peer in peers:
        lines.append(f'| {peer} | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |')
    lines.extend([
        '',
        '## Interpretation Handoff',
        '',
        '- 请大模型基于该表回答：主标的相对同行是贵还是便宜，溢价/折价是否合理，市场在交易什么预期。'
    ])
    out_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'peer_list_json': str(peer_path), 'peer_table_md': str(out_md), 'peer_count': len(peers)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
