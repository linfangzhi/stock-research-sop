#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', value)
    value = re.sub(r'-+', '-', value).strip('-')
    return value or 'item'


def main() -> int:
    parser = argparse.ArgumentParser(description='Save raw research artifacts locally before analysis.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--kind', required=True, choices=['news', 'filings', 'misc'], help='Raw bucket under 02_raw')
    parser.add_argument('--title', required=True, help='Short title for filename and record')
    parser.add_argument('--source', required=True, help='Source name')
    parser.add_argument('--url', default='', help='Optional source URL')
    parser.add_argument('--summary', default='', help='Optional short summary')
    parser.add_argument('--content-file', help='Path to text/markdown file to import')
    parser.add_argument('--content', help='Inline content to save')
    parser.add_argument('--format', default='md', choices=['md', 'txt', 'json'], help='Output format')
    args = parser.parse_args()

    if not args.content_file and not args.content:
        raise SystemExit('Provide --content-file or --content')

    base = Path(args.dir)
    raw_dir = base / '02_raw' / args.kind
    raw_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    ext = args.format
    filename = f'{ts}-{slugify(args.title)}.{ext}'
    path = raw_dir / filename

    body = Path(args.content_file).read_text(encoding='utf-8') if args.content_file else args.content

    if ext == 'json':
        payload = {
            'title': args.title,
            'source': args.source,
            'url': args.url,
            'summary': args.summary,
            'saved_at': datetime.now().isoformat(timespec='seconds'),
            'content': body,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        text = f'# {args.title}\n\n- source: {args.source}\n- url: {args.url}\n- saved_at: {datetime.now().isoformat(timespec="seconds")}\n'
        if args.summary:
            text += f'- summary: {args.summary}\n'
        text += '\n---\n\n' + body.strip() + '\n'
        path.write_text(text, encoding='utf-8')

    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
