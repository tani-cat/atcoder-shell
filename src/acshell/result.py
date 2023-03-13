from logging import Logger
import re
from typing import Dict, List, Sequence

from bs4.element import Tag
from tabulate import tabulate

from .contest.contest import Contest
from .utils import get_soup, search_contest_json, CookieSession, URL


def _add_judge_color(judge: str) -> str:
    """判定結果のテキスト出力に色をつける"""
    if judge == 'AC':
        # 緑
        return f'\033[32m{judge}\033[0m'
    elif judge in ('WA', 'TLE', 'MLE', 'CE', 'OLE', 'IE', 'RE'):
        # 黄色
        return f'\033[33m{judge}\033[0m'


def _get_submission(logger: Logger, contest: Contest, page_limit: int = 50):
    """提出結果を取得する"""
    tr_l: List[Tag] = []
    with CookieSession() as session:
        for page in range(1, page_limit + 1):
            try:
                soup = get_soup(session, URL.result(str(contest), page=page))
            except RuntimeError:
                raise RuntimeError(f'ページの取得に失敗しました: {contest}, page={page}')

            table = soup.select_one('table')
            if table is None:
                # ページにコンテンツなし
                break
            tbody = table.select_one('tbody')
            tr_l.extend(tbody.select('tr'))
        else:
            if len(tr_l) == 1000:
                logger.warning('1000件以上の提出が見つかったため、取得を打ち切りました')

    # regex
    REG_TITLE = re.compile('(.+) - .*')
    result_l: List[Dict] = []
    for tr in tr_l:
        result_l.append({
            'key': REG_TITLE.match(tr.select('td')[1].a.text).groups()[0],
            'submit_time': tr.select('td')[0].find('time').text[:-5],
            'lang': tr.select('td')[3].a.text,
            'score': tr.select('td')[4].text,
            'judge': _add_judge_color(tr.select('td')[6].find('span').text),
            'time': '',
            'memory': '',
        })
        if 'WJ' not in result_l[-1]['judge'] and '/' not in result_l[-1]['judge']:
            # 判定結果が出ている場合は時間とメモリの情報も追加する
            result_l[-1]['time'] = tr.select('td')[7].text
            result_l[-1]['memory'] = tr.select('td')[8].text

    return result_l


def recent_result(logger: Logger, argv: Sequence[str]) -> int:
    """直近の提出結果を取得する
    """
    contest_json = search_contest_json()
    contest = Contest(logger, contest_json)
    result_l = _get_submission(logger, contest, page_limit=1)
    HEADER_INFO = {
        'key': '問題',
        'submit_time': '提出時刻',
        'lang': '言語',
        'judge': '結果',
        'time': '実行時間',
        'memory': 'メモリ',
    }
    data_l = [[res[k] for k in HEADER_INFO.keys()] for res in result_l]
    print(tabulate(data_l, HEADER_INFO.values(), 'github'))
    return 0


def status(logger: Logger, argv: Sequence[str]) -> int:
    """コンテストの得点状況を取得する"""
    contest_json = search_contest_json()
    contest = Contest(logger, contest_json)
    # REG_WA: これに引っかからない判定結果をペナルティ扱いする
    REG_WA = re.compile('.*(AC|WJ|CE|WR|IE).*')
    wa_cnt = {key: 0 for key in contest.tasks.keys()}
    data_d = {
        key: {
            'key': key,
            'submit_time': None,
            'score': 0,
            'lang': '',
            'judge': '',
            'time': '',
            'memory': '',
        } for key in contest.tasks.keys()
    }
    # 結果を取得し、新しい順に処理する
    result_l = _get_submission(logger, contest)
    for result in result_l:
        _key = result['key']
        if _key not in data_d:
            continue
        if data_d[_key]['submit_time'] is None or 'AC' in result['judge']:
            # 最新の提出結果 or より古いACの結果 -> 上書きする
            data_d[_key] = result
            wa_cnt[_key] = 0
        if data_d[_key]['submit_time'] is not None and REG_WA.match(result['judge']) is None:
            # すでに提出記録があり、ペナルティ対象の場合
            wa_cnt[_key] += 1

    # data_d[key]: 最新の提出結果か、最古のACの結果が格納されている
    # wa_cnt[key]: 最新の提出結果か、最古のACの結果から以前のペナルティ数(その結果のペナを含む)
    tot_wa = sum(wa_cnt.values())
    tot_score = 0
    for key in data_d.keys():
        data_d[key]['penalty'] = wa_cnt[key]
        data_d[key]['name'] = contest.tasks[key]
        tot_score += int(data_d[key]['score'])

    HEADER_INFO = {
        'key': '問題',
        'submit_time': '提出時刻',
        'lang': '言語',
        'judge': '結果',
        'score': '得点',
        'penalty': 'ペナ数',
    }
    out_l = [[res[k] for k in HEADER_INFO.keys()] for res in data_d.values()]
    print(tabulate(out_l, HEADER_INFO.values(), 'github'))
    print(f'合計得点: {tot_score} (合計ペナルティ: {tot_wa})')
    return 0
