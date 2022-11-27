from pathlib import Path
import sys

from setuptools import setup


TARGET_DIR = Path(__file__).parent / 'src'
sys.path.insert(0, TARGET_DIR)

setup()
