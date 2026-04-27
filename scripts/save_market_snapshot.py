#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Save market snapshot to raw + normalized files.')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--price', type=float, required=True)
    parser.add_argument('--market-cap', type=float, dest='market_cap')
    parser.add_argument('--high52', type=float)
    parser.add_argument('--low52', type=float)
    parser.add_argument('--avg-volume', type=float, dest='avg_volume')
    parser.add_argument('--turnover', type=float)
    parser.add_argument('--long-trend', default='')
    parser.add_argument('--mid-trend', default='')
    parser.add_argument('--short-trend', default='')
    parser.add_argument('--support', action='append', default=[])
    parser.add_argument('--resistance', action='append', default=[])
    parser.add_argument('--stop-loss', type=float, dest='stop_loss')
    parser.add_argument('--take-profit', action='append', default=[])
    parser.add_argument('--flag', action='append', default=[])
    args = parser.parse_args()

    base = Path(args.dir)
    raw_dir = base / '02_raw' / 'market-data'
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f'snapshot-{args.date}.json'
    normalized_path = base / '03_normalized' / 'market-snapshot.json'

    take_profit_lines = [float(x) for x in args.take_profit] if args.take_profit else []
    support_levels = [float(x) for x in args.support] if args.support else []
    resistance_levels = [float(x) for x in args.resistance] if args.resistance else []

    payload = {
        'date': args.date,
        'price': args.price,
        'market_cap': args.market_cap,
        '52w_high': args.high52,
        '52w_low': args.low52,
        'avg_volume': args.avg_volume,
        'turnover': args.turnover,
        'long_trend': args.long_trend,
        'mid_trend': args.mid_trend,
        'short_trend': args.short_trend,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'stop_loss_line': args.stop_loss,
        'take_profit_lines': take_profit_lines,
        'technical_flags': args.flag,
        'saved_at': datetime.now().isoformat(timespec='seconds')
    }
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    normalized = json.loads(normalized_path.read_text(encoding='utf-8')) if normalized_path.exists() else {}
    normalized.update({
        'price': args.price,
        'market_cap': args.market_cap,
        '52w_high': args.high52,
        '52w_low': args.low52,
        'avg_volume': args.avg_volume,
        'turnover': args.turnover,
        'trend_summary': ' / '.join([x for x in [args.long_trend, args.mid_trend, args.short_trend] if x]),
        'long_trend': args.long_trend,
        'mid_trend': args.mid_trend,
        'short_trend': args.short_trend,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'stop_loss_line': args.stop_loss,
        'take_profit_lines': take_profit_lines,
        'technical_flags': args.flag,
    })
    normalized_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'raw': str(raw_path), 'normalized': str(normalized_path)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
