#!/usr/bin/env python3
import argparse
from pathlib import Path


def pick_latest_audit(base: Path) -> Path:
    audit_dir = base / '05_reports' / 'audit'
    candidates = sorted(audit_dir.glob('audit-report-*.md')) if audit_dir.exists() else []
    if not candidates:
        raise SystemExit('No audit reports found under 05_reports/audit')
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a merged KDocs markdown with report first and audit second.')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--audit-report', help='Optional path to audit markdown report; defaults to latest audit report')
    args = parser.parse_args()

    base = Path(args.dir)
    report_path = base / '05_reports' / 'kdocs-export.md'
    audit_path = Path(args.audit_report) if args.audit_report else pick_latest_audit(base)
    status_path = base / '05_reports' / 'session-status-summary.md'
    combined_path = base / '05_reports' / 'combined-kdocs-export.md'

    if not report_path.exists():
        raise SystemExit(f'Missing report export: {report_path}')
    if not audit_path.exists():
        raise SystemExit(f'Missing audit report: {audit_path}')

    report_text = report_path.read_text(encoding='utf-8').strip()
    audit_text = audit_path.read_text(encoding='utf-8').strip()
    status_text = status_path.read_text(encoding='utf-8').strip() if status_path.exists() else ''

    if not report_text or report_text.count('待补充') >= 4:
        raise SystemExit('Report export is still placeholder-like, refusing to build combined export')

    combined = []
    combined.append(report_text)
    combined.append('\n\n---\n\n')
    combined.append('# 研究自审计报告\n\n')
    combined.append('> 以下内容为本次股票研究在最终发布前执行的一次性自审计结果。\n\n')
    combined.append(audit_text)
    if status_text:
        combined.append('\n\n---\n\n')
        combined.append(status_text)
    combined_path.write_text(''.join(combined).strip() + '\n', encoding='utf-8')
    print(combined_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
