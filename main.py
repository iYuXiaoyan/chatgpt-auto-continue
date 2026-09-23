# -*- coding: utf-8 -*-
"""chatgpt-auto-continue 主循环。

用法：
    python main.py loop   # 整夜循环监测（默认）
    python main.py once   # 空闲发送一次后退出
"""
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import config
from chatgpt_ui import ChatGPTWindow
from keepawake import KeepAwake, keep_awake


def setup_logging():
    log_dir = Path(__file__).resolve().parent / config.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    logfile = log_dir / f'auto_continue_{datetime.now():%Y%m%d}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(logfile, encoding='utf-8'),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return logging.getLogger('auto-continue')


def main(mode='loop'):
    log = setup_logging()
    log.info('started: mode=%s poll=%ss cooldown=%ss text=%r',
             mode, config.POLL_INTERVAL, config.SEND_COOLDOWN, config.SEND_TEXT)
    last_sent = 0.0
    last_state = None
    not_found_rounds = 0

    with KeepAwake():
        while True:
            keep_awake()
            try:
                win = ChatGPTWindow.find()
                if win is None:
                    not_found_rounds += 1
                    if not_found_rounds == 1 or not_found_rounds % 10 == 0:
                        log.warning('ChatGPT window not found (round %d)', not_found_rounds)
                    time.sleep(config.POLL_INTERVAL)
                    continue
                not_found_rounds = 0

                state, info = win.get_state()
                if state != last_state:
                    log.info('state -> %s %s', state, info)
                    last_state = state

                if state == ChatGPTWindow.STATE_IDLE and time.time() - last_sent >= config.SEND_COOLDOWN:
                    log.info('idle: sending %r ...', config.SEND_TEXT)
                    ok, detail = win.send_message(config.SEND_TEXT)
                    if ok:
                        last_sent = time.time()
                        log.info('sent OK (%s)', detail)
                    else:
                        log.error('send failed: %s', detail)
                    if mode == 'once':
                        log.info('once mode: exit')
                        return 0 if ok else 1

                time.sleep(config.POLL_INTERVAL)
            except KeyboardInterrupt:
                log.info('interrupted, exit')
                return 0
            except Exception:
                log.error('unexpected error:\n%s', traceback.format_exc())
                time.sleep(config.POLL_INTERVAL)


if __name__ == '__main__':
    run_mode = sys.argv[1] if len(sys.argv) > 1 else 'loop'
    if run_mode not in ('once', 'loop'):
        print('usage: python main.py [once|loop]')
        sys.exit(2)
    sys.exit(main(run_mode))
