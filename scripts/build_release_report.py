#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


def extract_sections(text: str):
    pattern = re.compile(r'^(## .+)$', re.M)
    matches = list(pattern.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[title] = body
    return sections


SECTION_ALIASES = {
    'summary': ['## 2. 一句话结论', '## 一句话结论'],
    'logic': ['## 3. 核心逻辑', '## 核心逻辑'],
    'business': ['## 4. 业务与竞争格局', '## 业务与竞争格局'],
    'financial': ['## 5. 基本面分析', '## 基本面分析'],
    'valuation': ['## 6. 估值分析', '## 估值分析'],
    'technical': ['## 7. 技术分析', '## 技术分析'],
    'risk': ['## 8. 催化剂与风险', '## 催化剂与风险'],
    'variant': ['## 9. 情景分析', '## 情景分析', '## 反证与情景分析'],
    'plan': ['## 10. 投资建议与交易计划', '## 投资建议与交易计划'],
    'refs': ['## 11. 参考资料与来源', '## 参考资料与来源', '## 参考资料'],
    'next': ['## 12. 待补问题与下一步', '## 待补问题与下一步'],
}


def get_first(sections: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = sections.get(name, '').strip()
        if value:
            return value
    return ''


def main() -> int:
    parser = argparse.ArgumentParser(description='Build final release report only after audit passes.')
    parser.add_argument('--dir', required=True)
    args = parser.parse_args()

    base = Path(args.dir)
    master = base / '05_reports' / 'report-master.md'
    release = base / '05_reports' / 'release-report.md'
    audit_dir = base / '05_reports' / 'audit'
    status_summary = base / '05_reports' / 'session-status-summary.md'
    if not master.exists():
        raise SystemExit(f'Missing report master: {master}')

    audit_reports = sorted(audit_dir.glob('audit-report-*.md')) if audit_dir.exists() else []
    latest_audit = audit_reports[-1] if audit_reports else None
    audit_text = latest_audit.read_text(encoding='utf-8') if latest_audit else ''
    audit_passed = '审计结论：**通过**' in audit_text

    text = master.read_text(encoding='utf-8')
    sections = extract_sections(text)
    output = [
        '# 📈 股票分析最终报告',
        '',
        '> 本文档为最终交付版。默认在研究资产审计通过后生成，如达到审计上限仍未通过，会明确标记并建议人工复核。',
        '',
        f'> 审计状态：{"✅ 已通过" if audit_passed else "⚠️ 未通过，建议人工复核"}',
        '',
        '## 📌 摘要',
        '',
        get_first(sections, SECTION_ALIASES['summary']) or '待补充',
        '',
        '## 🧠 核心逻辑',
        '',
        get_first(sections, SECTION_ALIASES['logic']) or '待补充',
        '',
        '## 🏭 业务与竞争格局',
        '',
        get_first(sections, SECTION_ALIASES['business']) or '待补充',
        '',
        '## 📊 基本面分析',
        '',
        get_first(sections, SECTION_ALIASES['financial']) or '待补充',
        '',
        '## 💹 估值分析',
        '',
        get_first(sections, SECTION_ALIASES['valuation']) or '待补充',
        '',
        '## 📉 技术分析',
        '',
        get_first(sections, SECTION_ALIASES['technical']) or '待补充',
        '',
        '## ⚠️ 催化剂、风险与情景',
        '',
        '\n\n'.join([x for x in [get_first(sections, SECTION_ALIASES['risk']), get_first(sections, SECTION_ALIASES['variant'])] if x]) or '待补充',
        '',
        '## ✅ 投资建议与交易计划',
        '',
        get_first(sections, SECTION_ALIASES['plan']) or '待补充',
        '',
        '## 📚 参考资料',
        '',
        get_first(sections, SECTION_ALIASES['refs']) or '待补充',
        '',
        '## 📝 待补问题与下一步',
        '',
        get_first(sections, SECTION_ALIASES['next']) or '待补充',
        ''
    ]

    if status_summary.exists():
        output.extend([
            '---',
            '',
            status_summary.read_text(encoding='utf-8').strip(),
            ''
        ])

    content = '\n'.join(output)
    if content.count('待补充') >= 3:
        raise SystemExit('release report still looks incomplete, aborting')
    release.write_text(content, encoding='utf-8')
    print(release)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
