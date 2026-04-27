#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


TYPE_HINTS = [
    ('减持', '股东减持', '利空'),
    ('回购', '股份回购', '利多'),
    ('实验室', '合作进展', '利多'),
    ('合作', '合作进展', '利多'),
    ('新品', '新产品发布', '利多'),
    ('发布', '新产品发布', '利多'),
    ('年报', '财报', '中性'),
    ('季报', '财报', '中性'),
]


def detect_type(title: str, summary: str) -> tuple[str, str]:
    text = f'{title} {summary}'
    for keyword, event_type, bias in TYPE_HINTS:
        if keyword in text:
            return event_type, bias
    return '待判断', '待判断'


def main() -> int:
    parser = argparse.ArgumentParser(description='Build event cards from raw news/filings json files.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    args = parser.parse_args()

    base = Path(args.dir)
    news_dir = base / '02_raw' / 'news'
    filings_dir = base / '02_raw' / 'filings'
    out_json = base / '03_normalized' / 'event-cards.json'
    out_md = base / '04_analysis' / '06_event-cards.md'

    cards = []
    seen = set()
    for folder, bucket in [(news_dir, 'news'), (filings_dir, 'filings')]:
        if not folder.exists():
            continue
        for path in sorted(folder.glob('*.json')):
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                continue
            title = data.get('title', path.stem)
            summary = data.get('summary', '')
            dedupe_key = (data.get('date', ''), title.strip(), data.get('url', '').strip())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            event_type, bias = detect_type(title, summary)
            cards.append({
                'date': data.get('date', ''),
                'title': title,
                'type': event_type,
                'bucket': bucket,
                'source': data.get('source', ''),
                'url': data.get('url', ''),
                'summary': summary,
                'initial_bias': bias,
                'local_file': str(path),
            })

    cards.sort(key=lambda x: (x.get('date', ''), x.get('title', '')), reverse=True)

    out_json.write_text(json.dumps({'events': cards}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    md = ['# Event Cards', '', '> 本文件只整理事件卡片，不直接下结论，供大模型判断哪些是真催化剂、哪些是噪音。', '']
    if not cards:
        md.append('- 暂无事件卡片。')
    else:
        for i, card in enumerate(cards, 1):
            md.extend([
                f'## {i}. {card["title"]}',
                '',
                f'- 日期：{card["date"] or "待补充"}',
                f'- 类型：{card["type"]}',
                f'- 初步标签：{card["initial_bias"]}',
                f'- 来源：{card["source"] or "待补充"}',
                f'- 链接：{card["url"] or "待补充"}',
                f'- 摘要：{card["summary"] or "待补充"}',
                ''
            ])
    out_md.write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({'event_cards_json': str(out_json), 'event_cards_md': str(out_md), 'count': len(cards)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
