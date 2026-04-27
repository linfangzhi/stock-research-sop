#!/usr/bin/env python3
import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path


EMPTY_JSON_THRESHOLD = 40


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def file_has_substance(path: Path) -> bool:
    if not path.exists():
        return False
    text = read_text(path).strip()
    if not text:
        return False
    if '待补充' in text and len(text) < 400:
        return False
    return True


def json_has_data(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(read_text(path))
    s = json.dumps(data, ensure_ascii=False)
    for marker in ['null', '""', '[]', '{}']:
        s = s.replace(marker, '')
    return len(s.strip()) > EMPTY_JSON_THRESHOLD


def count_raw_files(base: Path, bucket: str) -> int:
    d = base / '02_raw' / bucket
    return len([p for p in d.glob('*') if p.is_file()]) if d.exists() else 0


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ''


def content_similarity(a: Path, b: Path) -> float:
    if not a.exists() or not b.exists():
        return 0.0
    ta = ' '.join(read_text(a).split())
    tb = ' '.join(read_text(b).split())
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    sa = set(ta.split())
    sb = set(tb.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa | sb), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description='Audit a stock research workspace against auditability rules.')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--output', help='Optional output markdown path')
    args = parser.parse_args()

    base = Path(args.dir)
    stock = json.loads(read_text(base / '00_meta' / 'stock.json'))
    coverage = json.loads(read_text(base / '00_meta' / 'coverage.json')) if (base / '00_meta' / 'coverage.json').exists() else {}
    ticker = stock.get('ticker', '')
    market = stock.get('market', '')
    root = base.parent
    duplicates = [p.name for p in root.glob(f'{market}-*-{ticker}-*') if p.is_dir() and p.resolve() != base.resolve()]
    analysis_dir = base / '04_analysis'
    standard_analysis = {
        '01_initial-questions.md',
        '02_business-quality.md',
        '03_financial-quality.md',
        '04_valuation.md',
        '05_technical.md',
        '06_catalysts-risks.md',
        '07_variant-view.md',
    }
    existing_analysis = {p.name for p in analysis_dir.glob('*.md')} if analysis_dir.exists() else set()
    nonstandard_analysis = sorted(existing_analysis - standard_analysis)

    checks = []

    def add(section: str, item: str, passed: bool, evidence: str):
        checks.append({'section': section, 'item': item, 'passed': passed, 'evidence': evidence})

    add('目录', '同一标的只有一个主目录', len(duplicates) == 0, 'duplicates=' + (', '.join(duplicates) if duplicates else 'none'))
    add('来源', 'source-log 非空', file_has_substance(base / '01_sources' / 'source-log.md') and read_text(base / '01_sources' / 'source-log.md').count('\n| ') > 1, 'source-log rows=' + str(read_text(base / '01_sources' / 'source-log.md').count('\n| ')))
    add('来源', 'links 非占位', file_has_substance(base / '01_sources' / 'links.md') and 'https://' in read_text(base / '01_sources' / 'links.md'), 'links_has_url=' + str('https://' in read_text(base / '01_sources' / 'links.md')))
    add('原始数据', 'market-data 已落盘', count_raw_files(base, 'market-data') > 0, f'market-data files={count_raw_files(base, "market-data")}')
    add('原始数据', 'financials 已落盘', count_raw_files(base, 'financials') > 0, f'financials files={count_raw_files(base, "financials")}')
    add('原始数据', 'news/filings 至少一类已落盘', count_raw_files(base, 'news') > 0 or count_raw_files(base, 'filings') > 0, f'news={count_raw_files(base, "news")}, filings={count_raw_files(base, "filings")}')
    add('结构化数据', 'company-profile 非空', json_has_data(base / '03_normalized' / 'company-profile.json'), 'company-profile=' + str(json_has_data(base / '03_normalized' / 'company-profile.json')))
    add('结构化数据', 'market-snapshot 非空', json_has_data(base / '03_normalized' / 'market-snapshot.json'), 'market-snapshot=' + str(json_has_data(base / '03_normalized' / 'market-snapshot.json')))
    add('结构化数据', 'financial-summary 非空', json_has_data(base / '03_normalized' / 'financial-summary.json'), 'financial-summary=' + str(json_has_data(base / '03_normalized' / 'financial-summary.json')))
    add('结构化数据', 'investment-plan 非空', json_has_data(base / '03_normalized' / 'investment-plan.json'), 'investment-plan=' + str(json_has_data(base / '03_normalized' / 'investment-plan.json')))
    add('分析', '核心分析文件非空', all(file_has_substance(base / '04_analysis' / name) for name in ['02_business-quality.md', '03_financial-quality.md', '04_valuation.md', '05_technical.md']), 'core-analysis=' + str(all(file_has_substance(base / '04_analysis' / name) for name in ['02_business-quality.md', '03_financial-quality.md', '04_valuation.md', '05_technical.md'])))
    add('分析', '标准分析槽位完整', all(file_has_substance(base / '04_analysis' / name) for name in ['02_business-quality.md', '03_financial-quality.md', '04_valuation.md', '05_technical.md', '06_catalysts-risks.md', '07_variant-view.md']), 'analysis_slots=' + str({name: file_has_substance(base / '04_analysis' / name) for name in ['02_business-quality.md', '03_financial-quality.md', '04_valuation.md', '05_technical.md', '06_catalysts-risks.md', '07_variant-view.md']}))
    add('分析', '不存在非标准分析文件名', len(nonstandard_analysis) == 0, 'nonstandard=' + (', '.join(nonstandard_analysis) if nonstandard_analysis else 'none'))
    dup_similarity = content_similarity(base / '04_analysis' / '02_business-quality.md', base / '04_analysis' / '03_financial-quality.md')
    add('分析', '业务分析与财务分析不应高度重复', dup_similarity < 0.8, f'similarity={dup_similarity:.2f}')
    add('报告', 'report-master 非模板', file_has_substance(base / '05_reports' / 'report-master.md'), 'report-master=' + str(file_has_substance(base / '05_reports' / 'report-master.md')))
    add('报告', 'release-report 非模板', file_has_substance(base / '05_reports' / 'release-report.md'), 'release-report=' + str(file_has_substance(base / '05_reports' / 'release-report.md')))
    stock_has_kdocs = bool(stock.get('kdocs_link'))
    checklist = coverage.get('completion_checklist', {})
    add('状态', 'completion_checklist 已同步', any(bool(v) for v in checklist.values()) if checklist else False, 'checklist=' + json.dumps(checklist, ensure_ascii=False))

    audit_dir = base / '05_reports' / 'audit'
    release_path = base / '05_reports' / 'release-report.md'
    latest_audit = sorted(audit_dir.glob('audit-report-*.md'))[-1] if audit_dir.exists() and list(audit_dir.glob('audit-report-*.md')) else None
    add('发布', '最终报告必须晚于审计生成', bool(latest_audit and release_path.exists() and release_path.stat().st_mtime >= latest_audit.stat().st_mtime), f'release_mtime={release_path.stat().st_mtime if release_path.exists() else 0}, latest_audit_mtime={latest_audit.stat().st_mtime if latest_audit else 0}')

    failed = [c for c in checks if not c['passed']]
    verdict = '通过' if not failed else '不通过'

    lines = []
    lines.append(f'# 股票研究自审计报告\n')
    lines.append(f'- 标的：{stock.get("name", "")} ({ticker})')
    lines.append(f'- 审计时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'- 审计结论：**{verdict}**')
    lines.append(f'- 未通过项数量：{len(failed)}\n')
    lines.append('## 审计明细\n')
    lines.append('| 分类 | 检查项 | 结果 | 证据 |')
    lines.append('|---|---|---|---|')
    for c in checks:
        lines.append(f"| {c['section']} | {c['item']} | {'✅ PASS' if c['passed'] else '❌ FAIL'} | {c['evidence']} |")
    lines.append('\n## 未通过项\n')
    if failed:
        for i, c in enumerate(failed, 1):
            lines.append(f'{i}. [{c["section"]}] {c["item"]}，证据：{c["evidence"]}')
    else:
        lines.append('- 无')
    lines.append('\n## 建议动作\n')
    if failed:
        lines.append('- 仅允许回补一次未通过项，然后重新执行一次自审计')
        lines.append('- 若第二次仍未通过，不再自动重试，直接标记为需人工处理')
    else:
        lines.append('- 可以进入最终发布流程')

    audit_dir = base / '05_reports' / 'audit'
    audit_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else audit_dir / f'audit-report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.md'
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    result = {
        'verdict': verdict,
        'failed_count': len(failed),
        'failed_items': failed,
        'report_path': str(output),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
