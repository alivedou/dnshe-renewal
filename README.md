# DNSHE Auto Renew (Telegram + SMTP)

自动续期 DNSHE 免费域名，基于 GitHub Actions 定时运行。  
支持 **多账号顺序执行**（一个跑完再跑下一个）。

## 功能

- 多账号顺序续期（`DNSHE_ACCOUNTS` JSON）
- 兼容旧版单账号 Secrets
- 自动检测到期时间，按阈值续期（默认剩余 &lt; 180 天）
- 通知通道（可并存）：
  - **Telegram Bot**（`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`）
  - **SMTP 邮件**（单个 Secret `SMTP_CONFIG` JSON）
- GitHub Actions 定时 / 手动触发

## Secrets 配置

路径：仓库 **Settings → Secrets and variables → Actions**

### 方式 A：多账号（推荐）

新建 Secret 名：`DNSHE_ACCOUNTS`  
值为 **JSON 数组**（不要用 Markdown 代码块包起来；可多行缩进）：

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

### 通知 A：Telegram（可选）

| Secret | 说明 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | 找 [@BotFather](https://t.me/BotFather) 创建机器人拿到的 Token |
| `TELEGRAM_CHAT_ID` | 你的用户/群 ID（见下方获取方法） |

#### 怎么拿 Token / Chat ID

1. Telegram 打开 [@BotFather](https://t.me/BotFather) → `/newbot` → 按提示创建 → 复制 **Token**  
2. Chat ID：打开 [@userinfobot](https://t.me/userinfobot) → 点 Start / 发任意消息 → 它会回你的 **Id**（一串数字）  
3. 先给你自己的机器人发一句 `hi`（否则机器人还不能主动给你发消息）  
4. 把 Token、Chat ID 分别填进仓库 Secrets  

发到群的话，把机器人拉进群，Chat ID 用群 ID（一般是负数，可用群内相关 bot 查）。  

旧的 `SCT_KEY` 可删，已不再使用。

### 通知 B：SMTP 邮件（可选，单个 JSON）

新建 Secret 名：`SMTP_CONFIG`  
值为 **一个 JSON 对象**（与 `DNSHE_ACCOUNTS` 一样，只贴纯 JSON）：

```json
{
  "host": "smtp.qq.com",
  "port": 465,
  "user": "你的邮箱@qq.com",
  "pass": "授权码",
  "from": "你的邮箱@qq.com",
  "to": "接收邮箱@example.com",
  "ssl": true
}
```

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `host` | ✅ | SMTP 服务器，如 `smtp.qq.com` / `smtp.163.com` / `smtp.gmail.com` |
| `port` | | 默认 `465`；Gmail 常用 `587` |
| `user` | ✅ | 登录用户（通常是邮箱） |
| `pass` | ✅ | **授权码 / App Password**，不是登录密码；也可用字段名 `password` |
| `from` | | 发件人，默认 = `user` |
| `to` | ✅ | 收件人；多人用逗号：`a@x.com,b@y.com` |
| `ssl` | | 默认 `true`（465 SSL）；`587` 请设 `false`（STARTTLS） |

说明：

- **TG 与 SMTP 可同时开**：两套都配则两条通道都推；只配一种也行  
- 都未配置 → 续期照跑，只跳过推送  
- 通知失败**不阻断**续期  
- 常见坑：必须用授权码；465/SSL 与 587/STARTTLS 别混；`from` 最好与认证邮箱一致  

QQ 邮箱：设置里开 SMTP → 生成授权码 → `host=smtp.qq.com` `port=465` `ssl=true`。  
Gmail：开 2FA → 应用专用密码 → `host=smtp.gmail.com` `port=587` `ssl=false`。

### 续期阈值

在 `renew_domains.py` 顶部改数字即可：

```python
RENEW_THRESHOLD_DAYS = 180  # 剩余天数小于该值才续期
```

无需在 GitHub Variables 里配置。

## 行为说明

1. 按账号顺序：列表 → 判断 → 续期  
2. 某账号失败会记入报告，**继续下一个账号**  
3. 全部跑完后 **一条** 精简汇总（每账号一行统计），推送到已配置的通道  
4. 失败时附失败域名列表  
5. 详细逐域名日志只在 Actions 控制台，不推通知  
6. 任一账号有续期/列表失败时，Workflow 以 exit code 1 结束（方便 Actions 标红），但前面账号已执行完  

通知示例：

```
DNSHE 续期报告 (2026-07-21 14:57) · 有失败

【号1】共 12 个域名，无需续期 10，续期成功 1，续期失败 1
失败域名:
  · foo.example.com (余额不足)
【号2】共 5 个域名，无需续期 5，续期成功 0，续期失败 0
```

## 本地试跑

```bash
export DNSHE_ACCOUNTS='[{"name":"测试","api_key":"...","api_secret":"..."}]'
export TELEGRAM_BOT_TOKEN='123456:ABC-DEF...'
export TELEGRAM_CHAT_ID='123456789'
# 可选 SMTP
export SMTP_CONFIG='{"host":"smtp.qq.com","port":465,"user":"a@qq.com","pass":"授权码","from":"a@qq.com","to":"b@example.com","ssl":true}'
pip install requests
python renew_domains.py
```

## 定时

默认 UTC 每月 **15** 日 00:00（北京时间约 08:00，避开月初扎堆）。  
改 `.github/workflows/renew.yml` 里 `cron`，或用 Actions 页 **Run workflow** 手动跑。

Fork 使用建议：请自行改成不同的 `cron`，避免与他人同一时间扎堆请求。
