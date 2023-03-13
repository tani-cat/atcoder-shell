from logging import Logger
import subprocess
from typing import Sequence

from .consts import ENCODING
from .utils import get_cheet_dir, search_contest_json


def extend_cheetsheet(logger: Logger, argv: Sequence[str]) -> int:
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
    cheet_dir = get_cheet_dir()
    cheet_path = cheet_dir / sheet_name
    if not cheet_path.is_file():
        # チートシートがない
        raise RuntimeError(f'チートシートが見つかりません: {sheet_name}')

    # ファイルをコピーして追加する
    with cheet_path.open(encoding=ENCODING) as rf:
        data = rf.read()

    target_path = target_dir / sheet_name
    with target_path.open(mode='w', encoding=ENCODING) as wf:
        wf.write(data)

    logger.info(f'チートシート: {sheet_name} -> {target_path.parent.parent}/{target_path.parent}')
    return 0


def open_cheet_dir(logger: Logger, argv: Sequence[str]) -> int:
    """チートシートフォルダを開く"""
    cheet_path = get_cheet_dir()
    logger.info(f'フォルダ: {cheet_path}')
    subprocess.run(f'open {cheet_path}', shell=True)
    return 0
