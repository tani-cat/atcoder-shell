from logging import Logger
import re
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

from ..exceptions import ACShellException
from ..utils import get_soup, CookieSession, URL, save_json


REGEX_DIFF = re.compile('^/contests/(?:.+)/tasks/(.+)$')
REGEX_TITLE = re.compile('(.+) - .*')


def __scrape_testcase(session, contest_code: str, task_code: str) -> Dict:
    """問題のテストケースを取得する
    """
    try:
        soup = get_soup(session, URL.task(contest_code, task_code))
    except ACShellException:
        raise RuntimeError(f'Failed to scrape testcase: {contest_code} - {task_code}')
    
    testcase_l: List[Dict] = []
    for part in soup.select_one('#task-statement').select('.part'):
        part_title = part.select_one('h3').text[:3]
        if part_title == '入力例':
            testcase_l.append(dict())
            testcase_l[-1]['input'] = part.select_one('pre').text.replace('\r', '')
        elif part_title == '出力例':
            testcase_l[-1]['output'] = part.select_one('pre').text.replace('\r', '')

    return testcase_l


def __scrape_task_list(soup: BeautifulSoup) -> Dict:
    """問題一覧を取得する
    """
    task_dict = dict()
    task_table = soup.select_one('#main-container').select_one('table').select_one('tbody')
    for tr in task_table.select('tr'):
        task_top = tr.select('td')[0].a
        task_key = task_top.text.strip()
        assert task_key not in task_dict
        task_dict[task_key] = {
            'code': REGEX_DIFF.match(task_top['href']).group(1),
            'name': tr.select('td')[1].a.text.strip(),
            'time_limit': float(tr.select('td')[2].text.replace('sec', '').strip()),
            'memory_limit': int(tr.select('td')[3].text.replace('MB', '').strip()),
            'testcases': [],
        }

    return task_dict


def fetch_task(logger: Logger, json_path: Path, contest_info: Dict):
    """コンテスト内の問題を取得する
    """
    contest_code = contest_info['code']
    with CookieSession() as session:
        try:
            soup = get_soup(session, URL.task(contest_code))
        except ACShellException:
            # 非公開
            raise RuntimeError(f'contest tasks are unpublished: {contest_code}')
        
        # 問題一覧の取得
        task_list = __scrape_task_list(soup)
        contest_info['tasks'] = task_list
        save_json(json_path, contest_info)
        logger.info('task list appended')
        # テストケースの取得 & フォルダとコードファイルの生成
        base_dir = json_path.parent
        for task_key, task_info in contest_info['tasks'].items():
            # フォルダとファイルの作成
            task_dir: Path = base_dir / task_key
            task_dir.mkdir(exist_ok=True)
            # TODO: ファイルの作成
            # テストケースの作成
            testcase_l = __scrape_testcase(session, contest_code, task_info['code'])
            contest_info['tasks'][task_key]['testcases'] = testcase_l
        
        save_json(json_path, contest_info)
        logger.info('task testcases appended')
