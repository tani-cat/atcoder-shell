from getpass import getpass
import logging
from typing import Sequence

from bs4 import BeautifulSoup

from .utils import CookieSession, URL


def login(logger: logging.Logger, argv: Sequence[str]) -> bool:
    """ログイン処理を実行する
    """
    username = input('Username: ')
    password = getpass()
    # アクセスする
    with CookieSession() as session:
        if '-f' in argv:
            # 強制ログアウト: ログアウトのURLがないので、Cookieを破棄する
            session.cookies.clear()
        get_res = session.get(URL.LOGIN)
        soup = BeautifulSoup(get_res.text, 'lxml')
        _container = soup.select_one('#main-container')
        csrf_token = _container.find('input', attrs={'name': 'csrf_token'})['value']
        data = {
            'username': username,
            'password': password,
            'csrf_token': csrf_token,
        }
        post_res = session.post(URL.LOGIN, data=data)
        if post_res.status_code == 200 and 'login' not in post_res.url:
            # ログイン成功してトップページにリダイレクトしたとき
            logger.info('ログインに成功しました')
            return 0

        soup = BeautifulSoup(post_res.text, 'lxml')
        _container = soup.select_one('#main-container')
        error_text = _container.select_one('.alert').text.strip().replace('×\n ', '')
        raise RuntimeError(f'ログインに失敗しました: {error_text}')
