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
- 現在いるディレクトリにコンテストフォルダを作成する
- コンテストフォルダには問題ごとのフォルダが作成される

### 公開されたテストケースで実行する
```shell
acsh check
```
- 現在いるディレクトリの問題についてテストする

### コードを提出する
```shell
acsh submit [:lang]
```
- 現在いるディレクトリの問題のコード(main.py)を提出する
- 言語を pypy または python から選択する必要がある

