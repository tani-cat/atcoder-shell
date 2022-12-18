from logging import Logger
from typing import Sequence


def load_cheetsheet(logger: Logger, argv: Sequence[str]):
    """チートシートをコードファイルに追加する
    """
    if len(argv) < 2:
        raise RuntimeError('Lack of argument')

    task_code, sheet_name = argv[:2]
    if len(argv) > 2:
        mode = argv[2]
    else:
        mode = ''

    # 指定された問題のコードファイルにチートシートを追加する
    pass
