# chatgpt-auto-continue

ChatGPT 桌面版「5 小时限额重置后自动发送『继续』」小工具。挂在后台轮询窗口状态：限额期静默等待；发现空闲且过了冷却期就自动粘贴「继续」并发送，让 Codex 整夜持续推进。

## 原理

- 通过 UIA（`uiautomation` 库）按 窗口类名 + 标题 + 进程名（`ChatGPT.exe`）定位窗口，每分钟读取一次界面文本与控件状态。
- **状态机**：
  - `limited`：界面出现「你已达到使用上限」类字样 → 只记录，不动作；
  - `working`：出现「正在思考 / 处理中 / 停止按钮」→ 说明 Codex 在干活，不打扰；
  - `idle`：以上都不是 → 距上次自动发送超过 `SEND_COOLDOWN`（默认 1800 秒）就发送一次「继续」。
- 发送路径：聚焦输入框 → Ctrl+A 清空 → 剪贴板粘贴（`pyperclip` + Ctrl+V，兼容中文）→ 优先点「发送」按钮，找不到则回车。
- 运行期间用 `SetThreadExecutionState` 阻止系统睡眠（不点亮屏幕），退出时恢复。

## 使用

1. 安装依赖（仅首次）：`pip install uiautomation pyperclip`
2. 启动：
   - 双击 `start.vbs`（静默后台，推荐）；或
   - 命令行 `python main.py loop`（整夜循环，默认）；`python main.py once`（发送一次即退出）。
3. 停止：任务管理器结束 `pythonw.exe` / 命令行 Ctrl+C。
4. 看日志：`logs/auto_continue_YYYYMMDD.log`。

## 配置（config.py）

| 项 | 默认 | 说明 |
| --- | --- | --- |
| `POLL_INTERVAL` | 60 | 轮询间隔（秒） |
| `SEND_TEXT` | 继续 | 自动发送的内容 |
| `SEND_COOLDOWN` | 1800 | 两次自动发送最小间隔（秒），防刷屏 |
| `LIMIT_KEYWORDS` / `WORKING_KEYWORDS` | 见文件 | 状态判定关键词，界面改版后可自行补充 |

## 注意事项

- 工具只操作 ChatGPT 桌面版（`ChatGPT.exe`），不会碰同名浏览器标签页。
- 发送时若窗口被最小化会被短暂还原；发送后不自动最小化回去。
- 若 Codex 停在「请求批准」等人审状态，发送「继续」不会替你做审批。
- 电脑需保持开机；工具只防睡眠，不防关机。
