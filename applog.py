# -*- coding: utf-8 -*-
"""统一日志：文件（logs/ 目录，按天滚动）+ 可选控制台。"""
import logging
from datetime import datetime
from pathlib import Path

import config
from paths import APP_DIR


def setup_logging(console=True):
    log_dir = APP_DIR / config.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    logfile = log_dir / f'auto_continue_{datetime.now():%Y%m%d}.log'
    handlers = [logging.FileHandler(logfile, encoding='utf-8')]
    if console:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=handlers,
        force=True,
    )
    # comtypes 的代码生成日志很吵，只保留警告以上
    logging.getLogger('comtypes').setLevel(logging.WARNING)
    return logging.getLogger('auto-continue')
