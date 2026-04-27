#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Append a single source item with low tool-call pressure.')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--source-type', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--url', default='')
    parser.add_argument('--reliability', default='中')
    parser.add_argument('--used-for', required=True)
    parser.add_argument('--bucket', choices=['official', 'filings', 'financial', 'industry', 'news'], default='news')
    args = parser.parse_args()

    base = Path(args.dir)
    source_log = base / '01_sources' / 'source-log.md'
    links = base / '01_sources' / 'links.md'
    date = datetime.now().strftime('%Y-%m-%d')
    row = f'| {date} | {args.source_type} | {args.source} | {args.url} | {args.reliability} | {args.used_for} |\n'

    if source_log.exists():
        source_log.write_text(source_log.read_text(encoding='utf-8') + row, encoding='utf-8')

    bucket_map = {
        'official': 'Official investor relations',
        'filings': 'Exchange filings',
        'financial': 'Financial data source',
        'industry': 'Industry source',
        'news': 'News / article sources',
    }
    if links.exists() and args.url:
        text = links.read_text(encoding='utf-8')
        label = bucket_map[args.bucket]
        text += f'- {label}: {args.source} - {args.url}\n'
        links.write_text(text, encoding='utf-8')

    print(source_log)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
