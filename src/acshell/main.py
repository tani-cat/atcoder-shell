import sys
from typing import Optional, Sequence

from . import acshell


def main(argv: Optional[Sequence[str]] = None) -> int:
    """コマンド実行時に呼び出される関数

    Args:
        argv (:obj:`str`, optional): コマンドライン引数
    """
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        print('実行コマンドが指定されていません')
        return 1
    instance = acshell.ACShell()
    instance.run(argv)
    return instance.exit_code()


if __name__ == '__main__':
    raise SystemExit(main())
