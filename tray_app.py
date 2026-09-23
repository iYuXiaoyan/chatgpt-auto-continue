# -*- coding: utf-8 -*-
"""托盘应用程序入口（双击 / 开机自启 / 打包为 exe 后的主程序）。

右键托盘图标：查看状态、开始/停止监测、立即发送一次、设置、打开日志、退出。
"""
import logging
import sys
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw

import config
from applog import setup_logging
from monitor import MonitorEngine, STATE_TEXT
from paths import APP_DIR
from version import __version__

APP_NAME = f'ChatGPT Auto Continue v{__version__}'
PROJECT_URL = 'https://github.com/iYuXiaoyan/chatgpt-auto-continue'

STATE_COLORS = {
    'stopped': (120, 120, 120),
    'limited': (230, 145, 56),
    'working': (46, 160, 90),
    'idle': (64, 130, 230),
}


def make_icon(color):
    """画一个圆角方块 + 白色「继续」三角箭头作为托盘图标。"""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, size - 2, size - 2], radius=14, fill=color + (255,))
    # 白色右向三角（▶），寓意「继续」
    tri = [(24, 20), (24, 44), (46, 32)]
    draw.polygon(tri, fill=(255, 255, 255, 255))
    return img


class TrayApp:
    def __init__(self):
        self.log = setup_logging(console=False)
        self.settings = config.load_settings()
        self.engine = MonitorEngine(self.settings,
                                    on_state=self._on_state,
                                    on_log=self.log.info)
        self._current_state = None
        menu = pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self._toggle_text, self._toggle),
            pystray.MenuItem('立即发送一次', self._send_once),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('设置...', self._open_settings),
            pystray.MenuItem('打开日志文件夹', self._open_logs),
            pystray.MenuItem('项目主页', lambda: webbrowser.open(PROJECT_URL)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('退出', self._quit),
        )
        self.icon = pystray.Icon('chatgpt-auto-continue',
                                 make_icon(STATE_COLORS['stopped']),
                                 APP_NAME, menu)
        self.log.info('tray app started v%s, auto_start=%s',
                      __version__, self.settings.get('auto_start', True))
        if self.settings.get('auto_start', True):
            self.engine.start()

    # ---------------- 托盘回调 ---------------- #
    def _status_text(self, item):
        if not self.engine.running:
            return f'{APP_NAME} | 已停止'
        text = STATE_TEXT.get(self._current_state, '检测中…')
        return f'{APP_NAME} | {text}'

    def _toggle_text(self, item):
        return '停止监测' if self.engine.running else '开始监测'

    def _toggle(self, icon, item):
        if self.engine.running:
            self.engine.stop()
            self.log.info('monitor stopped by user')
        else:
            self.engine.start()
            self.log.info('monitor started by user')
        self._refresh_icon()

    def _send_once(self, icon, item):
        def worker():
            self.log.info('manual send requested')
            ok, detail = self.engine.send_once()
            self.log.info('manual send: ok=%s (%s)', ok, detail)
        threading.Thread(target=worker, daemon=True).start()

    def _open_logs(self, icon, item):
        threading.Thread(
            target=lambda: __import__('os').startfile(APP_DIR / config.LOG_DIR),
            daemon=True).start()

    def _open_settings(self, icon, item):
        threading.Thread(target=self._settings_dialog, daemon=True).start()

    def _quit(self, icon, item):
        self.log.info('tray app exiting')
        self.engine.stop()
        self.icon.stop()

    # ---------------- 状态展示 ---------------- #
    def _on_state(self, state, info):
        self._current_state = state
        self._refresh_icon()

    def _refresh_icon(self):
        if not self.engine.running:
            color, text = STATE_COLORS['stopped'], '已停止'
        else:
            color = STATE_COLORS.get(self._current_state or 'idle')
            text = STATE_TEXT.get(self._current_state, '检测中')
        self.icon.icon = make_icon(color)
        self.icon.title = f'{APP_NAME} - {text}'

    # ---------------- 设置窗口 ---------------- #
    def _settings_dialog(self):
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title(f'设置 - {APP_NAME}')
        root.resizable(False, False)
        root.attributes('-topmost', True)

        pad = {'padx': 10, 'pady': 6}
        frm = ttk.Frame(root)
        frm.grid(**pad)

        ttk.Label(frm, text='轮询间隔（秒）').grid(row=0, column=0, sticky='w', **pad)
        var_interval = tk.StringVar(value=str(self.settings['poll_interval']))
        ttk.Entry(frm, textvariable=var_interval, width=12).grid(row=0, column=1, sticky='e', **pad)

        ttk.Label(frm, text='发送冷却期（秒）').grid(row=1, column=0, sticky='w', **pad)
        var_cooldown = tk.StringVar(value=str(self.settings['send_cooldown']))
        ttk.Entry(frm, textvariable=var_cooldown, width=12).grid(row=1, column=1, sticky='e', **pad)

        ttk.Label(frm, text='自动发送内容').grid(row=2, column=0, sticky='w', **pad)
        var_text = tk.StringVar(value=self.settings['send_text'])
        ttk.Entry(frm, textvariable=var_text, width=12).grid(row=2, column=1, sticky='e', **pad)

        var_auto = tk.BooleanVar(value=bool(self.settings.get('auto_start', True)))
        ttk.Checkbutton(frm, text='启动后自动开始监测', variable=var_auto) \
            .grid(row=3, column=0, columnspan=2, sticky='w', **pad)

        msg = ttk.Label(frm, text='', foreground='red')
        msg.grid(row=4, column=0, columnspan=2)

        def save():
            try:
                interval = int(var_interval.get())
                cooldown = int(var_cooldown.get())
                assert interval >= 10 and cooldown >= 0
            except (ValueError, AssertionError):
                msg.config(text='请输入合法数字（间隔 ≥ 10 秒）')
                return
            self.settings.update({
                'poll_interval': interval,
                'send_cooldown': cooldown,
                'send_text': var_text.get() or '继续',
                'auto_start': bool(var_auto.get()),
            })
            config.save_settings(self.settings)
            self.log.info('settings saved: %s', self.settings)
            root.destroy()

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text='保存', command=save).pack(side='left', padx=6)
        ttk.Button(btns, text='取消', command=root.destroy).pack(side='left', padx=6)

        root.mainloop()

    # ---------------- 运行 ---------------- #
    def run(self):
        self.icon.run()


def main():
    TrayApp().run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
