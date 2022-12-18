from pathlib import Path
import subprocess

from setuptools import setup

# チートシートフォルダの作成はシェルで行う
tgt_file = Path(__file__).parent / 'setup.sh'
subprocess.run(f'chmod 755 {str(tgt_file)}'.split())
subprocess.run(str(tgt_file))

setup()
