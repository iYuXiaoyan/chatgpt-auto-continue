# -*- coding: utf-8 -*-
"""chatgpt-auto-continue 配置项"""

# --- 窗口定位 ---
WINDOW_CLASS = 'Chrome_WidgetWin_1'      # ChatGPT 桌面版窗口类名
WINDOW_NAME_KEYWORD = 'ChatGPT'          # 窗口标题包含此关键字
PROCESS_NAME = 'ChatGPT.exe'             # 进程名（排除同标题的浏览器标签页）

# --- 轮询与发送 ---
POLL_INTERVAL = 60           # 轮询间隔（秒）
SEND_TEXT = '继续'           # 自动发送的内容
SEND_COOLDOWN = 1800         # 两次自动发送的最小间隔（秒），防止刷屏

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

# --- 日志 ---
LOG_DIR = 'logs'
