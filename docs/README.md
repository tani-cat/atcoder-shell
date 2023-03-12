# AtCoder Shell

## How to use

### インストール方法

```shell
pip install acshell
```

### ログインする

```shell
acsh login
```

- ログインする
- ログイン情報は一定期間保持される

### コンテストフォルダを作成する

```shell
acsh load agc001
```

- 現在いるフォルダにコンテストフォルダを作成する
- コンテストフォルダには問題ごとのフォルダが作成される

### 公開されたテストケースで実行する

```shell
acsh check [:task] [:lang]
```

- [task]: (必須)問題の記号（A、Bなど）を指定
- [lang]: (任意)実行言語を指定

### コードを提出する

```shell
acsh submit [:task] [:lang]
```

- 現在いるフォルダの問題のコード(main.py)を提出する
- 言語を pypy または python から選択する必要がある

- [task]: (必須)問題の記号（A、Bなど）を指定
- [lang]: (必須)実行言語を指定
