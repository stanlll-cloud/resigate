# ResiGate

**让 Claude、ChatGPT、Gemini 与支付风控网站，在你所有设备上固定走同一个静态住宅 IP。**

日常浏览、视频与下载依然走你原有的高速机场节点；只有高风控站点与配套验证码/支付接口才会经过链式跳板进入静态住宅出口，兼顾**低风控**、**高网速**与**省流量**。

> 🔗 **配套基础设施推荐**：
> - **独立静态住宅 IP（IPdodo）**：[点击注册获取纯净独享住宅 IP](https://account.ipdodo.com/account/register?invite_code=M9I3KRBI)
> - **前置加密跳板梯子（搬瓦工官方 Just My Socks）**：[CN2 GIA 稳定高速线路](https://justmysocks.net/members/aff.php?aff=39372)

---

## 核心特性

1. **精准分流，不烧昂贵住宅流量**
   - 将 **Google AI（Gemini / AI Studio）** 与 **全量 Google（Search / Drive / Play）** 拆开，默认只分流前者，避免下载大文件消耗住宅流量。
   - 默认覆盖 **Claude / Anthropic**、**OpenAI / ChatGPT**、**Stripe / PayPal / Persona**、**Cloudflare / hCaptcha / reCAPTCHA** 及常用风控埋点域名。
2. **链式跳板 + 防 502 修复**
   - 链路：`本机 → 机场节点（加密跳板）→ 静态住宅代理 → 目标站点`，解决国内直连 HTTP/SOCKS5 明文代理容易断线的问题。
   - 支持自定义指定前置跳板组/节点（或设为 `DIRECT` 直连）、UDP 开关、以及 Anthropic IPv6 拦截防 502 开关。
3. **单源驱动，全端一键导出**
   - 所有规则由 [`rules.json`](rules.json) 统一管理，前端生成器与各端静态模板保持严格一致。
   - 支持 **Clash Party**、**Clash Verge Rev**、**FlClash**、**Shadowrocket（含二维码）**、**Surge / Loon**、**Sing-box**，支持一键复制与下载配置文件。
4. **纯静态本地生成**
   - 网页工具（`index.html`）100% 在浏览器本地处理代理账密，不经过任何后端服务器。

---

## 快速开始

### 方式一：打开网页一键生成（推荐）

启用 GitHub Pages 后直接访问你的页面，或本地预览：

```bash
python3 -m http.server 8080
```

浏览器打开 `http://localhost:8080`：
1. 填入（或直接粘贴）静态住宅代理的 `Host:Port:User:Pass`；
2. 勾选需要走住宅 IP 的业务场景（支持额外自定义域名）；
3. 选择你的客户端，点击**复制**或**下载配置文件**并导入；
4. 访问 `https://ipv4.webshare.io/` 核对出口 IP 是否已切换为你的静态住宅 IP。

### 方式二：直接使用静态模板

- **Clash / FlClash**：使用 [`templates/clash.js`](templates/clash.js)，替换顶部 `HOME` 中的代理信息即可。
- **Shadowrocket**：使用 [`templates/resigate.module`](templates/resigate.module)。
- **Surge**：使用 [`templates/resigate.sgmodule`](templates/resigate.sgmodule)。
- **Loon**：使用 [`templates/resigate.plugin`](templates/resigate.plugin)。

---

## 规则维护与校验

所有分组规则均定义在 [`rules.json`](rules.json) 中。修改规则后，运行以下命令同步全部静态模板并执行校验：

```bash
python3 scripts/check.py --sync
```

---

## 开源协议

[MIT License](LICENSE)
