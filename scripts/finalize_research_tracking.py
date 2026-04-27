#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


SECTION_PATTERN = re.compile(r'^(## .+)$', re.M)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def extract_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def has_substance(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    bad_markers = ['待补充', '待填写', 'TBD']
    return not (any(m in text for m in bad_markers) and len(text) < 200)


def clean_line(line: str) -> str:
    line = line.strip()
    line = line.lstrip('- ').strip()
    if not line:
        return ''
    noisy_prefixes = ('*报告生成时间', '*下次更新', '#', '>', '|')
    if line.startswith(noisy_prefixes):
        return ''
    if '审计状态' in line or '模型状态与用量摘要' in line:
        return ''
    return line


def main() -> int:
    parser = argparse.ArgumentParser(description='Finalize coverage and next steps after stock report publishing.')
    parser.add_argument('--dir', required=True, help='Stock workspace dir')
    args = parser.parse_args()

    base = Path(args.dir)
    coverage_path = base / '00_meta' / 'coverage.json'
    stock_path = base / '00_meta' / 'stock.json'
    release_path = base / '05_reports' / 'release-report.md'
    next_steps_path = base / '06_tracking' / 'next-steps.md'
    investment_path = base / '03_normalized' / 'investment-plan.json'

    coverage = read_json(coverage_path)
    stock = read_json(stock_path)
    investment = read_json(investment_path)
    release_text = read_text(release_path)
    sections = extract_sections(release_text) if release_text else {}

    summary = sections.get('## 📌 摘要', '') or sections.get('## 摘要', '')
    logic = sections.get('## 🧠 核心逻辑', '') or sections.get('## 核心逻辑', '')
    financial = sections.get('## 📊 基本面分析', '') or sections.get('## 基本面分析', '')
    technical = sections.get('## 📉 技术分析', '') or sections.get('## 技术分析', '')
    plan = sections.get('## ✅ 投资建议与交易计划', '') or sections.get('## 投资建议与交易计划', '')
    refs = sections.get('## 📚 参考资料', '') or sections.get('## 参考资料', '')
    next_sec = sections.get('## 📝 待补问题与下一步', '') or sections.get('## 待补问题与下一步', '')

    checklist = coverage.get('completion_checklist', {})
    checklist['has_conclusion'] = has_substance(summary)
    checklist['has_reasoning'] = has_substance(logic)
    checklist['has_fundamental_analysis'] = has_substance(financial)
    checklist['has_technical_analysis'] = has_substance(technical)
    checklist['has_investment_advice'] = has_substance(plan)
    checklist['has_take_profit'] = '止盈' in plan or '止盈' in release_text
    checklist['has_stop_loss'] = '止损' in plan or '止损' in release_text
    checklist['has_sources'] = has_substance(refs)
    checklist['has_kdocs_link'] = bool(stock.get('kdocs_link') or stock.get('combined_kdocs_link'))
    coverage['completion_checklist'] = checklist
    coverage['confidence'] = 'high' if checklist.get('has_conclusion') and checklist.get('has_sources') else coverage.get('confidence', 'normal')
    write_json(coverage_path, coverage)

    lines = ['# Next Steps', '']

    if next_sec:
        bullets = [line.strip() for line in next_sec.splitlines() if line.strip()]
        waiting = []
        verify = []
        tracking = []
        for line in bullets:
            clean = clean_line(line)
            if not clean:
                continue
            if '待' in clean or '下次更新' in clean:
                waiting.append(clean)
            elif '跟踪' in clean or '观察' in clean or '减持' in clean:
                tracking.append(clean)
            else:
                verify.append(clean)
        lines.append('- 等待补充：')
        lines.extend([f'  - {x}' for x in waiting] or ['  - 无'])
        lines.append('- 需要验证：')
        lines.extend([f'  - {x}' for x in verify] or ['  - 无'])
        lines.append('- 需要持续跟踪：')
        lines.extend([f'  - {x}' for x in tracking] or ['  - 无'])
    else:
        lines.extend(['- 等待补充：', '  - 无', '- 需要验证：', '  - 无', '- 需要持续跟踪：', '  - 无'])

    if investment.get('next_update'):
        lines.extend(['', f'> 下次建议更新：{investment.get("next_update")}'])

    next_steps_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({
        'coverage_updated': str(coverage_path),
        'next_steps_updated': str(next_steps_path)
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
