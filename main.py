# -*- coding: utf-8 -*-
"""chatgpt-auto-continue 命令行入口。

用法：
    python main.py loop   # 整夜循环监测（默认）
    python main.py once   # 立即发送一次后退出
"""
import sys

import config
from applog import setup_logging
from monitor import MonitorEngine


def main(mode='loop'):
    log = setup_logging()
    settings = config.load_settings()
    log.info('started: mode=%s poll=%ss cooldown=%ss text=%r',
             mode, settings['poll_interval'], settings['send_cooldown'], settings['send_text'])

    engine = MonitorEngine(settings, on_log=log.info)
    if mode == 'once':
        ok, detail = engine.send_once()
        log.info('sent=%s (%s)', ok, detail)
        return 0 if ok else 1
    try:
        engine.run()
    except KeyboardInterrupt:
        log.info('interrupted, exit')
    return 0


if __name__ == '__main__':
    run_mode = sys.argv[1] if len(sys.argv) > 1 else 'loop'
    if run_mode not in ('once', 'loop'):
        print('usage: python main.py [once|loop]')
        sys.exit(2)
    sys.exit(main(run_mode))
