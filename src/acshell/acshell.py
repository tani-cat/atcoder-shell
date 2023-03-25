from logging import getLogger, StreamHandler, INFO, Formatter
from typing import Sequence

from .contest.contest import load_contest
from . import cheatsheet, help, login, result, task_run


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
        return self.exec_code

    def operate_command(self, argv: Sequence[str]) -> None:
        """コマンドの識別と実行処理
        """
        _exec_command = argv[0]
        if _exec_command in ('help', 'h'):
            return help.help(self.logger, argv[1:])
        elif _exec_command in ('login', 'lg'):
            return login.login(self.logger, argv[1:])
        elif _exec_command in  ('load', 'ld'):
            return load_contest(self.logger, argv[1:])
        elif _exec_command in ('test', 't'):
            return task_run.test_code(self.logger, argv[1:])
        elif _exec_command in ('check', 'c'):
            return task_run.check_testcase(self.logger, argv[1:])
        elif _exec_command in ('submit', 's'):
            return task_run.submit_code(self.logger, argv[1:])
        elif _exec_command in ('recent', 'rc'):
            return result.recent_result(self.logger, argv[1:])
        elif _exec_command in ('status', 'rs'):
            return result.status(self.logger, argv[1:])
        elif _exec_command in ('edit-cheat', 'ec'):
            return cheatsheet.open_cheat_dir(self.logger, argv[1:])
        elif _exec_command in ('add-cheat', 'ac'):
            return cheatsheet.extend_cheatsheet(self.logger, argv[1:])
        elif _exec_command in ('list-cheat', 'lc'):
            return cheatsheet.list_cheat_file(self.logger, argv[1:])
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
            self.logger.error(f'不正なコマンド: {argv[0]}')
            self.exec_code = 1
        except RuntimeError as e:
            self.logger.error(e)
            self.exec_code = 1
