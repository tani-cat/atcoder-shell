from logging import Logger
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from ..consts import ENCODING, LANG_TABLE
from ..utils import (
    get_soup, load_json, get_cheat_dir, print_bar, save_json, CookieSession, URL
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
            self.logger.debug('問題情報を読み込みました')
        else:
            raise RuntimeError('コンテストフォルダにいません')

        self.json_path = json_path
        self.testcases = []
        # task_infoの情報をattrに格納する
        for key, value in task_info.items():
            self.__setattr__(f'{key}', value)

    def __str__(self):
        return self.__getattribute__('code')

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
            cheat_dir = get_cheat_dir()
            for file in cheat_dir.joinpath('cheatsheets').glob('**/*.py'):
                codefile_table[file.stem] = file
        except RuntimeError as e:
            self.logger.warning(str(e))
            pass

        # マージ対象となるモジュールをインポートしている場合は、そのモジュールのコードを追加する
        text_l = []
        for line in code_l:
            reg_res = self.REG_IMPORT.match(line.strip())
            if reg_res is None:
                # インポート文の条件を満たさない
                text_l.append(line)
                continue

            for module_name in reg_res.groups():
                if module_name in codefile_table:
                    # モジュールを読み込んでいた場合
                    if len(text_l) > 0:
                        text_l.append('\n')
                    module_path: Path = codefile_table[module_name]
                    with module_path.open(encoding=ENCODING) as mf:
                        ext_l = [text for text in mf.readlines() if len(text.strip()) > 0]
                        text_l.extend(ext_l)

                    text_l.append('\n')
                    break
            else:
                # マージ対象のモジュールでない
                text_l.append(line)

        # 結合したコードを保存する
        merged_py = self.json_path.parent.joinpath(self.code + '_merged.py')
        with merged_py.open(mode='w', encoding=ENCODING) as wf:
            wf.writelines(text_l)

        return merged_py

    def __execute_code(
        self, lang: str, codefile_path: Path, test_in: str, test_out: str,
        label: Optional[str] = None,
    ) -> Tuple[bool, str]:
        res_text = []
        res_flg = False
        if lang not in LANG_TABLE:
            raise RuntimeError(f'定義されていない言語: {lang}')

        if isinstance(label, str):
            disp_label = f'{self.code} ({label})'
        else:
            disp_label = self.code

        exec_lang = LANG_TABLE[lang]
        try:
            sta = time.time()
            res = subprocess.run(
                exec_lang + ' ' + str(codefile_path),
                shell=True,
                input=test_in.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.time_limit + 2,
            )
            proc_t = int((time.time() - sta) * 1000)
        except subprocess.TimeoutExpired:
            proc_t = int((time.time() - sta) * 1000)
            res_text.append(f'{disp_label}: TLE[{proc_t} > {self.time_limit * 1000} msec]')
        else:
            stdout = res.stdout.decode()
            stderr = res.stderr.decode()
            if len(stderr) > 0:
                # 標準エラー
                res_text.append(f'{disp_label}: {proc_t} msec')
                if len(stdout) > 0:
                    # 標準出力があれば併記
                    res_text.append('[output]')
                    res_text += stdout.split('\n')
                # トレースバック
                res_text.append('[traceback]')
                res_text += stderr.split('\n')
            elif test_out == stdout:
                # 想定出力と一致
                res_text.append(f'OK: {disp_label}: {proc_t} msec')
                res_flg = True
            else:
                # 想定出力と異なる
                res_text.append(f'NG: {disp_label}: {proc_t} msec')
                # 想定出力と実際出力を表示
                res_text.append('[predict output]')
                res_text += test_out.split('\n')
                res_text.append('[exact output]')
                res_text += stdout.split('\n')

        res_text[0] += f' (in {lang})'
        return res_flg, '\n'.join(res_text)

    def update_testcase(self):
        """テストケースの取得更新
        """
        with CookieSession() as session:
            try:
                soup = get_soup(session, URL.task(self.contest, self.code))
            except RuntimeError:
                raise RuntimeError(f'テストケースの取得に失敗しました: {self.contest} - {self.code}')

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
            self.logger.info(f'問題のテストケースを更新しました: {self.code}')

    def run_testcase(self, lang: str, target: str = None) -> None:
        """テストケースの実行
        """
        if not self.testcases:
            self.update_testcase()

        if target is None:
            target = list(range(len(self.testcases)))
        else:
            try:
                target = [int(target)]
            except ValueError:
                self.logger.error('テストケースの番号は整数で指定してください')
                return

        codefile_path = self.__merge_code_file()
        os.chdir(str(self.json_path.parent))

        counter = {True: 0, False: 0}
        for i, case in enumerate(self.testcases):
            if i not in target:
                continue
            res_flg, res_text = \
                self.__execute_code(
                    lang, codefile_path, case['input'], case['output'], f'Case {i + 1}')
            counter[res_flg] += 1
            if res_flg:
                self.logger.info(res_text)
            else:
                self.logger.error(res_text)

            print_bar()

        self.logger.info(f'テストの実行結果:\n{counter[True]} OK, {counter[False]} NG')

    def submit_code(self, lang: str) -> None:
        """提出
        """
        # 実行ファイルを1つにまとめる
        merged_path = self.__merge_code_file()

        with merged_path.open(encoding=ENCODING) as f:
            code_text = f.read()

        with CookieSession() as session:
            try:
                soup = get_soup(session, URL.submit(self.contest, self.code))
            except RuntimeError:
                raise RuntimeError(f'ページの取得に失敗しました: {self.contest}')

            # post に必要なデータを整理する
            lang_sel = soup.select_one(f'#select-lang-{self.code}').select_one('select')
            lang_soup = lang_sel.select('option')
            lang_dict = {x.text: x['value'] for x in lang_soup if len(x.text)}
            data = {
                'data.TaskScreenName': self.code,
                'data.LanguageId': lang_dict[lang],
                'sourceCode': code_text,
                'csrf_token': soup.find('input', attrs={'name': 'csrf_token'})['value'],
            }
            res = session.post(URL.submit(self.contest, self.code), data=data)

        if res.status_code == 200:
            # 成功
            self.logger.info(f'コードを提出しました: {self.key} (lang: {lang_dict[lang]})')
        else:
            # 失敗
            raise RuntimeError(
                f'コードの提出に失敗しました: {self.key} (lang: {lang_dict[lang]})\n'
                f'Response Code: {res.status_code}'
            )
