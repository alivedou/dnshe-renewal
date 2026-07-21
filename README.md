# DNSHE Auto Renew (Telegram Edition)

自动续期 DNSHE 免费域名，基于 GitHub Actions 定时运行。  
支持 **多账号顺序执行**（一个跑完再跑下一个）。

## 功能

- 多账号顺序续期（`DNSHE_ACCOUNTS` JSON）
- 兼容旧版单账号 Secrets
- 自动检测到期时间，按阈值续期（默认剩余 &lt; 180 天）
- **Telegram Bot** 汇总通知（只推本仓库任务，不吵别的项目）
- GitHub Actions 定时 / 手动触发

## Secrets 配置

路径：仓库 **Settings → Secrets and variables → Actions**

### 方式 A：多账号（推荐）

新建 Secret 名：`DNSHE_ACCOUNTS`  
值为 **一行 JSON 数组**（不要用 Markdown 代码块包起来）：

```json
[
  {"name": "号1", "api_key": "你的KEY1", "api_secret": "你的SECRET1"},
  {"name": "号2", "api_key": "你的KEY2", "api_secret": "你的SECRET2"},
  {"name": "号3", "api_key": "你的KEY3", "api_secret": "你的SECRET3"}
]
```

字段说明：

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `name` | | 显示名，便于报告区分 |
| `api_key` | ✅ | 也可用 `key` |
| `api_secret` | ✅ | 也可用 `secret` |

执行顺序 = 数组顺序（先 号1，再 号2…）。

### 方式 B：单账号（兼容旧配置）

| Secret | 说明 |
|--------|------|
| `DNSHE_API_KEY` | API Key |
| `DNSHE_API_SECRET` | API Secret |
| `DNSHE_ACCOUNT_NAME` | 可选，报告里的账号名，默认 `default` |

若同时配置了 `DNSHE_ACCOUNTS`，**只使用多账号 JSON**，忽略单账号两项。

### 通知（Telegram）

| Secret | 说明 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | 找 [@BotFather](https://t.me/BotFather) 创建机器人拿到的 Token |
| `TELEGRAM_CHAT_ID` | 你的用户/群 ID（见下方获取方法） |

#### 怎么拿 Token / Chat ID

1. Telegram 打开 [@BotFather](https://t.me/BotFather) → `/newbot` → 按提示创建 → 复制 **Token**  
2. Chat ID：打开 [@userinfobot](https://t.me/userinfobot) → 点 Start / 发任意消息 → 它会回你的 **Id**（一串数字）  
3. 先给你自己的机器人发一句 `hi`（否则机器人还不能主动给你发消息）  
4. 把 Token、Chat ID 分别填进仓库 Secrets  

### 续期阈值

在 `renew_domains.py` 顶部改数字即可：

```python
RENEW_THRESHOLD_DAYS = 180  # 剩余天数小于该值才续期
```

无需在 GitHub Variables 里配置。

## 行为说明

1. 按账号顺序：列表 → 判断 → 续期  
2. 某账号失败会记入报告，**继续下一个账号**  
3. 全部跑完后 **一条** Telegram 汇总（超长自动拆多条）  
4. 任一账号有续期/列表失败时，Workflow 以 exit code 1 结束（方便 Actions 标红），但前面账号已执行完  

## 本地试跑

```bash
export DNSHE_ACCOUNTS='[{"name":"测试","api_key":"...","api_secret":"..."}]'
export TELEGRAM_BOT_TOKEN='123456:ABC-DEF...'
export TELEGRAM_CHAT_ID='123456789'
pip install requests
python renew_domains.py
```

## 定时

默认 UTC 每月 **15** 日 00:00（北京时间约 08:00，避开月初扎堆）。  
改 `.github/workflows/renew.yml` 里 `cron`，或用 Actions 页 **Run workflow** 手动跑。
