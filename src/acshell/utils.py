import http
import json
from pathlib import Path
from typing import Dict, Optional

import appdirs
from bs4 import BeautifulSoup
import requests

from src.acshell.exceptions import ACShellException


ENCODING = 'utf-8'
JSON_NAME = '.contest.json'
user_data_dir = Path(appdirs.user_data_dir('acshell'))
user_cache_dir = Path(appdirs.user_cache_dir('acshell'))
cookie_path = user_data_dir / 'cookie.jar'



def load_json(json_path: Optional[Path] = None) -> Dict:
    """.contest.jsonを読み込む
    """
    if json_path is None:
        current_dir = Path.cwd()
        json_path = current_dir / JSON_NAME
    
    assert json_path.name == JSON_NAME
    if json_path.exists():
        with json_path.open(encoding=ENCODING) as f:
            data = json.load(f)
    else:
        raise RuntimeError

    return data


def save_json(json_path: Path, data: Dict) -> Path:
    """.contest.jsonに書き込む
    """
    try:
        if json_path.is_dir():
            json_path = json_path / JSON_NAME
        with json_path.open(mode='w', encoding=ENCODING) as f:
            json.dump(data, f)
    except Exception:
        raise RuntimeError(f'Failed to save contest info: {json_path.parent}') 

    return json_path


def search_json() -> Optional[Path]:
    """上位ディレクトリにcontest.jsonがあるかどうかを調べる
    """
    cur_dir = Path.cwd()
    root_dir = Path(cur_dir.root)
    while cur_dir != root_dir:
        try:
            json_path = cur_dir / JSON_NAME
            if json_path.is_file():
                return json_path

            cur_dir = cur_dir.parent
        except Exception:
            break

    return None


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url)
    if response.status_code != 200:
        raise ACShellException
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


class URL:
    """URLを格納する
    """

    BASE = 'https://atcoder.jp/'
    LOGIN = BASE + 'login'
    SETTINGS = BASE + 'settings'

    @classmethod
    def contest(cls, contest: str) -> str:
        return cls.BASE + 'contests/' + contest

    @classmethod
    def task(cls, contest: str, task: str = None) -> str:
        _res = cls.contest(contest) + '/tasks'
        if isinstance(task, str):
            return _res + '/' + task

        return _res


class CookieSession(requests.Session):
    """コマンドごとに認証情報入りのセッションを生成する

    refs: https://github.com/online-judge-tools/api-client/blob/8529981e570c231770ac2347270623d29c9b14f9/onlinejudge/utils.py#L44
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Cookieの設定
        self.cookies: requests.models.cookies.RequestsCookieJar = \
            http.cookiejar.LWPCookieJar(str(cookie_path))
        if cookie_path.exists():
            self.cookies.load(ignore_discard=True)
        self.cookies.clear_expired_cookies()
        # ログインのフラグ設定
        self.is_logined: Optional[bool] = None
        self.get(URL.SETTINGS)
    
    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        self.cookies.save(ignore_discard=True)
        cookie_path.chmod(0o600)
        return super().__exit__(exc_type, exc_value, traceback)
    
    def quit(self) -> None:
        self.__exit__(None, None, None)
    
    def request(self, *args, **kwargs):
        """レスポンスを読んでログインしているかどうかを確認する
        """
        # 有効期限の切れたCookieを破棄する
        self.cookies.clear_expired_cookies()
        # 処理を行う
        response = super().request(*args, **kwargs)
        # ログイン状態にあるかどうかを確認する
        if URL.LOGIN in response.url:
            self.is_logined = False
        else:
            self.is_logined = True
        
        return response
