from logging import Logger
import subprocess
from typing import Sequence

from .consts import ENCODING
from .utils import get_cheat_dir, search_contest_json


def extend_cheatsheet(logger: Logger, argv: Sequence[str]) -> int:
    """チートシートをコードファイルに追加する
    """
    if len(argv) < 2:
        raise RuntimeError('オプションが不足しています')

    task_code, sheet_name = argv[:2]
    if sheet_name[:-3] != '.py':
        sheet_name += '.py'

    # チートシートを追加するディレクトリ
    contest_json = search_contest_json()
    target_dir = contest_json.parent / task_code
    if not target_dir.is_dir():
        # コードのディレクトリがない
        raise RuntimeError(f'問題コードが見つかりません: {task_code}')

    # チートシート
    cheat_dir = get_cheat_dir()
    cheat_path = cheat_dir / sheet_name
    if not cheat_path.is_file():
        # チートシートがない
        raise RuntimeError(f'チートシートが見つかりません: {sheet_name}')

    # ファイルをコピーして追加する
    with cheat_path.open(encoding=ENCODING) as rf:
        data = rf.read()

    target_path = target_dir / sheet_name
    with target_path.open(mode='w', encoding=ENCODING) as wf:
        wf.write(data)

    logger.info(f'チートシート: {sheet_name} -> {target_path.parent.parent}/{target_path.parent}')
    return 0


def open_cheat_dir(logger: Logger, argv: Sequence[str]) -> int:
    """チートシートフォルダを開く"""
    cheat_path = get_cheat_dir()
    logger.info(f'フォルダ: {cheat_path}')
    subprocess.run(f'open {cheat_path}', shell=True)
    return 0


def list_cheat_file(logger: Logger, argv: Sequence[str]) -> int:
    """チートシートの一覧を表示する"""
    cheat_path = get_cheat_dir()
    logger.info(f'フォルダ: {cheat_path}')
    file_l = sorted(list(file for file in cheat_path.glob('*.py')))
    for file in file_l:
        print(f'\t{file.stem}')
    return 0
