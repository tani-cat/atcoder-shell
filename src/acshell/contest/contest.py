from logging import Logger
from pathlib import Path
import re
from typing import Dict, Optional, Sequence, List

from bs4 import BeautifulSoup

from ..consts import ENCODING
from ..utils import (
    CookieSession, URL, get_soup, save_json, search_contest_json, load_json,
    get_cheat_dir,
)


class Contest:
    """コンテスト
    """

    _CONTEST_KEY = [
        'code', 'title', 'start_dt', 'end_dt',
    ]
    _CONTEST_TASK_KEY = [
        'code', 'name', 'score',
    ]

    def __init__(self, logger: Logger, json_path: Optional[Path] = None) -> None:
        """コンストラクタ
        """
        self.logger = logger
        contest_info: Dict = dict()
        if json_path is None:
            # 直上にあるcontest.jsonを探す
            json_path = search_contest_json()

        if isinstance(json_path, Path):
            contest_info = load_json(json_path)
            self.logger.debug('コンテスト情報を取得')
        else:
            raise RuntimeError('コンテストフォルダにいません')

        self.json_path = json_path
        self.tasks = dict()
        # contest_infoの情報をattrに格納する
        for key, value in contest_info.items():
            self.__setattr__(f'{key}', value)

        # task_infoについても追加する
        for task_key in self.tasks:
            if not self.task_path(task_key).is_file():
                continue

            task_info = load_json(self.task_path(task_key))
            self.tasks[task_key].update(task_info)

    def __str__(self):
        return self.__getattribute__('code')

    @property
    def contest_name(self):
        return self.__getattribute__('title')

    @property
    def contest_dict(self) -> Dict:
        resp = dict()
        for key in self._CONTEST_KEY:
            resp[key] = self.__getattribute__(f'{key}')

        resp['tasks'] = dict()
        for t_key, task in self.tasks.items():
            resp['tasks'][t_key] = {
                ct_key: task[ct_key] for ct_key in self._CONTEST_TASK_KEY
            }

        return resp

    def task_path(self, key: str) -> Path:
        return self.json_path.parent / key / '.task.json'

    def task_dict(self, key: str) -> Dict:
        resp = self.tasks[key]
        resp['contest'] = self.code  # contest.code
        resp['key'] = key
        return resp

    def update_info(self):
        """コンテストの情報を更新する
        """
        with CookieSession() as session:
            # コンテスト情報
            try:
                contest_soup = get_soup(session, URL.contest(self.code))
            except RuntimeError:
                raise RuntimeError(f'未公開のコンテストです: {self.code}')

            contest_info = self.__scrape_contest_info(contest_soup)
            for key, value in contest_info.items():
                self.__setattr__(f'{key}', value)
            save_json(self.json_path, self.contest_dict)

            # 設問情報
            try:
                tasklist_soup = get_soup(session, URL.task(self.code))
            except RuntimeError:
                raise RuntimeError(f'未公開のコンテストです: {self.code}')

            task_info = self.__scrape_task_list(tasklist_soup)
            for key in task_info:
                if key not in self.tasks:
                    self.tasks[key] = dict()
                self.tasks[key].update(task_info[key])

            # 設問のスコア情報の追加
            score_info = self.__scrape_task_score(contest_soup)
            for key, score in score_info.items():
                if key in self.tasks:
                    self.tasks[key]['score'] = score
                else:
                    self.logger.warning(f'問題のスコア情報が不明です: {key} - {score}')

            # 設問情報を保存
            save_json(self.json_path, self.contest_dict)
            # コードファイルのテンプレート準備
            code_template = self.__fetch_init_code()
            for key in self.tasks:
                # フォルダが未作成なら作成する
                task_dir = self.task_path(key).parent
                task_dir.mkdir(exist_ok=True)
                # コードファイルも作成する
                codefile_path = task_dir.joinpath(f'{self.tasks[key]["code"]}.py')
                if not codefile_path.is_file():
                    self.__generate__code_file(codefile_path, code_template)
                # 保存
                save_json(self.task_path(key), self.task_dict(key))

    @staticmethod
    def __scrape_contest_info(soup: BeautifulSoup) -> Dict:
        """コンテストトップの情報を取得する
        """
        REG_DT_TXT = r'.*:([\d-]+\s[\d:\+]+) - ([\d-]+\s[\d:\+]+).*?$'
        datetime_text = soup.select_one('#contest-nav-tabs').select_one('small').text
        datetime_text = datetime_text.strip().replace('\n', '').replace('\t', '')
        res = re.match(REG_DT_TXT, datetime_text)
        if res is None or len(res.groups()) < 2:
            raise RuntimeError('コンテスト期間データの取得に失敗しました。開発者に確認してください')
        data = {
            'title': soup.select_one('h1').text,
            'start_dt': res.group(1),
            'end_dt': res.group(2),
        }
        return data

    @staticmethod
    def __scrape_task_list(soup: BeautifulSoup) -> Dict:
        """問題一覧を取得する
        """
        REGEX_DIFF = re.compile('^/contests/(?:.+)/tasks/(.+)$')
        task_info = dict()
        task_table = soup.select_one('#main-container').select_one('table').select_one('tbody')
        for tr in task_table.select('tr'):
            task_top = tr.select('td')[0].a
            task_key = task_top.text.strip()
            assert task_key not in task_info
            # 問題情報に追加する (task.json)
            task_info[task_key] = {
                'code': REGEX_DIFF.match(task_top['href']).group(1),
                'name': tr.select('td')[1].a.text.strip(),
                'time_limit': float(tr.select('td')[2].text.replace('sec', '').strip()),
                'memory_limit': int(tr.select('td')[3].text.replace('MB', '').strip()),
            }

        return task_info

    def __scrape_task_score(self, soup: BeautifulSoup) -> Dict:
        """トップページの配点情報を取得する
        """
        score_info = dict()
        for table in soup.select('table'):
            # 配点情報のテーブルを拾う
            if table.select_one('th').text.strip() != '問題':
                continue
            # あたり
            for task in table.select_one('tbody').select('tr'):
                _code = task.select('td')[0].text.strip()
                _score = task.select('td')[1].text.strip()
                assert _code not in score_info
                score_info[_code] = _score
            break
        else:
            self.logger.warning('スコア情報の取得に失敗しました')

        return score_info

    def __fetch_init_code(self) -> List[str]:
        """コードファイルのテンプレートを取得する
        """
        # カスタムファイルの確認
        init_file_path: Optional[Path] = None
        text_l = ['']
        try:
            cheat_dir = get_cheat_dir()
            init_file_path = cheat_dir / 'initial.py'
            if not init_file_path.is_file():
                RuntimeError
        except RuntimeError:
            self.logger.info('テンプレートが設定されていないため、空のファイルを配置しました')
        else:
            try:
                if isinstance(init_file_path, Path):
                    with init_file_path.open(mode='r', encoding=ENCODING) as rf:
                        text_l = rf.readlines()
            except Exception as e:
                self.logger.warning(f'読み込み中にエラーが発生しました [{str(init_file_path)}]:\n\t{e}')

        return text_l

    def __generate__code_file(self, target_path: Path, code_template: List[str]) -> None:
        """コードファイルを生成する
        """
        try:
            with target_path.open(mode='w', encoding=ENCODING) as wf:
                wf.writelines(code_template)
        except Exception:
            self.logger.warning(f'コードファイルの生成に失敗しました: {str(target_path)}')


def __generate_contest_dir(logger: Logger, contest_code: str) -> Contest:
    """新たにコンテストフォルダを作成する
    """
    with CookieSession() as session:
        # ログインしていることを確認する
        res = session.get(URL.SETTINGS)
        if res.url not in URL.SETTINGS:
            # ログインしていない
            raise RuntimeError('ログインしてください')

        # コンテストが存在することを確認する
        try:
            get_soup(session, URL.contest(contest_code))
        except RuntimeError:
            # 存在しない
            raise RuntimeError(f'未公開のコンテストです: {contest_code}')

    # フォルダを作成する
    current_dir = Path.cwd()

    new_dir = current_dir.joinpath(contest_code)
    try:
        new_dir.mkdir(parents=True)
    except Exception:
        raise RuntimeError(f'コンテストフォルダの作成に失敗しました: {contest_code}')

    # 保存する
    contest_info = {
        'code': contest_code,
    }
    json_path = save_json(new_dir, contest_info)
    return Contest(logger, json_path)


def load_contest(logger: Logger, argv: Sequence[str]) -> int:
    """コンテスト情報を取得し、コードファイルなどを生成する
    """
    contest_code: str = ''
    if len(argv) > 0:
        contest_code = argv[0]
        contest = __generate_contest_dir(logger, contest_code)
    else:
        contest = Contest(logger)

    # 情報の取得
    contest.update_info()
    return 0
