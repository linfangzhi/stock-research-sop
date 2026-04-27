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
    parser = argparse.ArgumentParser(description='Publish stock KDocs export to an .otl smart doc in KDocs openclaw folder.')
    parser.add_argument('--dir', required=True, help='Path to stock folder')
    parser.add_argument('--title', help='Document title without suffix')
    args = parser.parse_args()

    base = Path(args.dir)
    stock_meta = json.loads((base / '00_meta' / 'stock.json').read_text(encoding='utf-8'))
    export_path = base / '05_reports' / 'kdocs-export.md'
    if not export_path.exists():
        raise SystemExit(f'Missing export file: {export_path}')

    drive_id, parent_id = find_openclaw_folder()
    title = args.title or f"{stock_meta.get('name') or stock_meta.get('ticker','stock')}-股票研究档案"
    file_name = f'{title}.otl'

    create_payload = {'drive_id': drive_id, 'parent_id': parent_id, 'file_type': 'file', 'name': file_name}
    create_json = Path('/tmp/kdocs_publish_create.json')
    create_json.write_text(json.dumps(create_payload, ensure_ascii=False), encoding='utf-8')
    created = run(['kdocs-cli', 'drive', 'create-file', f'@{create_json}'])
    created_data = created['data']['data']
    file_id = created_data['id']

    insert_payload = {'file_id': file_id, 'content': export_path.read_text(encoding='utf-8'), 'pos': 'end'}
    insert_json = Path('/tmp/kdocs_publish_insert.json')
    insert_json.write_text(json.dumps(insert_payload, ensure_ascii=False), encoding='utf-8')
    run(['kdocs-cli', 'otl', 'insert-content', f'@{insert_json}', '--silent'])

    share_payload = {
        'drive_id': drive_id,
        'file_id': file_id,
        'scope': 'anyone',
        'opts': {'allow_perm_apply': True, 'close_after_expire': False, 'expire_period': 0},
    }
    share_json = Path('/tmp/kdocs_publish_share.json')
    share_json.write_text(json.dumps(share_payload, ensure_ascii=False), encoding='utf-8')
    shared = run(['kdocs-cli', 'drive', 'share-file', f'@{share_json}'])
    share_url = shared['data']['data']['url']

    stock_meta['kdocs_doc_id'] = file_id
    stock_meta['kdocs_link'] = share_url
    (base / '00_meta' / 'stock.json').write_text(json.dumps(stock_meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps({'file_id': file_id, 'share_url': share_url, 'title': file_name}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
