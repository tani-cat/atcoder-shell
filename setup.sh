#! /bin/sh
# チートシートフォルダの作成と環境変数の追加を行う
# インストール時に実行される
# フォルダを作成する
cheat_dir="${HOME%/}/.acshell"
if [[ ! -d $cheat_dir ]]; then
    mkdir $cheat_dir
fi
# 環境変数を追加する処理を現在のシェルの設定ファイルに追記する
# 現在のシェルを取得
current_shell=${SHELL##*/}
# この時点で環境変数が存在しない場合のみ追記を行う
if [[ -z ${ACSHELL_PATH} ]]; then
    # 現在のシェルの設定ファイルが存在しなければ作成する
    config_path="${HOME%/}/.${current_shell}rc"
    if [[ ! -e $config_path ]]; then
      touch $config_path
    fi
    # 環境変数の定義を追加する
    echo "" >> $config_path
    echo "# For atcoder-shell" >> $config_path
    echo "export ACSHELL_PATH=\"${cheat_dir}\"" >> $config_path
fi
echo "environment path has been appended"
