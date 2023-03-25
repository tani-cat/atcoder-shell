from logging import Logger
from typing import Sequence

from .consts import LANG_TABLE, SUB_LANG_TABLE
from .contest.task import Task
from .utils import (
    search_task_json,
)


def __pre_operate(logger, argv) -> Task:
    """共通の前処理"""
    # 引数の処理
    lang = list(LANG_TABLE.keys())[0]
    task_code = ''
    if len(argv) >= 2:
        lang = argv[1]
    if len(argv) >= 1:
        task_code = argv[0]
    else:
        raise RuntimeError('オプションが不足しています')

    task_path = search_task_json(task_code)
    task = Task(logger, task_path)
    return task, lang


def check_testcase(logger: Logger, argv: Sequence[str]) -> int:
    """公式のテストケースでチェックする
    """
    task: Task
    task, lang = __pre_operate(logger, argv)
    task.run_testcase(lang)
    return 0


def submit_code(logger: Logger, argv: Sequence[str]) -> int:
    """コードを提出する
    """
    task: Task
    task, lang = __pre_operate(logger, argv)
    task.submit_code(SUB_LANG_TABLE[lang])

    return 0


def test_code(logger: Logger, argv: Sequence[str]) -> int:
    """単一のテストケースでチェックする
    """
    lang = list(LANG_TABLE.keys())[0]
    task_code = ''
    if len(argv) >= 3:
        lang = argv[1]
    if len(argv) >= 2:
        task_code = argv[0]
        test_num = argv[1]
    else:
        raise RuntimeError('オプションが不足しています')

    task_path = search_task_json(task_code)
    task = Task(logger, task_path)
    task.run_testcase(lang, test_num)
    return 0
