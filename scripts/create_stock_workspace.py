#!/usr/bin/env python3
import os
import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(os.environ.get('STOCK_WORKSPACE_DIR', Path(__file__).parents[2] / 'stocks'))
TEMPLATE = BASE / '_templates' / 'company'


def safe_name(value: str) -> str:
    value = value.strip()
    value = re.sub(r'[\\/:*?"<>|]+', '-', value)
    value = re.sub(r'\s+', '-', value)
    value = re.sub(r'-+', '-', value).strip('-')
    return value or 'unknown'


def market_prefix(market: str) -> str:
    market = market.upper()
    if market in {'CN', 'A', 'ASHARE'}:
        return 'CN'
    if market in {'HK', 'H'}:
        return 'HK'
    if market in {'US'}:
        return 'US'
    return market


def default_exchange(market: str, ticker: str, exchange: str | None) -> str:
    if exchange:
        exchange = exchange.upper()
        alias = {'SZSE': 'SZ', 'SSE': 'SH'}
        return alias.get(exchange, exchange)
    market = market.upper()
    ticker = ticker.upper()
    if market in {'CN', 'A', 'ASHARE'}:
        if ticker.startswith('6'):
            return 'SH'
        return 'SZ'
    if market == 'HK':
        return 'HK'
    if market == 'US':
        return 'NASDAQ'
    return ''


def folder_name(market: str, exchange: str, ticker: str, name: str) -> str:
    return '-'.join([
        market_prefix(market),
        exchange.upper() if exchange else 'NA',
        ticker.upper(),
        safe_name(name),
    ])


def ensure_dirs(base: Path) -> None:
    for rel in [
        '02_raw/market-data',
        '02_raw/financials',
        '02_raw/news',
        '02_raw/filings',
        '02_raw/misc',
        '05_reports/report-history',
    ]:
        (base / rel).mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a stock research workspace from template.')
    parser.add_argument('--ticker', required=True, help='Ticker, e.g. 600519 or AAPL')
    parser.add_argument('--name', required=True, help='Company short name')
    parser.add_argument('--market', required=True, help='CN / HK / US')
    parser.add_argument('--exchange', help='SH / SZ / HK / NASDAQ / NYSE ...')
    parser.add_argument('--industry', default='', help='Industry label')
    parser.add_argument('--currency', default='', help='CNY / HKD / USD ...')
    parser.add_argument('--owner', default='xiaodaidai', help='Primary owner agent')
    parser.add_argument('--force', action='store_true', help='Overwrite if folder already exists')
    args = parser.parse_args()

    exchange = default_exchange(args.market, args.ticker, args.exchange)
    dirname = folder_name(args.market, exchange, args.ticker, args.name)
    target = BASE / dirname

    normalized_market = market_prefix(args.market)
    dup_glob = f'{normalized_market}-*-{args.ticker.upper()}-*'
    existing = [p for p in BASE.glob(dup_glob) if p.is_dir() and p.name != dirname]
    if existing and not target.exists() and not args.force:
        names = ', '.join(str(p) for p in existing)
        raise SystemExit(f'Potential duplicate workspace exists for ticker {args.ticker.upper()}: {names}')

    if target.exists():
        if not args.force:
            raise SystemExit(f'Workspace already exists: {target}')
        shutil.rmtree(target)

    shutil.copytree(TEMPLATE, target)
    ensure_dirs(target)

    now = datetime.now().isoformat(timespec='seconds')

    phases = load_json(target / '00_meta' / 'phases.json')
    if phases.get('phases'):
        phases['phases'][0]['status'] = 'in_progress'
        phases['current_phase'] = '1'
    write_json(target / '00_meta' / 'phases.json', phases)

    stock = load_json(target / '00_meta' / 'stock.json')
    stock.update({
        'ticker': args.ticker.upper(),
        'name': args.name,
        'market': market_prefix(args.market),
        'exchange': exchange,
        'industry': args.industry,
        'currency': args.currency,
        'research_status': 'new',
        'coverage_started_at': now,
        'last_updated_at': now,
        'owners': [args.owner],
        'tags': [],
    })
    write_json(target / '00_meta' / 'stock.json', stock)

    coverage = load_json(target / '00_meta' / 'coverage.json')
    coverage['open_questions'] = [
        '公司核心业务和收入结构是什么？',
        '当前市场为什么关注它？',
        '估值相对同行是贵还是便宜？',
        '未来 6-12 个月催化剂是什么？',
    ]
    write_json(target / '00_meta' / 'coverage.json', coverage)

    links = target / '01_sources' / 'links.md'
    links.write_text(
        '# Links\n\n'
        f'- Official investor relations: \n'
        f'- Exchange filings: \n'
        f'- Financial data source: \n'
        f'- Industry source: \n'
        f'- News / article sources: \n\n'
        f'> Ticker: {args.ticker.upper()} | Name: {args.name} | Market: {market_prefix(args.market)} | Exchange: {exchange}\n',
        encoding='utf-8'
    )

    initial = target / '04_analysis' / '01_initial-questions.md'
    initial.write_text(
        '# Initial Questions\n\n'
        f'## 标的\n- 名称：{args.name}\n- 代码：{args.ticker.upper()}\n- 市场：{market_prefix(args.market)}\n- 交易所：{exchange}\n\n'
        '## 第一轮问题\n'
        '- 公司是做什么的，核心收入从哪里来？\n'
        '- 行业位置和竞争优势是什么？\n'
        '- 当前市场关注它的主要逻辑是什么？\n'
        '- 当前估值对应了什么预期？\n'
        '- 未来 6-12 个月最重要的催化剂和风险是什么？\n',
        encoding='utf-8'
    )

    report = target / '05_reports' / 'report-master.md'
    report.write_text(
        '# 股票研究主报告\n\n'
        f'> 标的：{args.name} ({args.ticker.upper()})\n\n'
        '## 1. 标的概览\n\n'
        f'- 公司名称：{args.name}\n'
        f'- 股票代码：{args.ticker.upper()}\n'
        f'- 市场 / 交易所：{market_prefix(args.market)} / {exchange}\n'
        f'- 行业：{args.industry or "待补充"}\n'
        '- 当前研究状态：初始建档\n\n'
        '## 2. 一句话结论\n\n'
        '- 结论：待补充\n'
        '- 评级：观察\n\n'
        '## 3. 核心逻辑\n\n'
        '### 3.1 做多逻辑\n\n'
        '### 3.2 市场当前分歧\n\n'
        '### 3.3 本次研究最关键的验证点\n\n'
        '## 4. 业务与竞争格局\n\n'
        '### 4.1 公司是做什么的\n\n'
        '### 4.2 收入结构与增长驱动\n\n'
        '### 4.3 行业格局与竞争优势\n\n'
        '### 4.4 关键护城河判断\n\n'
        '## 5. 基本面分析\n\n'
        '### 5.1 收入与利润质量\n\n'
        '### 5.2 毛利率、净利率、ROE、ROIC\n\n'
        '### 5.3 现金流与资产负债表\n\n'
        '### 5.4 分红、资本开支与财务稳健性\n\n'
        '## 6. 估值分析\n\n'
        '### 6.1 当前估值水平\n\n'
        '### 6.2 同行对比\n\n'
        '### 6.3 估值是否透支预期\n\n'
        '## 7. 技术分析\n\n'
        '### 7.1 整体趋势\n- 长期趋势：\n- 中期趋势：\n- 短期趋势：\n\n'
        '### 7.2 关键支撑与压力\n- 第一支撑：\n- 第二支撑：\n- 第一压力：\n- 第二压力：\n\n'
        '### 7.3 成交量、资金流、形态\n\n'
        '### 7.4 技术结论\n\n'
        '## 8. 催化剂与风险\n\n'
        '### 8.1 未来 3-12 个月催化剂\n\n'
        '### 8.2 主要风险\n\n'
        '### 8.3 哪些信号会推翻当前观点\n\n'
        '## 9. 情景分析\n\n'
        '### 9.1 乐观情景\n\n'
        '### 9.2 中性情景\n\n'
        '### 9.3 悲观情景\n\n'
        '## 10. 投资建议与交易计划\n\n'
        '### 10.1 当前建议\n- 结论：\n- 适合人群：长线 / 波段 / 观察\n\n'
        '### 10.2 建仓思路\n- 理想关注区间：\n- 不追高原则：\n\n'
        '### 10.3 止盈线\n- 第一止盈线：\n- 第二止盈线：\n- 止盈依据：\n\n'
        '### 10.4 止损线\n- 硬止损线：\n- 条件止损线：\n- 止损依据：\n\n'
        '## 11. 参考资料与来源\n\n'
        '- 官方公告：\n- 交易所披露：\n- 财务数据来源：\n- 行业资料：\n- 重要新闻 / 深度文章：\n\n'
        '## 12. 待补问题与下一步\n\n'
        '- 仍待确认：\n- 下轮更新重点：\n',
        encoding='utf-8'
    )

    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
