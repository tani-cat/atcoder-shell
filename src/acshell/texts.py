"""表示テキストなどを格納する
"""
HELP_TEXT = {
    'help': {
        'short': 'h',
        'args': '',
        'text': 'コマンド一覧を表示する',
    },
    'login': {
        'short': 'lg',
        'args': '',
        'text': 'サイトにログインする',
    },
    'load': {
        'short': 'ld',
        'args': '<contest_name>',
        'text': '<contest_name> のフォルダを現在のディレクトリに作成し、テストケースなどを取得する'
    },
    'test': {
        'short': 't',
        'args': '<task_code> <test_num> [lang]',
        'text': '問題 <task_code> のテストケース <test_num> を [lang] で実行する'
    },
    'check': {
        'short': 'c',
        'args': '<task_code> [lang]',
        'text': '問題 <task_code> のテストケースを [lang] で実行する'
    },
    'submit': {
        'short': 's',
        'args': '<task_code> <lang>',
        'text': '問題 <task_code> のコードを <lang> で提出する'
    },
    'recent': {
        'short': 'rc',
        'args': '',
        'text': 'コンテストへの直近の提出結果を取得する'
    },
    'status': {
        'short': 'rs',
        'args': '',
        'text': 'コンテストでの得点状況を取得する'
    },
    'edit-cheat': {
        'short': 'ec',
        'args': '',
        'text': 'チートシートのフォルダを開く'
    },
    'add-cheat': {
        'short': 'ac',
        'args': '<task_code> <cheatsheet_name>',
        'text': 'チートシート <cheatsheet_name> を問題 <task_code> のフォルダに追加する'
    },
    'list-cheat': {
        'short': 'lc',
        'args': '',
        'text': 'チートシートの一覧を表示する'
    }
}
