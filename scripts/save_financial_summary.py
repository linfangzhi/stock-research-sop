#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Save financial summary to raw + normalized files.')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--period', required=True)
    parser.add_argument('--revenue-growth-1y', type=float, dest='rev1y')
    parser.add_argument('--net-margin', type=float)
    parser.add_argument('--gross-margin', type=float)
    parser.add_argument('--roe', type=float)
    parser.add_argument('--roic', type=float)
    parser.add_argument('--operating-cf', type=float, dest='opcf')
    parser.add_argument('--free-cf', type=float, dest='fcf')
    parser.add_argument('--debt-ratio', type=float, dest='debt_ratio')
    parser.add_argument('--current-ratio', type=float, dest='current_ratio')
    parser.add_argument('--pe-ttm', type=float, dest='pe_ttm')
    parser.add_argument('--pb', type=float)
    parser.add_argument('--dividend-yield', type=float, dest='dividend_yield')
    args = parser.parse_args()

    base = Path(args.dir)
    raw_dir = base / '02_raw' / 'financials'
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f'financial-summary-{args.period}.json'
    normalized_path = base / '03_normalized' / 'financial-summary.json'

    payload = {
        'period': args.period,
        'revenue_growth_1y': args.rev1y,
        'gross_margin': args.gross_margin,
        'net_margin': args.net_margin,
        'roe': args.roe,
        'roic': args.roic,
        'operating_cashflow': args.opcf,
        'free_cashflow': args.fcf,
        'debt_ratio': args.debt_ratio,
        'current_ratio': args.current_ratio,
        'pe_ttm': args.pe_ttm,
        'pb': args.pb,
        'dividend_yield': args.dividend_yield,
        'saved_at': datetime.now().isoformat(timespec='seconds')
    }
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    normalized = json.loads(normalized_path.read_text(encoding='utf-8')) if normalized_path.exists() else {}
    normalized.setdefault('revenue_growth', {})['1y'] = args.rev1y
    normalized.setdefault('profitability', {})['gross_margin'] = args.gross_margin
    normalized['profitability']['net_margin'] = args.net_margin
    normalized['profitability']['roe'] = args.roe
    normalized['profitability']['roic'] = args.roic
    normalized.setdefault('cash_flow', {})['operating_cashflow'] = args.opcf
    normalized['cash_flow']['free_cashflow'] = args.fcf
    normalized.setdefault('balance_sheet', {})['debt_ratio'] = args.debt_ratio
    normalized['balance_sheet']['current_ratio'] = args.current_ratio
    normalized.setdefault('valuation', {})['pe_ttm'] = args.pe_ttm
    normalized['valuation']['pb'] = args.pb
    normalized['valuation']['dividend_yield'] = args.dividend_yield
    normalized_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'raw': str(raw_path), 'normalized': str(normalized_path)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
