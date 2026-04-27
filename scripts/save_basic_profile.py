#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Save basic stock/company profile with low tool-call pressure.')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--ticker', required=True)
    parser.add_argument('--market', required=True)
    parser.add_argument('--exchange', required=True)
    parser.add_argument('--industry', default='')
    parser.add_argument('--business', default='')
    parser.add_argument('--segment', action='append', default=[])
    parser.add_argument('--geography', action='append', default=[])
    parser.add_argument('--question', action='append', default=[])
    args = parser.parse_args()

    base = Path(args.dir)
    path = base / '03_normalized' / 'company-profile.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    data.update({
        'company_name': args.name,
        'ticker': args.ticker,
        'business_summary': args.business,
        'segments': args.segment,
        'geographies': args.geography,
        'industry': args.industry,
        'key_questions': args.question,
    })
    data.setdefault('management', [])
    data.setdefault('moat_hypothesis', [])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
