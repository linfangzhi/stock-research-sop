#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


PLACEHOLDER_MARKERS = ['待补充', '待填写', 'TBD']


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


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a reader-friendly KDocs export from report-master.md')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    args = parser.parse_args()

    base = Path(args.dir)
    master = base / '05_reports' / 'release-report.md'
    export = base / '05_reports' / 'kdocs-export.md'
    if not master.exists():
        raise SystemExit(f'Missing release report: {master}')

    text = master.read_text(encoding='utf-8')
    if sum(1 for marker in PLACEHOLDER_MARKERS if marker in text) > 8:
        raise SystemExit('report-master.md still looks like a template, refuse to build kdocs export')
    sections = extract_sections(text)

    if '## 研究结论' in text or '## 📌 摘要' in text:
        export.write_text(text if text.endswith('\n') else text + '\n', encoding='utf-8')
        print(export)
        return 0

    def get(name: str) -> str:
        return sections.get(name, '').strip()

    summary_bits = [x for x in [get('## 2. 一句话结论'), get('## 3. 核心逻辑')] if x]
    fundamentals = [x for x in [get('## 4. 业务与竞争格局'), get('## 5. 基本面分析'), get('## 6. 估值分析')] if x]
    technicals = [x for x in [get('## 7. 技术分析')] if x]
    advice = [x for x in [get('## 10. 投资建议与交易计划')] if x]
    risks = [x for x in [get('## 8. 催化剂与风险'), get('## 9. 情景分析')] if x]
    refs = [x for x in [get('## 11. 参考资料与来源')] if x]

    output = [
        '# 金山文档导出版',
        '',
        '> 面向阅读和分享，保留结论、推理、关键数据、交易计划与参考资料。',
        '',
        '## 摘要',
        '',
        '\n\n'.join(summary_bits) if summary_bits else '待补充',
        '',
        '## 研究结论',
        '',
        get('## 1. 标的概览') or '待补充',
        '',
        '## 核心逻辑',
        '',
        get('## 3. 核心逻辑') or '待补充',
        '',
        '## 基本面分析',
        '',
        '\n\n'.join(fundamentals) if fundamentals else '待补充',
        '',
        '## 技术分析',
        '',
        '\n\n'.join(technicals) if technicals else '待补充',
        '',
        '## 投资建议',
        '',
        '\n\n'.join(advice) if advice else '待补充',
        '',
        '## 风险与反证',
        '',
        '\n\n'.join(risks) if risks else '待补充',
        '',
        '## 参考资料',
        '',
        '\n\n'.join(refs) if refs else '待补充',
        ''
    ]

    substantive = '\n'.join(output)
    if substantive.count('待补充') >= 4:
        raise SystemExit('kdocs export would still be mostly placeholder content, aborting')

    export.write_text('\n'.join(output), encoding='utf-8')
    print(export)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
