#!/usr/bin/env python3
"""ResiGate 自检与单源同步工具。

用法：
  python3 scripts/check.py         # 校验 rules.json、模板一致性和 JS 执行逻辑
  python3 scripts/check.py --sync  # 根据 rules.json 同步生成各端静态模块文件
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_JSON = ROOT / "rules.json"
CLASH_JS = ROOT / "templates" / "clash.js"
SR_MODULE = ROOT / "templates" / "resigate.module"
SURGE_MODULE = ROOT / "templates" / "resigate.sgmodule"
LOON_PLUGIN = ROOT / "templates" / "resigate.plugin"

TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "PROCESS-NAME", "GEOIP", "GEOSITE"}


def expand_rule(raw: str, exit_name: str) -> str:
    if raw.startswith("S:"):
        return f"DOMAIN-SUFFIX,{raw[2:]},{exit_name}"
    if raw.startswith("K:"):
        return f"DOMAIN-KEYWORD,{raw[2:]},{exit_name}"
    return raw.replace("@", exit_name)


def load_default_rules():
    data = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    exit_name = data["exitName"]
    common, android, ipv6_block = [], [], []
    for g in data["groups"]:
        if not g.get("on"):
            continue
        for cidr in g.get("ipv6Block", []):
            ipv6_block.append(f"IP-CIDR6,{cidr},REJECT,no-resolve")
        for r in g.get("rules", []):
            common.append(expand_rule(r, exit_name))
        for p in g.get("android", []):
            android.append(f"PROCESS-NAME,{p},{exit_name}")
    return data, common, android, ipv6_block


def sync_templates():
    data, common, android, ipv6_block = load_default_rules()
    exit_name = data["exitName"]
    all_rules = common + android

    # 1. 同步 templates/clash.js 中的 DEFAULT_RULES 与 IPV6_BLOCK_RULES
    js_src = CLASH_JS.read_text(encoding="utf-8")
    rules_block = "const DEFAULT_RULES = [\n" + "".join(f"  {json.dumps(r, ensure_ascii=False)},\n" for r in all_rules) + "];"
    ipv6_block_str = "const IPV6_BLOCK_RULES = [\n" + "".join(f"  {json.dumps(r, ensure_ascii=False)},\n" for r in ipv6_block) + "];"
    js_src = re.sub(r"const DEFAULT_RULES = \[[\s\S]*?\];", rules_block, js_src, count=1)
    js_src = re.sub(r"const IPV6_BLOCK_RULES = \[[\s\S]*?\];", ipv6_block_str, js_src, count=1)
    CLASH_JS.write_text(js_src, encoding="utf-8")

    # 2. Shadowrocket Module
    sr_body = (
        f"#!name=ResiGate\n"
        f"#!desc=AI、支付与风控域名统一走备注为 {exit_name} 的静态住宅节点\n\n"
        f"[Rule]\n" + "\n".join(ipv6_block + common) + "\n"
    )
    SR_MODULE.write_text(sr_body, encoding="utf-8")

    # 3. Surge Module
    surge_body = (
        f"#!name=ResiGate\n"
        f"#!desc=AI、支付与风控域名统一走 {exit_name} 静态住宅节点\n"
        f"#!category=ResiGate\n\n"
        f"[Rule]\n" + "\n".join(ipv6_block + common) + "\n"
    )
    SURGE_MODULE.write_text(surge_body, encoding="utf-8")

    # 4. Loon Plugin
    loon_body = (
        f"#!name = ResiGate\n"
        f"#!desc = AI、支付与风控域名统一走 {exit_name} 静态住宅节点\n\n"
        f"[Rule]\n" + "\n".join(ipv6_block + common) + "\n"
    )
    LOON_PLUGIN.write_text(loon_body, encoding="utf-8")
    print("已根据 rules.json 同步所有端模板。")


def rule_ok(rule: str, exit_name: str, where: str, errors: list):
    parts = [p.strip() for p in rule.split(",")]
    if len(parts) < 3 or parts[0] not in TYPES:
        errors.append(f"{where}: 无法识别的规则 {rule}")
    elif parts[0] == "IP-CIDR6" and parts[2] != "REJECT":
        errors.append(f"{where}: IPv6 规则应为 REJECT：{rule}")
    elif parts[0] != "IP-CIDR6" and parts[2] != exit_name:
        errors.append(f"{where}: 策略应为 {exit_name}：{rule}")


def check_all():
    errors = []
    data, common, android, ipv6_block = load_default_rules()
    exit_name = data["exitName"]
    relay_name = data["relayName"]
    expected_common = set(ipv6_block + common)
    expected_all = expected_common | set(android)

    # 校验静态模块文件
    for label, path in [("shadowrocket", SR_MODULE), ("surge", SURGE_MODULE), ("loon", LOON_PLUGIN)]:
        if not path.exists():
            errors.append(f"缺少模板文件: {path}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if "[Rule]" not in lines:
            errors.append(f"{label}: 缺少 [Rule]")
            continue
        rules = [l.strip() for l in lines[lines.index("[Rule]") + 1:] if l.strip() and not l.startswith("#")]
        for r in rules:
            rule_ok(r, exit_name, label, errors)
        if set(rules) != expected_common:
            diff_miss = sorted(expected_common - set(rules))
            diff_extra = sorted(set(rules) - expected_common)
            errors.append(f"{label} 与 rules.json 不一致：缺 {diff_miss}，多 {diff_extra}")

    # 用 Node 跑 Clash 脚本测试
    if not shutil.which("node"):
        print("提示：未找到 node，跳过 JS 运行时检查", file=sys.stderr)
    else:
        src = CLASH_JS.read_text(encoding="utf-8")
        desktop = src.replace("const main = (config) => {", "function main(config, profileName) {").rstrip()
        desktop = re.sub(r"\n};$", "\n}", desktop)
        cases = {
            "match": (
                {
                    "proxies": [{"name": "🇯🇵 东京"}],
                    "proxy-groups": [
                        {"name": "♻️ 自动选择", "type": "url-test", "proxies": ["🇯🇵 东京"]},
                        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "🇯🇵 东京"]},
                    ],
                    "rules": ["GEOIP,CN,DIRECT", "MATCH,🚀 节点选择"],
                },
                "🚀 节点选择",
            ),
            "select": (
                {
                    "proxies": [{"name": "A"}],
                    "proxy-groups": [
                        {"name": "auto", "type": "url-test", "proxies": ["A"]},
                        {"name": "PROXY", "type": "select", "proxies": ["auto", "A"]},
                    ],
                    "rules": [],
                },
                "PROXY",
            ),
            "none": ({"proxies": [{"name": "A"}], "proxy-groups": [], "rules": ["MATCH,DIRECT"]}, relay_name),
        }
        for variant, code in (("flclash", src), ("desktop", desktop)):
            for case_name, (cfg, want_relay) in cases.items():
                js = code + f"\nconsole.log(JSON.stringify(main({json.dumps(cfg, ensure_ascii=False)})));"
                out = subprocess.run(["node", "-e", js], capture_output=True, text=True)
                if out.returncode != 0:
                    errors.append(f"{variant}/{case_name}: JS 运行失败\n{out.stderr}")
                    continue
                c = json.loads(out.stdout)
                leaf = next((p for p in c["proxies"] if p["name"] == exit_name), None)
                if not leaf:
                    errors.append(f"{variant}/{case_name}: 缺少出口节点 {exit_name}")
                    continue
                if leaf.get("dialer-proxy") != want_relay:
                    errors.append(f"{variant}/{case_name}: 跳板应为 {want_relay}，实际 {leaf.get('dialer-proxy')}")
                out_rules = {r for r in c["rules"] if exit_name in r or r.startswith("IP-CIDR6")}
                if out_rules != expected_all:
                    errors.append(f"{variant}/{case_name}: 输出规则与 rules.json 不一致")

        # 额外测试：forceRelay = "DIRECT" 时不应有 dialer-proxy
        direct_code = src.replace('forceRelay: ""', 'forceRelay: "DIRECT"')
        js_direct = direct_code + '\nconsole.log(JSON.stringify(main({"proxies":[],"proxy-groups":[],"rules":[]})));'
        out_d = subprocess.run(["node", "-e", js_direct], capture_output=True, text=True)
        if out_d.returncode == 0:
            c_d = json.loads(out_d.stdout)
            leaf_d = next((p for p in c_d["proxies"] if p["name"] == exit_name), {})
            if "dialer-proxy" in leaf_d:
                errors.append("forceRelay=DIRECT 时不应写入 dialer-proxy")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"检查通过：{len(expected_common)} 条通用规则 + {len(android)} 条安卓包名规则，全端模板一致。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="同步生成各端模板")
    args = parser.parse_args()
    if args.sync:
        sync_templates()
    check_all()
