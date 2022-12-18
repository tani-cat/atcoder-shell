from logging import getLogger, StreamHandler, INFO, Formatter
from typing import Sequence

from .contest.contest import load_contest
from .contest.task import check_testcase
from . import help, login


class ACShell:
    """シェル処理を集約したクラス

    コマンド実行ごとにインスタンスが生成され、処理を行う
    """

    def __init__(self) -> None:
        # 制御
        self.exec_code = 0
        self.logger = getLogger('acshell')
        self.logger.setLevel(INFO)

        if not self.logger.hasHandlers():
            # Stream: ログの標準出力
            sh = StreamHandler()
            sh.setLevel(INFO)
            sh_formatter = Formatter('[%(levelname)s] %(message)s')
            sh.setFormatter(sh_formatter)
            self.logger.addHandler(sh)

    def exit_code(self) -> int:
        """Return the program exit code."""
        # if self.catastrophic_failure:
        #     return 1
        # assert self.options is not None
        # if self.options.exit_zero:
        #     return 0
        # else:
        #     return int(self.result_count > 0)
        return self.exec_code

    def operate_command(self, argv: Sequence[str]) -> None:
        """コマンドの識別と実行処理
        """
        _exec_command = argv[0]
        if _exec_command == 'help':
            return help.help(self.logger, argv[1:])
        elif _exec_command == 'login':
            return login.login(self.logger, argv[1:])
        elif _exec_command == 'load':
            return load_contest(self.logger, argv[1:])
        elif _exec_command == 'check':
            return check_testcase(self.logger, argv[1:])
        elif _exec_command == 'submit':
            raise NotImplementedError
        else:
            # その他の入力
            raise NotImplementedError

    def run(self, argv: Sequence[str]) -> None:
        """コマンド実行の呼び出し
        """
        assert len(argv) > 0
        try:
            self.exec_code = self.operate_command(argv)
        except KeyboardInterrupt:
            self.exec_code = 1
        except NotImplementedError:
            self.logger.error(f'wrong command: {argv[0]}')
            self.exec_code = 1
        except RuntimeError as e:
            self.logger.error(e)
            self.exec_code = 1
