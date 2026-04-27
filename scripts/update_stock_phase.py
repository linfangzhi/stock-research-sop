#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def is_placeholder_text(text: str) -> bool:
    return ('待补充' in text) or ('待填写' in text)


def file_has_substance(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding='utf-8').strip()
    if not text:
        return False
    if is_placeholder_text(text) and len(text) < 400:
        return False
    return True


def json_has_data(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding='utf-8'))
    serialized = json.dumps(data, ensure_ascii=False)
    empty_markers = [
        'null', '""', '[]', '{}'
    ]
    nonempty = serialized
    for marker in empty_markers:
        nonempty = nonempty.replace(marker, '')
    return len(nonempty.strip()) > 40


def update_coverage_checklist(base: Path) -> None:
    coverage_path = base / '00_meta' / 'coverage.json'
    if not coverage_path.exists():
        return
    coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
    checklist = coverage.setdefault('completion_checklist', {})

    checklist['has_conclusion'] = file_has_substance(base / '05_reports' / 'report-master.md') and ('评级' in (base / '05_reports' / 'report-master.md').read_text(encoding='utf-8'))
    checklist['has_reasoning'] = file_has_substance(base / '04_analysis' / '02_business-quality.md') or file_has_substance(base / '04_analysis' / '03_financial-quality.md')
    checklist['has_fundamental_analysis'] = file_has_substance(base / '04_analysis' / '03_financial-quality.md')
    checklist['has_technical_analysis'] = file_has_substance(base / '04_analysis' / '05_technical.md')
    checklist['has_investment_advice'] = json_has_data(base / '03_normalized' / 'investment-plan.json')
    report_text = (base / '05_reports' / 'report-master.md').read_text(encoding='utf-8') if (base / '05_reports' / 'report-master.md').exists() else ''
    checklist['has_take_profit'] = ('止盈' in report_text) or ('take_profit_lines' in ((base / '03_normalized' / 'investment-plan.json').read_text(encoding='utf-8') if (base / '03_normalized' / 'investment-plan.json').exists() else ''))
    checklist['has_stop_loss'] = ('止损' in report_text) or ('hard_stop_loss' in ((base / '03_normalized' / 'investment-plan.json').read_text(encoding='utf-8') if (base / '03_normalized' / 'investment-plan.json').exists() else ''))
    checklist['has_sources'] = file_has_substance(base / '01_sources' / 'source-log.md') and ('| ' in (base / '01_sources' / 'source-log.md').read_text(encoding='utf-8')) and (base / '01_sources' / 'source-log.md').read_text(encoding='utf-8').count('\n| ') > 1
    stock_path = base / '00_meta' / 'stock.json'
    stock = json.loads(stock_path.read_text(encoding='utf-8')) if stock_path.exists() else {}
    checklist['has_kdocs_link'] = bool(stock.get('kdocs_link'))

    done_count = sum(1 for v in checklist.values() if v)
    total_count = max(len(checklist), 1)
    coverage['confidence'] = 'high' if done_count >= total_count - 1 else 'medium' if done_count >= total_count // 2 else 'low'
    coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_phase_completion(base: Path, phase: str) -> None:
    if phase == '3':
        needed = [
            base / '03_normalized' / 'company-profile.json',
            base / '03_normalized' / 'market-snapshot.json',
            base / '03_normalized' / 'financial-summary.json',
        ]
        if not all(json_has_data(p) for p in needed):
            raise SystemExit('Phase 3 cannot be completed: normalized data is still incomplete')
    if phase == '5':
        if not file_has_substance(base / '05_reports' / 'report-master.md'):
            raise SystemExit('Phase 5 cannot be completed: report-master.md is still placeholder/empty')
        if not json_has_data(base / '03_normalized' / 'investment-plan.json'):
            raise SystemExit('Phase 5 cannot be completed: investment-plan.json is incomplete')
        if not file_has_substance(base / '01_sources' / 'source-log.md'):
            raise SystemExit('Phase 5 cannot be completed: source-log.md is empty')
    if phase == '6':
        if not file_has_substance(base / '05_reports' / 'kdocs-export.md'):
            raise SystemExit('Phase 6 cannot be completed: kdocs-export.md is empty or placeholder')
        if not file_has_substance(base / '05_reports' / 'combined-kdocs-export.md'):
            raise SystemExit('Phase 6 cannot be completed: combined-kdocs-export.md is missing or placeholder')
        audit_dir = base / '05_reports' / 'audit'
        audit_reports = list(audit_dir.glob('audit-report-*.md')) if audit_dir.exists() else []
        if not audit_reports:
            raise SystemExit('Phase 6 cannot be completed: audit report has not been generated')
        stock_path = base / '00_meta' / 'stock.json'
        stock = json.loads(stock_path.read_text(encoding='utf-8')) if stock_path.exists() else {}
        if not stock.get('combined_kdocs_link'):
            raise SystemExit('Phase 6 cannot be completed: combined report has not been published to KDocs')


def main() -> int:
    parser = argparse.ArgumentParser(description='Update stock research phase status and append a progress log entry.')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--phase', required=True, help='Phase id, e.g. 1, 2A, 2B, 3')
    parser.add_argument('--status', required=True, choices=['pending', 'in_progress', 'completed', 'blocked'])
    parser.add_argument('--note', default='', help='Short progress note')
    args = parser.parse_args()

    base = Path(args.dir)
    phases_path = base / '00_meta' / 'phases.json'
    log_path = base / '06_tracking' / 'progress-log.md'
    if not phases_path.exists():
        raise SystemExit(f'Missing phases file: {phases_path}')

    phases = json.loads(phases_path.read_text(encoding='utf-8'))
    found = None
    order = [str(p.get('id')) for p in phases.get('phases', [])]
    for item in phases.get('phases', []):
        if str(item.get('id')) == str(args.phase):
            item['status'] = args.status
            found = item
    if found is None:
        raise SystemExit(f'Phase not found: {args.phase}')

    if args.status == 'completed':
        validate_phase_completion(base, str(args.phase))

    if args.status == 'completed':
        try:
            idx = order.index(str(args.phase))
            phases['current_phase'] = order[idx + 1] if idx + 1 < len(order) else str(args.phase)
        except ValueError:
            phases['current_phase'] = str(args.phase)
    else:
        phases['current_phase'] = str(args.phase)

    phases_path.write_text(json.dumps(phases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    title = found.get('name', f'阶段 {args.phase}')
    line = f'- {timestamp} | 阶段 {args.phase} {title} | {args.status} | {args.note or "无备注"}\n'

    if log_path.exists():
        old = log_path.read_text(encoding='utf-8')
        if old.rstrip().endswith('待开始'):
            old = old.replace('- 待开始\n', '')
        log_path.write_text(old + line, encoding='utf-8')
    else:
        log_path.write_text('# Progress Log\n\n## 阶段推进记录\n\n' + line, encoding='utf-8')

    update_coverage_checklist(base)

    print(json.dumps({'phase': str(args.phase), 'status': args.status, 'note': args.note}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
