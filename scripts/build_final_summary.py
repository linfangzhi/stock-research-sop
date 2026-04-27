#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime
from pathlib import Path


SECTION_PATTERN = re.compile(r'^(## .+)$', re.M)
RATING_RE = re.compile(r'\*\*(?:📈\s*)?([^*\n]+?)\*\*')
NUMBER_RE = re.compile(r'(-?\d+(?:\.\d+)?)')


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def extract_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def first_section(sections: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = sections.get(name, '').strip()
        if value:
            return value
    return ''


def parse_rating(text: str) -> str:
    m = RATING_RE.search(text)
    if not m:
        return ''
    return m.group(1).strip()


def parse_first_number(text: str) -> str:
    m = NUMBER_RE.search(text)
    return m.group(1) if m else ''


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a compact final summary for phase 6 publishing.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--model', default='', help='Model name override')
    parser.add_argument('--tokens-in', default='', help='Input tokens summary override')
    parser.add_argument('--tokens-out', default='', help='Output tokens summary override')
    parser.add_argument('--context', default='', help='Context usage summary override')
    parser.add_argument('--cache-hit', default='', help='Cache hit summary override')
    parser.add_argument('--rating', default='', help='Rating override')
    parser.add_argument('--price', default='', help='Current price override')
    parser.add_argument('--target', default='', help='Target price override')
    parser.add_argument('--stop-loss', default='', dest='stop_loss', help='Stop loss override')
    args = parser.parse_args()

    base = Path(args.dir)
    out = base / '00_meta' / 'final-summary.json'

    stock = read_json(base / '00_meta' / 'stock.json')
    investment = read_json(base / '03_normalized' / 'investment-plan.json')
    market = read_json(base / '03_normalized' / 'market-snapshot.json')
    existing = read_json(out)

    report_path = base / '05_reports' / 'report-master.md'
    report_text = report_path.read_text(encoding='utf-8') if report_path.exists() else ''
    sections = extract_sections(report_text) if report_text else {}
    summary_text = first_section(sections, ['## 2. 一句话结论', '## 一句话结论'])
    plan_text = first_section(sections, ['## 10. 投资建议与交易计划', '## 投资建议与交易计划'])

    target_value = args.target or ''
    if not target_value:
        low = investment.get('target_price_low')
        mid = investment.get('target_price_mid')
        high = investment.get('target_price_high')
        if mid and high:
            target_value = f'{mid}元 / {high}元'
        elif low and high:
            target_value = f'{low}-{high}元'
        elif mid:
            target_value = f'{mid}元'
        elif high:
            target_value = f'{high}元'
    if not target_value:
        target_value = existing.get('target', '')

    stop_loss = args.stop_loss or ''
    if not stop_loss:
        stop_loss = investment.get('stop_loss') or investment.get('hard_stop_loss') or market.get('stop_loss_line') or ''
        if stop_loss != '':
            stop_loss = f'{stop_loss}元'
    if not stop_loss:
        stop_loss = existing.get('stop_loss', '')

    price = args.price or ''
    if not price:
        p = market.get('price', '')
        if p != '':
            date = market.get('date', '')
            price = f'{p}元' + (f' ({date})' if date else '')
    if not price:
        price = existing.get('price', '')

    rating = args.rating or investment.get('rating', '') or ''
    if not rating:
        rating = parse_rating(summary_text)

    if not rating:
        rating = parse_first_number(plan_text)
    if not rating:
        rating = existing.get('rating', '')

    result = {
        'ticker': stock.get('ticker', ''),
        'name': stock.get('name', ''),
        'model': args.model or existing.get('model', ''),
        'tokens_in': args.tokens_in or existing.get('tokens_in', ''),
        'tokens_out': args.tokens_out or existing.get('tokens_out', ''),
        'context': args.context or existing.get('context', ''),
        'cache_hit': args.cache_hit or existing.get('cache_hit', ''),
        'rating': rating or '',
        'price': price or '',
        'target': target_value or '',
        'stop_loss': stop_loss or '',
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'source': 'build_final_summary.py'
    }

    write_json(out, result)
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
