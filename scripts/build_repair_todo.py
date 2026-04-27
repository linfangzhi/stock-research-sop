#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def read_json_output(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def latest_audit_report(base: Path) -> Path | None:
    audit_dir = base / '05_reports' / 'audit'
    candidates = sorted(audit_dir.glob('audit-report-*.md')) if audit_dir.exists() else []
    return candidates[-1] if candidates else None


def map_suggestion(item: dict) -> str:
    section = item.get('section', '')
    check = item.get('item', '')
    if section == '来源':
        return '补充 source-log / links，并确认原始来源已落盘到 02_raw。'
    if section == '原始数据':
        return '补齐对应 raw 数据文件，确保 market-data / financials / news / filings 至少一类存在。'
    if section == '结构化数据':
        return '回填 03_normalized 下对应 JSON，确保不是空壳。'
    if section == '分析':
        return '补齐或清理 04_analysis，保证标准槽位完整、命名规范且不重复。'
    if section == '报告':
        return '完善 report-master / release-report，去掉模板占位并补全关键章节。'
    if section == '状态':
        return '同步 coverage.json / stock.json / tracking 文件，避免元信息滞后。'
    if section == '发布':
        return '重新生成最终报告后再执行发布前时序校验，确保 release 晚于最新审计。'
    if '止损' in check or '止盈' in check:
        return '补充 investment-plan 与报告中的交易计划段落。'
    return '按失败项补齐对应文件，然后重新执行一次自审计。'


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a repair todo from audit failed items.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--audit-json', help='Optional audit json result path')
    args = parser.parse_args()

    base = Path(args.dir)
    out_md = base / '06_tracking' / 'repair-todo.md'
    out_json = base / '06_tracking' / 'repair-todo.json'

    audit_data = read_json_output(Path(args.audit_json)) if args.audit_json else {}
    if not audit_data:
        latest = latest_audit_report(base)
        if latest and latest.exists():
            audit_data = {'report_path': str(latest), 'failed_items': [], 'failed_count': 0}

    failed_items = audit_data.get('failed_items', []) or []

    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'audit_report_path': audit_data.get('report_path', ''),
        'failed_count': len(failed_items),
        'items': [],
    }

    lines = ['# Repair Todo', '']
    if not failed_items:
        lines.extend(['- 当前没有审计失败项。', '- 若仍需优化，优先做质量增强而不是补缺。'])
    else:
        for idx, item in enumerate(failed_items, 1):
            suggestion = map_suggestion(item)
            entry = {
                'id': idx,
                'section': item.get('section', ''),
                'check': item.get('item', ''),
                'evidence': item.get('evidence', ''),
                'suggestion': suggestion,
            }
            payload['items'].append(entry)
            lines.extend([
                f'## {idx}. [{entry["section"]}] {entry["check"]}',
                '',
                f'- 证据：{entry["evidence"]}',
                f'- 建议动作：{entry["suggestion"]}',
                ''
            ])
        lines.extend([
            '## 执行规则',
            '',
            '- 只按失败项回补，不做无关大改。',
            '- 回补完成后重新执行一次自审计。',
            '- 若达到审计上限，停止自动修复，改为人工接管。'
        ])

    out_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'markdown': str(out_md), 'json': str(out_json), 'failed_count': len(failed_items)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
