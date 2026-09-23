# -*- coding: utf-8 -*-
"""运行期间阻止系统睡眠（标准库 ctypes 实现）。

用法：
    with KeepAwake():
        main_loop()
或在循环中周期性调用 keep_awake()。
"""
import ctypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

_kernel32 = ctypes.windll.kernel32


class KeepAwake:
    """进入时阻止系统睡眠，退出时恢复默认电源策略。"""

    def __enter__(self):
        keep_awake()
        return self

    def __exit__(self, *exc):
        allow_sleep()
        return False


def keep_awake():
    """告知系统当前线程需要系统保持运行状态（每次轮询时续期）。"""
    _kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


def allow_sleep():
    """恢复默认电源管理。"""
    _kernel32.SetThreadExecutionState(ES_CONTINUOUS)
