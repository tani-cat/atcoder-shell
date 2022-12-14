from logging import Logger
from pathlib import Path
import re
from typing import Dict, Sequence

from bs4 import BeautifulSoup

from ..exceptions import ACShellException
from ..utils import CookieSession, URL, get_soup, save_json, search_json, load_json

from .task import fetch_task


REG_DT = re.compile(r'.*:([\d-]+\s[\d:\+]+) - ([\d-]+\s[\d:\+]+).*?$')


def __scrape_contest_info(contest_code: str, soup: BeautifulSoup) -> Dict:
    """コンテストトップの情報を取得する
    """
    datetime_text = soup.select_one('#contest-nav-tabs').select_one('small').text
    datetime_text = datetime_text.strip().replace('\n', '').replace('\t', '')
    res = REG_DT.match(datetime_text)
    if res is None or len(res.groups()) < 2:
        raise RuntimeError('Failed to get contest period data by site resource changes')
    data = {
        'code': contest_code,
        'title': soup.select_one('h1').text,
        'start_dt': res.group(1),
        'end_dt': res.group(2),
        'tasks': dict(),
    }
    return data


def __fetch_contest_info(contest_code: str) -> Dict:
    """新たにコンテストフォルダを作成する
    """
    # 上位コンテストフォルダでないことを確認する
    if search_json() is not None:
        raise RuntimeError('Current directory is in the contest directory')

    with CookieSession() as session:
        # ログインしていることを確認する
        res = session.get(URL.SETTINGS)
        if res.url not in URL.SETTINGS:
            # ログインしていない
            raise RuntimeError('not logged in')

        # コンテストが存在することを確認する
        try:
            soup = get_soup(session, URL.contest(contest_code))
        except ACShellException:
            # 存在しない
            raise RuntimeError(f'unpublished contest: {contest_code}')

        # フォルダを作成する
        current_dir = Path.cwd()
        new_dir = current_dir.joinpath(contest_code)
        try:
            new_dir.mkdir(parents=True)
        except Exception:
            raise RuntimeError(f'Failed to make contest directory: {contest_code}')

        contest_info = __scrape_contest_info(contest_code, soup)
        # 保存する
        json_path = save_json(new_dir, contest_info)

    return json_path, contest_info


def load_contest(logger: Logger, argv: Sequence[str]) -> int:
    """コンテスト情報を取得し、コードファイルなどを生成する
    """
    contest_code: str = ''
    contest_info: Dict = dict()
    if len(argv) > 0:
        contest_code = argv[0]
        json_path, contest_info = __fetch_contest_info(contest_code)
        logger.info('Contest info saved')
    else:
        # コンテストフォルダにいるどうかを確認する
        json_path = search_json()
        if json_path is None:
            raise RuntimeError('Not in contest directory')
        contest_info = load_json(json_path)
        logger.info('Contest info checked')

    # 問題情報を取得できるなら問題情報を取得
    fetch_task(logger, json_path, contest_info)
    return 0
