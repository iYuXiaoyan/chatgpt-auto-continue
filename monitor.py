# -*- coding: utf-8 -*-
"""监测引擎：状态轮询 + 自动发送，CLI 与托盘 GUI 共用。

用法（阻塞，CLI）：
    engine = MonitorEngine(settings)
    engine.run()

用法（后台线程，GUI）：
    engine.start()
    ...
    engine.stop()
"""
import threading
import time
import traceback

import uiautomation as auto

from chatgpt_ui import ChatGPTWindow
from keepawake import KeepAwake, keep_awake

STATE_TEXT = {
    ChatGPTWindow.STATE_LIMITED: '限额已用完，等待重置',
    ChatGPTWindow.STATE_WORKING: 'Codex 工作中',
    ChatGPTWindow.STATE_IDLE: '空闲，可发送',
}


class MonitorEngine:
    def __init__(self, settings, on_state=None, on_log=None):
        self.settings = settings
        self.on_state = on_state or (lambda state, info: None)
        self.on_log = on_log or (lambda message: None)
        self.last_sent = 0.0
        self.last_state = None
        self.not_found_rounds = 0
        self._stop_event = threading.Event()
        self._thread = None

    # ------------------------------------------------------------------ #
    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """后台线程启动。"""
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_guarded, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台线程。"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
            self._thread = None

    def run(self):
        """阻塞运行（CLI 用），直到 KeyboardInterrupt 或 stop()。"""
        self._stop_event.clear()
        self._run_guarded()

    def send_once(self):
        """立即发送一次配置文本，返回 (ok, detail)。可在任意线程调用。"""
        auto.InitializeUIAutomationInCurrentThread()
        try:
            win = ChatGPTWindow.find()
            if win is None:
                return False, 'ChatGPT window not found'
            return win.send_message(self.settings.get('send_text', '继续'))
        finally:
            try:
                auto.UninitializeUIAutomationInCurrentThread()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def _run_guarded(self):
        # uiautomation 依赖 COM，工作线程需自行初始化（主线程由库自动处理）
        auto.InitializeUIAutomationInCurrentThread()
        try:
            with KeepAwake():
                self._loop()
        finally:
            try:
                auto.UninitializeUIAutomationInCurrentThread()
            except Exception:
                pass

    def _loop(self):
        while not self._stop_event.is_set():
            keep_awake()
            try:
                self._tick()
            except Exception:
                self.on_log('unexpected error:\n' + traceback.format_exc())
            self._stop_event.wait(self.settings.get('poll_interval', 60))

    def _tick(self):
        win = ChatGPTWindow.find()
        if win is None:
            self.not_found_rounds += 1
            if self.not_found_rounds == 1 or self.not_found_rounds % 10 == 0:
                self.on_log(f'ChatGPT window not found (round {self.not_found_rounds})')
            return
        self.not_found_rounds = 0

        state, info = win.get_state()
        if state != self.last_state:
            self.on_log(f'state -> {state} {info}')
            self.on_state(state, info)
            self.last_state = state

        cooldown = self.settings.get('send_cooldown', 1800)
        if state == ChatGPTWindow.STATE_IDLE and time.time() - self.last_sent >= cooldown:
            text = self.settings.get('send_text', '继续')
            self.on_log(f'idle: sending {text!r} ...')
            ok, detail = win.send_message(text)
            if ok:
                self.last_sent = time.time()
                self.on_log(f'sent OK ({detail})')
            else:
                self.on_log(f'send failed: {detail}')
