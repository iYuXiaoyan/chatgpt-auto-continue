# -*- coding: utf-8 -*-
"""chatgpt-auto-continue 默认配置与运行期设置读写。

优先级：settings.json（应用目录） > 本文件中的默认值。
"""
import json

from paths import APP_DIR

# --- 窗口定位 ---
WINDOW_CLASS = 'Chrome_WidgetWin_1'      # ChatGPT 桌面版窗口类名
WINDOW_NAME_KEYWORD = 'ChatGPT'          # 窗口标题包含此关键字
PROCESS_NAME = 'ChatGPT.exe'             # 进程名（排除同标题的浏览器标签页）

# --- 状态判定 ---
# 命中任一即视为「限额用完」
LIMIT_KEYWORDS = (
    '你已达到使用上限',
    '使用上限',
    "You've reached your limit",
    'reached your current usage limit',
)
# 命中任一即视为「正在工作」（此时不发送）
WORKING_KEYWORDS = ('正在思考', '正在运行', '处理中')
WORKING_BUTTON_NAMES = ('停止', 'Stop', 'stop')

# --- 默认值 ---
DEFAULT_SETTINGS = {
    'poll_interval': 60,        # 轮询间隔（秒）
    'send_text': '继续',        # 自动发送的内容
    'send_cooldown': 1800,      # 两次自动发送的最小间隔（秒），防止刷屏
    'auto_start': True,         # 托盘程序启动后是否自动开始监测
}

SETTINGS_FILE = 'settings.json'
LOG_DIR = 'logs'


def load_settings():
    """读取应用目录下的 settings.json，缺失或损坏时返回默认值。"""
    settings = dict(DEFAULT_SETTINGS)
    path = APP_DIR / SETTINGS_FILE
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            for key in settings:
                if key in data and isinstance(data[key], type(settings[key])):
                    settings[key] = data[key]
        except Exception:
            pass
    return settings


def save_settings(settings):
    """把运行设置写回 settings.json。"""
    path = APP_DIR / SETTINGS_FILE
    data = {key: settings.get(key, DEFAULT_SETTINGS[key]) for key in DEFAULT_SETTINGS}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
