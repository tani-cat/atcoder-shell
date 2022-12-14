import logging
from typing import Sequence

from .texts import HELP_TEXT


def __format_help_text(command: str) -> str:
    data = HELP_TEXT[command]
    text = f'\t{command}'
    if data.get('args', ''):
        text += f' [{data.get("args", "")}]'
    text += ' : ' + data.get('text', '')
    return text


def help(logger: logging.Logger, argv: Sequence[str]) -> bool:
    """コマンド一覧を表示する
    """
    if len(argv) > 0:
        # コマンドの指定がある場合
        if argv[0] in HELP_TEXT:
            print(__format_help_text(argv[0]))
        else:
            logger.error(f'コマンドのヘルプは設定されていません: {argv[0]}')
    else:
        for command in sorted(HELP_TEXT.keys()):
            print(__format_help_text(command))

    return 0
