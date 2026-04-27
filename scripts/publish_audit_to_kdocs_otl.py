#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

ROOT_FOLDER_NAME = 'openclaw'


def run(cmd: list[str]) -> dict:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def find_openclaw_folder() -> tuple[str, str]:
    data = run(['kdocs-cli', 'drive', 'search-files', 'keyword=openclaw', 'type=all', 'file_type=folder', 'page_size=20'])
    items = data['data']['data'].get('items', [])
    for item in items:
        f = item['file']
        if f['name'].lower() == ROOT_FOLDER_NAME:
            return f['drive_id'], f['id']
    raise SystemExit('KDocs folder not found: openclaw')


def main() -> int:
    parser = argparse.ArgumentParser(description='Publish stock research audit report to KDocs .otl')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--report', required=True, help='Path to audit markdown report')
    parser.add_argument('--title', help='Document title without suffix')
    args = parser.parse_args()

    base = Path(args.dir)
    report_path = Path(args.report)
    stock_meta_path = base / '00_meta' / 'stock.json'
    stock_meta = json.loads(stock_meta_path.read_text(encoding='utf-8'))

    if not report_path.exists():
        raise SystemExit(f'Missing audit report: {report_path}')

    drive_id, parent_id = find_openclaw_folder()
    title = args.title or f"{stock_meta.get('name') or stock_meta.get('ticker','stock')}-研究审计报告"
    file_name = f'{title}.otl'

    create_payload = {'drive_id': drive_id, 'parent_id': parent_id, 'file_type': 'file', 'name': file_name}
    create_json = Path('/tmp/kdocs_audit_create.json')
    create_json.write_text(json.dumps(create_payload, ensure_ascii=False), encoding='utf-8')
    created = run(['kdocs-cli', 'drive', 'create-file', f'@{create_json}'])
    file_id = created['data']['data']['id']

    insert_payload = {'file_id': file_id, 'content': report_path.read_text(encoding='utf-8'), 'pos': 'end'}
    insert_json = Path('/tmp/kdocs_audit_insert.json')
    insert_json.write_text(json.dumps(insert_payload, ensure_ascii=False), encoding='utf-8')
    run(['kdocs-cli', 'otl', 'insert-content', f'@{insert_json}', '--silent'])

    share_payload = {
        'drive_id': drive_id,
        'file_id': file_id,
        'scope': 'anyone',
        'opts': {'allow_perm_apply': True, 'close_after_expire': False, 'expire_period': 0},
    }
    share_json = Path('/tmp/kdocs_audit_share.json')
    share_json.write_text(json.dumps(share_payload, ensure_ascii=False), encoding='utf-8')
    shared = run(['kdocs-cli', 'drive', 'share-file', f'@{share_json}'])
    share_url = shared['data']['data']['url']

    stock_meta['audit_doc_id'] = file_id
    stock_meta['audit_kdocs_link'] = share_url
    stock_meta_path.write_text(json.dumps(stock_meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps({'file_id': file_id, 'share_url': share_url, 'title': file_name}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
