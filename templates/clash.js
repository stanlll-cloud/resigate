// ResiGate · Clash / FlClash 住宅 IP 精准分流覆写脚本
// 适用：FlClash (>= 0.8.85) / Clash Verge Rev / Clash Party
// 链路：本机 -> 机场跳板节点 -> 🏠住宅出口-勿选 -> 目标站点

const HOME = {
  type: "http",
  server: "<HOST>",
  port: 0,
  username: "<USERNAME>",
  password: "<PASSWORD>",
  udp: true,
};

const OPTIONS = {
  exitName: "🏠住宅出口-勿选",
  relayName: "RG_Relay",
  // 留空 = 自动跟随主选择组；填 "DIRECT" = 直连住宅；也可填特定策略组或节点名
  forceRelay: "",
  blockAnthropicIpv6: true,
};

const RELAY_EXCLUDE = "(?i)住宅出口|到期|过期|剩余|官网|网址|失联|故障|重置|套餐|Expire|Traffic|Reset|^(DIRECT|REJECT|COMPATIBLE|PASS)$";

const DEFAULT_RULES = [
  "DOMAIN-SUFFIX,claude.ai,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,claude.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,clau.de,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,anthropic.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,claudeusercontent.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,claudemcpcontent.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,modelcontextprotocol.io,🏠住宅出口-勿选",
  "DOMAIN-KEYWORD,anthropic,🏠住宅出口-勿选",
  "DOMAIN-KEYWORD,claude,🏠住宅出口-勿选",
  "IP-CIDR,160.79.104.0/21,🏠住宅出口-勿选,no-resolve",
  "IP-ASN,399358,🏠住宅出口-勿选,no-resolve",
  "DOMAIN-SUFFIX,openai.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,chatgpt.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,chat.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,oaistatic.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,oaiusercontent.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,sora.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,auth0.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,gemini.google.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,aistudio.google.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,generativelanguage.googleapis.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,alkalimakersuite-pa.clients6.google.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,accounts.google.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,labs.google,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,sentry.io,🏠住宅出口-勿选",
  "DOMAIN-KEYWORD,browser-intake,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,datadoghq.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,growthbook.io,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,usefathom.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,segment.io,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,siftscience.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,intercom.io,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,intercomcdn.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,hcaptcha.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,challenges.cloudflare.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,recaptcha.net,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,stripe.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,stripe.network,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,stripecdn.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,withpersona.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,paypal.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,paypalobjects.com,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,webshare.io,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,ipinfo.io,🏠住宅出口-勿选",
  "DOMAIN-SUFFIX,ip.sb,🏠住宅出口-勿选",
  "PROCESS-NAME,com.anthropic.claude,🏠住宅出口-勿选",
  "PROCESS-NAME,com.openai.chatgpt,🏠住宅出口-勿选",
  "PROCESS-NAME,com.google.android.apps.bard,🏠住宅出口-勿选",
];

const IPV6_BLOCK_RULES = [
  "IP-CIDR6,2607:6bc0::/48,REJECT,no-resolve",
  "IP-CIDR6,2607:6bc0:11::/48,REJECT,no-resolve",
];

function mainGroup(config) {
  const groups = config["proxy-groups"] || [];
  const names = new Set(groups.map((g) => g.name));
  const rules = config.rules || [];
  for (let i = rules.length - 1; i >= 0; i--) {
    const p = String(rules[i]).split(",").map((x) => x.trim());
    if (/^(MATCH|FINAL)$/i.test(p[0]) && names.has(p[1])) return p[1];
  }
  const sel = groups.find((g) => g.type === "select");
  return sel ? sel.name : "";
}

const main = (config) => {
  config.proxies = config.proxies || [];
  config["proxy-groups"] = config["proxy-groups"] || [];
  const groups = config["proxy-groups"];
  const EXIT = OPTIONS.exitName;

  for (const g of groups) {
    if (g["include-all"] || g["include-all-proxies"]) {
      g["exclude-filter"] = g["exclude-filter"] ? g["exclude-filter"] + "|住宅出口" : "住宅出口";
    }
  }

  let relay = OPTIONS.forceRelay || mainGroup(config);
  if (!relay) {
    groups.push({
      name: OPTIONS.relayName,
      type: "url-test",
      hidden: true,
      url: "https://www.gstatic.com/generate_204",
      interval: 300,
      tolerance: 50,
      lazy: false,
      "include-all": true,
      "exclude-filter": RELAY_EXCLUDE,
    });
    relay = OPTIONS.relayName;
  }

  const proxyObj = {
    name: EXIT,
    ...HOME,
  };
  if (relay && relay !== "DIRECT") {
    proxyObj["dialer-proxy"] = relay;
  }
  config.proxies.push(proxyObj);

  const rules = [
    ...(OPTIONS.blockAnthropicIpv6 ? IPV6_BLOCK_RULES : []),
    ...DEFAULT_RULES,
  ];
  config.rules = rules.concat(config.rules || []);
  return config;
};
