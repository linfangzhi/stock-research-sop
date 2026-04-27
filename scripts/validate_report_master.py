#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


SECTION_PATTERN = re.compile(r'^(## .+)$', re.M)
PLACEHOLDERS = ['待补充', '待填写', 'TBD']

REQUIRED_SECTIONS = {
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


def extract_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def get_first(sections: dict[str, str], names: list[str]) -> tuple[str, str]:
    for name in names:
        value = sections.get(name, '').strip()
        if value:
            return name, value
    return '', ''


def has_substance(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if any(marker in text for marker in PLACEHOLDERS) and len(text) < 240:
        return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    real_lines = [line for line in lines if line.lstrip('- ').strip() and line.lstrip('- ').strip() not in PLACEHOLDERS]
    if len(real_lines) >= 2:
        return True
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate report-master structure before phase 6 publish.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    parser.add_argument('--output-json', help='Optional output json path')
    args = parser.parse_args()

    base = Path(args.dir)
    report = base / '05_reports' / 'report-master.md'
    if not report.exists():
        raise SystemExit(f'Missing report master: {report}')

    text = report.read_text(encoding='utf-8')
    sections = extract_sections(text)

    checks = []
    failed = []

    for key, aliases in REQUIRED_SECTIONS.items():
        title, body = get_first(sections, aliases)
        passed = bool(title) and has_substance(body)
        evidence = title or 'missing'
        checks.append({
            'key': key,
            'passed': passed,
            'evidence': evidence,
        })
        if not passed:
            failed.append({
                'key': key,
                'reason': 'missing_or_placeholder',
                'expected_titles': aliases,
                'evidence': evidence,
            })

    extra_rules = {
        'has_take_profit': '止盈' in text,
        'has_stop_loss': '止损' in text,
        'has_rating': '评级' in text or '增持' in text or '买入' in text or '卖出' in text or '中性' in text,
        'has_support_resistance': ('支撑' in text and '压力' in text) or ('support' in text.lower() and 'resistance' in text.lower()),
    }
    for key, passed in extra_rules.items():
        checks.append({'key': key, 'passed': passed, 'evidence': 'keyword_scan'})
        if not passed:
            failed.append({'key': key, 'reason': 'keyword_missing', 'evidence': 'keyword_scan'})

    placeholder_count = sum(text.count(marker) for marker in PLACEHOLDERS)
    checks.append({'key': 'placeholder_count_ok', 'passed': placeholder_count <= 6, 'evidence': f'placeholders={placeholder_count}'})
    if placeholder_count > 6:
        failed.append({'key': 'placeholder_count_ok', 'reason': 'too_many_placeholders', 'evidence': f'placeholders={placeholder_count}'})

    result = {
        'ok': len(failed) == 0,
        'failed_count': len(failed),
        'failed_items': failed,
        'checks': checks,
        'report_path': str(report),
    }

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
