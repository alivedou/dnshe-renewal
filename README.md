# DNSHE Auto Renew (ServerChan Edition)

自动续期 DNSHE 免费域名，基于 GitHub Actions 定时运行。  
支持 **多账号顺序执行**（一个跑完再跑下一个）。

## 功能

- 多账号顺序续期（`DNSHE_ACCOUNTS` JSON）
- 兼容旧版单账号 Secrets
- 自动检测到期时间，按阈值续期（默认剩余 &lt; 180 天）
- ServerChan (sct.ftqq.com) 微信汇总通知
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

### 通知

| Secret | 说明 |
|--------|------|
| `SCT_KEY` | ServerChan SendKey（https://sct.ftqq.com/ ） |

### 可选 Variables

| Variable | 默认 | 说明 |
|----------|------|------|
| `RENEW_THRESHOLD_DAYS` | `180` | 剩余天数 **小于** 该值才续期 |

路径：**Settings → Secrets and variables → Actions → Variables**

## 行为说明

1. 按账号顺序：列表 → 判断 → 续期  
2. 某账号失败会记入报告，**继续下一个账号**  
3. 全部跑完后 **一条** Server酱汇总（含所有账号）  
4. 任一账号有续期/列表失败时，Workflow 以 exit code 1 结束（方便 Actions 标红），但前面账号已执行完  

## 本地试跑

```bash
export DNSHE_ACCOUNTS='[{"name":"测试","api_key":"...","api_secret":"..."}]'
export SCT_KEY='你的SendKey'   # 可选
export RENEW_THRESHOLD_DAYS=180
pip install requests
python renew_domains.py
```

## 定时

默认 UTC 每月 1 日 00:00（北京时间约 08:00）。  
改 `.github/workflows/renew.yml` 里 `cron`，或用 Actions 页 **Run workflow** 手动跑。
