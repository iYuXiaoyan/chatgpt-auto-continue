# -*- coding: utf-8 -*-
"""ChatGPT 桌面版窗口封装：定位窗口、判定限额/工作状态、发送消息。"""
import ctypes
import ctypes.wintypes as wt
import time

import pyperclip
import uiautomation as auto

import config

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi

SW_RESTORE = 9


def _silence_uiautomation_logger():
    """禁用 uiautomation 向 stdout 打印横幅/调试信息。

    pythonw / PyInstaller --noconsole 环境下 sys.stdout 为 None 或管道，
    其 ResetConsoleColor 里的 sys.stdout.flush() 会直接抛 OSError 杀死线程，
    必须在任何工作线程启动前静默。
    """
    try:
        noop = staticmethod(lambda *args, **kwargs: None)
        auto.Logger.Write = noop
        auto.Logger.WriteLine = noop
        auto.Logger.ColorfullyWrite = noop
    except Exception:
        pass


_silence_uiautomation_logger()


def process_image_name(pid):
    """按 pid 取进程映像路径（设备路径），失败返回空串。"""
    handle = _kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ''
    try:
        buf = ctypes.create_unicode_buffer(260)
        size = wt.DWORD(260)
        _psapi.GetProcessImageFileNameW(handle, buf, ctypes.byref(size))
        return buf.value
    finally:
        _kernel32.CloseHandle(handle)


def find_chatgpt_window():
    """按 类名 + 标题关键字 + 进程名 + 可见 找 ChatGPT 主窗口，排除同名浏览器标签页。

    注意：最小化的窗口 UIA 矩形为 0x0（如 Typora/Edge 最小化时），
    因此可见性用 win32 IsWindowVisible 判定，不能依赖 UIA 矩形尺寸。
    """
    root = auto.GetRootControl()
    for w in root.GetChildren():
        try:
            if w.ControlTypeName != 'WindowControl' or w.ClassName != config.WINDOW_CLASS:
                continue
            if config.WINDOW_NAME_KEYWORD not in (w.Name or ''):
                continue
            if not _user32.IsWindowVisible(w.NativeWindowHandle):
                continue
            image = process_image_name(w.ProcessId).lower()
            if not image.endswith(config.PROCESS_NAME.lower()):
                continue
            return w
        except Exception:
            continue
    return None


class ChatGPTWindow:
    STATE_LIMITED = 'limited'   # 限额用完
    STATE_WORKING = 'working'   # Codex 正在运行
    STATE_IDLE = 'idle'         # 空闲（可发送）

    def __init__(self, window):
        self.window = window

    @classmethod
    def find(cls):
        window = find_chatgpt_window()
        return cls(window) if window else None

    # ------------------------------------------------------------------ #
    def _walk(self, on_node, max_depth=40):
        def rec(ctrl, depth):
            if depth > max_depth:
                return
            try:
                go_on = on_node(ctrl)
            except Exception:
                go_on = True
            if not go_on:
                return
            try:
                children = ctrl.GetChildren()
            except Exception:
                return
            for ch in children:
                rec(ch, depth + 1)
        rec(self.window, 0)

    def _find_input(self):
        """底部主输入框：排除地址栏。

        最小化窗口的 UIA 矩形为 0x0，不能用窗口相对位置判断；
        地址栏位于窗口顶部（top 通常 < 100），输入框在中下部（top > 300）。
        """
        found = []

        def on_node(ctrl):
            try:
                if ctrl.ControlTypeName != 'EditControl':
                    return True
                name = ctrl.Name or ''
                if '地址' in name:
                    return True
                r = ctrl.BoundingRectangle
                if r.top > 300 and r.width() > 200:
                    found.append(ctrl)
            except Exception:
                pass
            return True

        self._walk(on_node)
        return found[0] if found else None

    def get_state(self):
        """返回 (state, info)。state ∈ limited / working / idle。"""
        limit_hits, working_hits = [], []
        working_button = False

        def on_node(ctrl):
            nonlocal working_button
            try:
                ctype = ctrl.ControlTypeName
                name = ctrl.Name or ''
                if ctype in ('TextControl', 'EditControl', 'DocumentControl'):
                    for kw in config.LIMIT_KEYWORDS:
                        if kw in name:
                            limit_hits.append(name[:80])
                            return True
                    for kw in config.WORKING_KEYWORDS:
                        if kw in name:
                            working_hits.append(name[:80])
                            return True
                elif ctype == 'ButtonControl':
                    for kw in config.WORKING_BUTTON_NAMES:
                        if kw in name:
                            working_button = True
                            return True
            except Exception:
                pass
            return True

        self._walk(on_node)
        input_box = self._find_input()

        if limit_hits:
            state = self.STATE_LIMITED
        elif working_hits or working_button:
            state = self.STATE_WORKING
        else:
            state = self.STATE_IDLE

        info = {
            'limit_hits': limit_hits,
            'working_hits': working_hits,
            'working_button': working_button,
            'input_found': input_box is not None,
        }
        return state, info

    # ------------------------------------------------------------------ #
    def _ensure_visible(self):
        hwnd = self.window.NativeWindowHandle
        if _user32.IsIconic(hwnd):
            _user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.5)

    def _find_send_button(self, edit):
        """输入后查找发送按钮（输入框右侧、名字含 发送/send）。找不到返回 None。"""
        er = edit.BoundingRectangle
        found = []

        def on_node(ctrl):
            try:
                if ctrl.ControlTypeName == 'ButtonControl':
                    name = ctrl.Name or ''
                    r = ctrl.BoundingRectangle
                    if ('发送' in name or 'send' in name.lower()) \
                            and r.left >= er.right - 80 and abs(r.top - er.top) <= 150:
                        found.append(ctrl)
            except Exception:
                pass
            return True

        self._walk(on_node)
        return found[0] if found else None

    def send_message(self, text):
        """聚焦输入框 -> 清空 -> 粘贴 -> 点发送（找不到按钮则回车）。返回 (ok, detail)。"""
        try:
            self._ensure_visible()
        except Exception:
            pass
        edit = self._find_input()
        if edit is None:
            return False, 'input box not found'
        try:
            edit.SetFocus()
            time.sleep(0.2)
            edit.Click(simulateMove=False)
            time.sleep(0.3)
            auto.SendKeys('{Ctrl}a')
            time.sleep(0.2)
            pyperclip.copy(text)
            auto.SendKeys('{Ctrl}v')
            time.sleep(0.5)
            send_btn = self._find_send_button(edit)
            if send_btn is not None:
                send_btn.Click(simulateMove=False)
                return True, 'clicked send button'
            auto.SendKeys('{Enter}')
            return True, 'pressed Enter (no send button found)'
        except Exception as e:
            return False, f'{type(e).__name__}: {e}'
