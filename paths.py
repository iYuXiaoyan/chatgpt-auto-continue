# -*- coding: utf-8 -*-
"""应用目录解析：源码运行时取脚本目录，PyInstaller 打包后取 exe 所在目录。"""
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent
