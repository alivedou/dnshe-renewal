import json
import os
from datetime import datetime

import requests

BASE_URL = "https://api005.dnshe.com/index.php?m=domain_hub"

# 续期阈值：剩余天数小于该值才续期（改数字即可，不走 Actions 变量）
RENEW_THRESHOLD_DAYS = 180


def send_notification(content, title="DNSHE 域名自动续期报告"):
    """使用 ServerChan (sct.ftqq.com) 发送通知"""
    sct_key = os.environ.get("SCT_KEY")
    if not sct_key:
        print("未配置 SCT_KEY，跳过推送")
        return

    url = f"https://sct.ftqq.com/{sct_key}.send"
    data = {
        "title": title,
        "desp": content.replace("\n", "\n\n"),
        "short": title[:64],
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        print("ServerChan 推送结果:", resp.text)
    except Exception as e:
        print("推送失败:", str(e))


def load_accounts():
    """
    加载账号列表，支持两种方式（优先 JSON 多账号）：

    1) Secret DNSHE_ACCOUNTS（推荐，多账号顺序执行）:
       [
         {"name": "号1", "api_key": "xxx", "api_secret": "yyy"},
         {"name": "号2", "api_key": "aaa", "api_secret": "bbb"}
       ]

    2) 单账号兼容:
       DNSHE_API_KEY + DNSHE_API_SECRET
       可选 DNSHE_ACCOUNT_NAME（默认 default）
    """
    raw = os.environ.get("DNSHE_ACCOUNTS", "").strip()
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SystemExit(f"DNSHE_ACCOUNTS 不是合法 JSON: {e}")

        if not isinstance(data, list) or not data:
            raise SystemExit("DNSHE_ACCOUNTS 必须是非空 JSON 数组")

        accounts = []
        for i, item in enumerate(data, 1):
            if not isinstance(item, dict):
                raise SystemExit(f"DNSHE_ACCOUNTS[{i}] 必须是对象")
            key = (item.get("api_key") or item.get("key") or "").strip()
            secret = (item.get("api_secret") or item.get("secret") or "").strip()
            name = (item.get("name") or item.get("label") or f"account-{i}").strip()
            if not key or not secret:
                raise SystemExit(f"账号 [{name}] 缺少 api_key / api_secret")
            accounts.append({"name": name, "api_key": key, "api_secret": secret})
        return accounts

    key = (os.environ.get("DNSHE_API_KEY") or "").strip()
    secret = (os.environ.get("DNSHE_API_SECRET") or "").strip()
    if key and secret:
        name = (os.environ.get("DNSHE_ACCOUNT_NAME") or "default").strip()
        return [{"name": name, "api_key": key, "api_secret": secret}]

    raise SystemExit(
        "未配置账号：请设置 DNSHE_ACCOUNTS（多账号 JSON），"
        "或 DNSHE_API_KEY + DNSHE_API_SECRET（单账号）"
    )


def process_account(account):
    """处理单个账号：列域名 → 按阈值续期 → 返回报告文本与是否有失败"""
    name = account["name"]
    headers = {
        "X-API-Key": account["api_key"],
        "X-API-Secret": account["api_secret"],
        "Content-Type": "application/json",
    }

    lines = [f"## 账号: {name}", ""]
    has_error = False

    list_url = (
        f"{BASE_URL}&endpoint=subdomains&action=list"
        f"&fields=id,subdomain,rootdomain,full_domain,status,expires_at,never_expires"
    )
    try:
        resp = requests.get(list_url, headers=headers, timeout=30)
        body = resp.json()
        subdomains = body.get("subdomains", [])
        if resp.status_code >= 400:
            has_error = True
            lines.append(f"❌ 获取域名列表 HTTP {resp.status_code}: {body}")
            return "\n".join(lines), has_error
    except Exception as e:
        has_error = True
        lines.append(f"❌ 获取域名列表失败: {e}")
        return "\n".join(lines), has_error

    if not subdomains:
        lines.append("（该账号下无子域名）")
        return "\n".join(lines), has_error

    today = datetime.now()
    renewal_results = []
    expiry_info = []

    for domain in subdomains:
        domain_id = domain["id"]
        full_domain = domain["full_domain"]
        expires_at_str = domain.get("expires_at")
        never_expires = domain.get("never_expires", 0)

        if never_expires:
            expiry_info.append(f"{full_domain}: 到期时间 永久有效")
            renewal_results.append(f"⏭️ {full_domain}: 已设置为永不过期，跳过续期")
            continue

        expires_at = None
        days_remaining = None
        if expires_at_str:
            try:
                expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
                days_remaining = (expires_at - today).days
            except ValueError:
                days_remaining = None

        if days_remaining is not None:
            expiry_info.append(
                f"{full_domain}: 到期时间 {expires_at_str} (剩余 {days_remaining}天)"
            )
        else:
            expiry_info.append(f"{full_domain}: 到期时间 未知")

        if days_remaining is not None and days_remaining >= RENEW_THRESHOLD_DAYS:
            renewal_results.append(
                f"⏭️ {full_domain}: 剩余 {days_remaining}天 >= {RENEW_THRESHOLD_DAYS}天，跳过续期"
            )
            continue

        renew_url = f"{BASE_URL}&endpoint=subdomains&action=renew"
        payload = {"subdomain_id": domain_id}

        try:
            r_resp = requests.post(
                renew_url, headers=headers, json=payload, timeout=30
            ).json()
            if r_resp.get("success"):
                new_expiry = r_resp.get("new_expires_at", "未知")
                charged = r_resp.get("charged_amount", 0)
                renewal_results.append(
                    f"✅ {full_domain}: 续期成功 (新到期: {new_expiry}, 消耗: {charged}积分)"
                )
            else:
                has_error = True
                msg = r_resp.get("message", "未知错误")
                renewal_results.append(f"❌ {full_domain}: 续期失败 ({msg})")
        except Exception as e:
            has_error = True
            renewal_results.append(f"❌ {full_domain}: 请求异常 ({e})")

    lines.append("=== 本次续期结果 ===")
    if renewal_results:
        lines.extend(renewal_results)
    else:
        lines.append(
            f"（所有域名剩余天数 >= {RENEW_THRESHOLD_DAYS}天，本次无需续期）"
        )

    lines.append("")
    lines.append("=== 所有域名到期时间 ===")
    lines.extend(expiry_info)

    return "\n".join(lines), has_error


def main():
    accounts = load_accounts()
    print(f"共 {len(accounts)} 个账号，将顺序执行")
    print(f"续期阈值: 剩余 < {RENEW_THRESHOLD_DAYS} 天")

    all_parts = []
    any_error = False

    for i, account in enumerate(accounts, 1):
        print(f"\n-------- [{i}/{len(accounts)}] {account['name']} --------")
        report, err = process_account(account)
        print(report)
        all_parts.append(report)
        if err:
            any_error = True

    full_message = "\n\n---\n\n".join(all_parts)
    status = "有失败" if any_error else "完成"
    title = f"DNSHE 多账号续期报告 ({len(accounts)}号) · {status}"
    send_notification(full_message, title=title)

    if any_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
