from logging import Logger
from pathlib import Path
import os
import re
import subprocess
import time
from typing import Dict, List, Sequence, Tuple

from ..const import ENCODING, LANG_TABLE
from ..utils import (
    get_soup, CookieSession, URL, save_json, load_json, get_cheet_dir,
    print_bar, search_contest_json,
)


class Task:
    """設問
    """

    TASK_KEY = [
        'contest', 'key', 'code', 'time_limit', 'memory_limit', 'testcases',
    ]
    REG_IMPORT = re.compile(r'^(?:from ([^.]+) )?import (?:([^.]+)\.)?(?:.+\.)*([^.]+)$')

    def __init__(self, logger: Logger, json_path: Path) -> None:
        """コンストラクタ
        """
        self.logger = logger
        if isinstance(json_path, Path):
            task_info = load_json(json_path)
            self.logger.info('Task info checked')
        else:
            raise RuntimeError('Not in contest directory')

        self.json_path = json_path
        self.testcases = []
        # task_infoの情報をattrに格納する
        for key, value in task_info.items():
            self.__setattr__(f'{key}', value)

    @property
    def task_info(self) -> Dict:
        resp = dict()
        for key in self.TASK_KEY:
            resp[key] = self.__getattribute__(key)

        return resp

    def __merge_code_file(self) -> Path:
        """フォルダ内のpyファイルをimport文に従って結合する
        """
        # 実行ファイルのコード取得
        base_py = self.json_path.parent.joinpath(self.code + '.py')
        with base_py.open(encoding=ENCODING) as mf:
            code_l = mf.readlines()

        # フォルダ内のコードファイル取得
        codefile_table = dict()
        for file in self.json_path.parent.glob('*.py'):
            if file == base_py:
                continue
            codefile_table[file.stem] = file

        # チートシートも取得しておく
        try:
            cheet_dir = get_cheet_dir()
            for file in cheet_dir.joinpath('cheetsheets').glob('**/*.py'):
                codefile_table[file.stem] = file
        except RuntimeError as e:
            self.logger.warning(str(e))
            pass

        # マージ対象となるモジュールをインポートしている場合は、そのモジュールのコードを追加する
        text_l = []
        for line in code_l:
            reg_res = self.REG_IMPORT(line)
            if reg_res is None:
                # インポート文の条件を満たさない
                text_l.append(line)
                continue

            for module_name in reg_res.groups():
                if module_name in codefile_table:
                    # モジュールを読み込んでいた場合
                    text_l.append('\n')
                    module_path: Path = codefile_table[module_name]
                    with module_path.open(encoding=ENCODING) as mf:
                        text_l.append(mf.readlines())
                    text_l.append('\n')
                    break
            else:
                # マージ対象のモジュールでない
                text_l.append(line)

        # 結合したコードを保存する
        merged_py = self.json_path.parent.joinpath(self.code + '_merged.py')
        with merged_py.open(mode='w', encoding=ENCODING) as wf:
            wf.writelines(text_l)

    def update_testcase(self):
        """テストケースの取得更新
        """
        with CookieSession() as session:
            try:
                soup = get_soup(session, URL.task(self.contest, self.code))
            except RuntimeError:
                raise RuntimeError(f'Failed to scrape testcase: {self.contest} - {self.code}')

        testcase_l: List[Dict] = []
        for part in soup.select_one('#task-statement').select('.part'):
            part_title = part.select_one('h3').text[:3]
            if part_title == '入力例':
                testcase_l.append(dict())
                testcase_l[-1]['input'] = part.select_one('pre').text.replace('\r', '')
            elif part_title == '出力例':
                testcase_l[-1]['output'] = part.select_one('pre').text.replace('\r', '')

        if len(testcase_l):
            self.testcases = testcase_l
            save_json(self.json_path, self.task_info)
            self.logger.info(f'Task testcases updated: {self.code}')

    def run_testcase(self, lang: str) -> None:
        """テストケースの実行
        """
        if not self.testcases:
            self.update_testcase()

        # TODO: コードファイルのマージ機能
        codefile_path = self.json_path.parent.joinpath(self.code + '.py')
        os.chdir(str(self.json_path.parent))

        counter = {True: 0, False: 0}
        for case in self.testcases:
            res_flg, res_text = \
                self.__execute_code(lang, codefile_path, case['input'], case['output'])
            counter[res_flg] += 1
            if res_flg:
                self.logger.info(res_text)
            else:
                self.logger.error(res_text)

            print_bar()

        self.logger.info(f'All testcases have finished:\n{counter[True]} OK, {counter[False]} NG')

    def __execute_code(
        self, lang: str, codefile_path: Path, test_in: str, test_out: str,
    ) -> Tuple[bool, str]:
        res_text = []
        res_flg = False
        if lang not in LANG_TABLE:
            raise RuntimeError(f'Not implemented lang: {lang}')

        exec_lang = LANG_TABLE[lang]
        try:
            sta = time.time()
            res = subprocess.run(
                exec_lang + ' ' + str(codefile_path),
                shell=True,
                input=test_in.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.time_limit,
            )
            proc_t = int((time.time() - sta) * 1000)
        except subprocess.TimeoutExpired:
            res_text.append(f'{self.code}: TLE[{self.time_limit} sec]')
        else:
            stdout = res.stdout.decode()
            stderr = res.stderr.decode()
            if len(stderr) > 0:
                # 標準エラー
                res_text.append(f'{self.code}: {proc_t} msec')
                if len(stdout) > 0:
                    # 標準出力があれば併記
                    res_text.append('[output]')
                    res_text += stdout.split('\n')
                # トレースバック
                res_text.append('[traceback]')
                res_text += stderr.split('\n')
            elif test_out == stdout:
                # 想定出力と一致
                res_text.append(f'OK: {self.code}: {proc_t} msec')
                res_flg = True
            else:
                # 想定出力と異なる
                res_text.append(f'NG: {self.code}: {proc_t} msec')
                # 想定出力と実際出力を表示
                res_text.append('[predict output]')
                res_text += test_out.split('\n')
                res_text.append('[exact output]')
                res_text += stdout.split('\n')

        res_text[0] += f' (in {lang})'
        return res_flg, '\n'.join(res_text)


def check_testcase(logger: Logger, argv: Sequence[str]) -> int:
    """公式のテストケースでチェックする
    """
    # 引数の処理
    lang = ''
    task = ''
    if len(argv) >=2:
        task = argv[1]
    if len(argv) >= 1:
        lang = argv[0]
    else:
        raise RuntimeError('Lack of arguments')

    current_dir = Path.cwd()
    # TODO: 深いところでも再帰的に探せるようにする
    task_path = current_dir.joinpath('.task.json')
    if task:
        contest_json = search_contest_json()
        if contest_json is None:
            raise RuntimeError('Not in acshell directory')
        task_path = contest_json.parent / task / '.task.json'
    if task_path.is_file():
        task = Task(logger, task_path)
        task.run_testcase(lang)
    else:
        raise RuntimeError(f'Wrong task path: {task_path}')

    return 0