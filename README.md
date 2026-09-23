# ChatGPT Auto Continue

[English](#english) | [中文](#中文)

当 ChatGPT 桌面版（Windows）的 5 小时用量限额重置后，自动发送「继续」，让 Codex / Agent 接着干活 -- 不用熬夜守着。

A tiny Windows tray app that watches the ChatGPT desktop app and automatically sends a "continue" message once your 5-hour usage limit resets, so your Codex / agent work keeps going overnight.

![platform](https://img.shields.io/badge/platform-Windows-0078D6) ![python](https://img.shields.io/badge/python-3.9+-3776AB) ![license](https://img.shields.io/badge/license-MIT-green)

---

## English

### Features

- **Polls every minute** and classifies the ChatGPT window into three states:
  - `limited` – the "you've reached your usage limit" banner is visible → wait quietly;
  - `working` – "thinking" / stop button visible → don't disturb;
  - `idle` – free quota and nothing running → send your custom text (default `继续` / "continue") if the cooldown (default 30 min) has passed.
- **System tray app** (pystray): live status icon (orange = limited, green = working, blue = idle, gray = stopped), start/stop, send once, settings dialog, open logs.
- **Stays awake** while running (prevents Windows sleep; does not keep the screen on).
- **CLI mode** for headless use: `python main.py loop` / `python main.py once`.
- Works with a **minimized** ChatGPT window (restores it only for the moment of sending).

### Install

**Option A – download the exe (recommended)**

Grab `ChatGPT-Auto-Continue.exe` from [Releases](https://github.com/iYuXiaoyan/chatgpt-auto-continue/releases), put it anywhere, double-click. A tray icon appears; right-click it for the menu. Settings and logs live next to the exe (`settings.json`, `logs/`).

**Option B – run from source**

```bat
pip install -r requirements.txt
python tray_app.py        :: tray app
python main.py loop       :: or CLI
```

### Requirements

- Windows 10/11, ChatGPT **desktop** app open and signed in.
- The machine must stay **unlocked** (the tool prevents sleep, but cannot act on a lock screen).

### Disclaimer

Unofficial tool, not affiliated with or endorsed by OpenAI. "ChatGPT" is a trademark of OpenAI. It only reads UI text and sends keystrokes to a window you own; use at your own risk.

---

## 中文

### 功能

- **每分钟轮询** ChatGPT 桌面版窗口，三态状态机：
  - `limited` 限额用完 → 静默等待；
  - `working` Codex 工作中 → 不打扰；
  - `idle` 空闲 → 冷却期（默认 30 分钟）过后自动发送自定义文本（默认「继续」）。
- **托盘小软件**：图标颜色即状态（橙=限额，绿=工作中，蓝=空闲，灰=停止），右键菜单含 开始/停止、立即发送、设置、打开日志。
- 运行期间**防止系统睡眠**（不点亮屏幕）。
- 支持 **CLI 无界面模式**：`python main.py loop` / `once`。
- ChatGPT 窗口**最小化也能用**（发送瞬间短暂还原窗口）。

### 安装使用

**方式 A：下载 exe（推荐）**

在 [Releases](https://github.com/iYuXiaoyan/chatgpt-auto-continue/releases) 下载 `ChatGPT-Auto-Continue.exe`，放到任意位置双击即可。托盘图标右键出菜单；设置和日志存放在 exe 旁边（`settings.json`、`logs/`）。

**方式 B：源码运行**

```bat
pip install -r requirements.txt
python tray_app.py        :: 托盘版
python main.py loop       :: 或命令行版
```

### 前提

- Windows 10/11，ChatGPT **桌面版**已登录并保持打开。
- 电脑**不能锁屏**：工具只防睡眠，锁屏下任何键鼠自动化都无效。

### 免责声明

非官方工具，与 OpenAI 无关，「ChatGPT」为 OpenAI 商标。工具只读取界面文本、向本机窗口发送键盘输入，请自行评估风险后使用。

## License

[MIT](LICENSE)
