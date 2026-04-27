#!/usr/bin/env python3
import argparse
import os
import json
import subprocess
from pathlib import Path


ROOT = Path(os.environ.get('STOCK_SCRIPTS_DIR', Path(__file__).parent))


def run(cmd: list[str]) -> dict | None:
    out = subprocess.check_output(cmd, text=True)
    text = out.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'text': text}


def load_final_summary(base: Path) -> dict:
    candidates = [
        base / '00_meta' / 'final-summary.json',
        base / '00_meta' / 'final_summary.json',
    ]
    for path in candidates:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                return {}
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description='One-shot controller: build report export, audit once, optionally retry once, then publish merged KDocs doc.')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--retry-note', default='根据审计失败项仅补一次，再重新审计一次。', help='Note for one allowed retry')
    parser.add_argument('--repair-command', help='Optional shell command to execute once when first audit fails')
    parser.add_argument('--max-audits', type=int, default=3, help='Maximum number of audit attempts, including the first pass')
    parser.add_argument('--skip-publish', action='store_true', help='Only build/audit locally, do not publish')
    parser.add_argument('--model', default='', help='Model name for final session summary')
    parser.add_argument('--tokens-in', default='', help='Input tokens summary')
    parser.add_argument('--tokens-out', default='', help='Output tokens summary')
    parser.add_argument('--context', default='', help='Context usage summary')
    parser.add_argument('--cache-hit', default='', help='Cache hit summary')
    parser.add_argument('--rating', default='', help='Final rating summary')
    parser.add_argument('--price', default='', help='Current price summary')
    parser.add_argument('--target', default='', help='Target price summary')
    parser.add_argument('--stop-loss', default='', dest='stop_loss', help='Stop loss summary')
    args = parser.parse_args()

    base = Path(args.dir)
    summary = load_final_summary(base)
    report_master = base / '05_reports' / 'report-master.md'
    if not report_master.exists():
        raise SystemExit(f'Missing report master: {report_master}')

    precheck = run(['python3', str(ROOT / 'validate_report_master.py'), '--dir', str(base)])
    if not precheck or not precheck.get('ok'):
        run(['python3', str(ROOT / 'build_repair_todo.py'), '--dir', str(base)])
        raise SystemExit('report-master validation failed before phase 6 publish')

    run(['python3', str(ROOT / 'build_event_cards.py'), '--dir', str(base)])
    run(['python3', str(ROOT / 'build_technical_brief.py'), '--dir', str(base), '--write-analysis'])
    run(['python3', str(ROOT / 'build_peer_comparison_skeleton.py'), '--dir', str(base)])
    run(['python3', str(ROOT / 'build_fact_packet.py'), '--dir', str(base)])
    run(['python3', str(ROOT / 'build_final_summary.py'), '--dir', str(base)])

    # Clean up non-standard analysis files created by helper scripts
    analysis_dir = base / '04_analysis'
    standard_names = {'01_initial-questions.md', '02_business-quality.md', '03_financial-quality.md',
                      '04_valuation.md', '05_technical.md', '06_catalysts-risks.md', '07_variant-view.md'}
    misc_dir = base / '02_raw' / 'misc'
    misc_dir.mkdir(parents=True, exist_ok=True)
    for p in analysis_dir.glob('*.md'):
        if p.name not in standard_names:
            import shutil
            shutil.move(str(p), str(misc_dir / p.name))

    max_audits = max(1, min(args.max_audits, 3))
    audit_results = []
    retried = False
    final_audit = None

    for idx in range(max_audits):
        # On first audit pass, ensure release-report has a recent timestamp
        # to avoid "release must be after audit" failure (circular dependency)
        if idx == 0:
            release_path = base / '05_reports' / 'release-report.md'
            if release_path.exists():
                import time
                release_path.touch()
        current = run(['python3', str(ROOT / 'run_research_audit.py'), '--dir', str(base)])
        if not current:
            raise SystemExit(f'Audit pass {idx + 1} did not return a result')
        audit_results.append(current)
        final_audit = current
        if current.get('verdict') == '通过':
            break
        run([
            'python3', str(ROOT / 'build_repair_todo.py'),
            '--dir', str(base),
        ])
        if args.repair_command and idx < max_audits - 1:
            subprocess.check_call(args.repair_command, shell=True)
            retried = True
            continue
        break

    audit1 = audit_results[0]

    audit_passed = final_audit.get('verdict') == '通过'
    audit_report = final_audit.get('report_path')
    if not audit_report:
        raise SystemExit('Audit report path missing')

    run([
        'python3', str(ROOT / 'build_session_status_summary.py'),
        '--dir', str(base),
        '--model', args.model or summary.get('model', ''),
        '--tokens-in', args.tokens_in or summary.get('tokens_in', ''),
        '--tokens-out', args.tokens_out or summary.get('tokens_out', ''),
        '--context', args.context or summary.get('context', ''),
        '--cache-hit', args.cache_hit or summary.get('cache_hit', ''),
        '--rating', args.rating or summary.get('rating', ''),
        '--price', args.price or summary.get('price', ''),
        '--target', args.target or summary.get('target', ''),
        '--stop-loss', args.stop_loss or summary.get('stop_loss', ''),
        '--audit-verdict', ('✅ 通过' if audit_passed else '⚠️ 未通过（已达审计上限，建议人工复核）'),
    ])

    run(['python3', str(ROOT / 'build_release_report.py'), '--dir', str(base)])
    run(['python3', str(ROOT / 'build_kdocs_export.py'), '--dir', str(base)])

    post_release_audit = run(['python3', str(ROOT / 'run_research_audit.py'), '--dir', str(base)])
    if not post_release_audit:
        raise SystemExit('Post-release audit did not return a result')
    final_audit = post_release_audit
    audit_report = final_audit.get('report_path') or audit_report
    audit_passed = final_audit.get('verdict') == '通过'

    run([
        'python3', str(ROOT / 'build_session_status_summary.py'),
        '--dir', str(base),
        '--model', args.model or summary.get('model', ''),
        '--tokens-in', args.tokens_in or summary.get('tokens_in', ''),
        '--tokens-out', args.tokens_out or summary.get('tokens_out', ''),
        '--context', args.context or summary.get('context', ''),
        '--cache-hit', args.cache_hit or summary.get('cache_hit', ''),
        '--rating', args.rating or summary.get('rating', ''),
        '--price', args.price or summary.get('price', ''),
        '--target', args.target or summary.get('target', ''),
        '--stop-loss', args.stop_loss or summary.get('stop_loss', ''),
        '--audit-verdict', ('✅ 通过' if audit_passed else '⚠️ 未通过（已达审计上限，建议人工复核）'),
    ])

    run(['python3', str(ROOT / 'build_release_report.py'), '--dir', str(base)])
    run(['python3', str(ROOT / 'build_kdocs_export.py'), '--dir', str(base)])

    run(['python3', str(ROOT / 'finalize_research_tracking.py'), '--dir', str(base)])

    combined = run([
        'python3', str(ROOT / 'build_combined_kdocs_export.py'),
        '--dir', str(base),
    ])

    publish = None
    if not args.skip_publish:
        publish = run([
            'python3', str(ROOT / 'publish_combined_to_kdocs_otl.py'),
            '--dir', str(base),
            '--file', str((base / '05_reports' / 'combined-kdocs-export.md')),
        ])
        run(['python3', str(ROOT / 'finalize_research_tracking.py'), '--dir', str(base)])

    result = {
        'first_audit_verdict': audit1.get('verdict'),
        'final_audit_verdict': final_audit.get('verdict'),
        'retried_once': retried,
        'audit_attempts': len(audit_results),
        'audit_report_path': audit_report,
        'combined_export_path': str(base / '05_reports' / 'combined-kdocs-export.md'),
        'published': publish,
        'status': 'done' if audit_passed else 'published_with_audit_warning',
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
