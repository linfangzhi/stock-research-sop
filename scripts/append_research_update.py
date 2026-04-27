#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def append_section(path: Path, heading: str, lines: list[str]) -> None:
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    block = heading + '\n' + '\n'.join(lines).rstrip() + '\n\n'
    path.write_text(existing.rstrip() + '\n\n' + block, encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Append a dated research update to an existing stock workspace.')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--facts', action='append', default=[], help='New fact, repeatable')
    parser.add_argument('--views', action='append', default=[], help='New judgment, repeatable')
    parser.add_argument('--reversed', action='append', default=[], help='Overturned old judgment, repeatable')
    parser.add_argument('--next', dest='next_steps', action='append', default=[], help='Next step, repeatable')
    args = parser.parse_args()

    base = Path(args.dir)
    if not base.exists():
        raise SystemExit(f'Not found: {base}')

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    update_log = base / '06_tracking' / 'update-log.md'
    heading = f'## {now}'
    lines = []

    if args.facts:
        lines.append('- 新增事实：')
        lines.extend([f'  - {x}' for x in args.facts])
    if args.views:
        lines.append('- 新增判断：')
        lines.extend([f'  - {x}' for x in args.views])
    if args.reversed:
        lines.append('- 被推翻的旧判断：')
        lines.extend([f'  - {x}' for x in args.reversed])
    if args.next_steps:
        lines.append('- 下次要补的内容：')
        lines.extend([f'  - {x}' for x in args.next_steps])
    if not lines:
        lines = ['- 本次未提供具体更新内容。']

    append_section(update_log, heading, lines)

    meta_path = base / '00_meta' / 'stock.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        meta['last_updated_at'] = datetime.now().isoformat(timespec='seconds')
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(update_log)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
