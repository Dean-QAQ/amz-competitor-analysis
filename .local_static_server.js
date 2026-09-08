const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");
const { spawnSync, spawn } = require("child_process");

const root = __dirname;
const scanRoot = path.resolve(root, "..");
const codexConfigPath = path.join(process.env.USERPROFILE || "", ".codex", "config.toml");

/* 亚马逊商品页抓取：用于在 MCP 未返回主图时兜底。只抓公开商品页 HTML 里的真实图片字段，
 * 不访问评论页（评论页需要登录）。走本机代理 127.0.0.1:7897，超时 20 秒。 */
/* 已废弃：模板字符串转义易错，改为调用 scripts/fetch_amazon_product.js 独立脚本文件 */
const AMAZON_PRODUCT_FETCH_SCRIPT_DEPRECATED = `
const https = require("https");
const http = require("http");
const { URL } = require("url");

const asin = process.argv[2] || "";
if (!/^[A-Z0-9]{10}$/.test(asin)) {
  console.log(JSON.stringify({ found: false, error: "ASIN 格式无效" }));
  process.exit(0);
}
const target = new URL("https://www.amazon.com/dp/" + asin);
const options = {
  hostname: target.hostname,
  path: target.pathname,
  method: "GET",
  headers: {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
  },
};
function fetchViaProxy() {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port: 7897, path: target.toString(), method: "GET", headers: options.headers, timeout: 20000 }, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf8") }));
    });
    req.on("timeout", () => req.destroy(new Error("请求超时")));
    req.on("error", reject);
    req.end();
  });
}
function fetchDirect() {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf8") }));
    });
    req.on("timeout", () => req.destroy(new Error("请求超时")));
    req.on("error", reject);
    req.end();
  });
}
(async () => {
  let result = null;
  try { result = await fetchViaProxy(); } catch (err) { /* 代理失败时尝试直连 */ }
  if (!result || result.status !== 200) {
    try { result = await fetchDirect(); } catch (err) { /* 直连也失败时报错 */ }
  }
  if (!result || result.status !== 200) {
    console.log(JSON.stringify({ found: false, error: "亚马逊页面返回 " + (result ? result.status : "网络失败") }));
    process.exit(0);
  }
  const html = result.body;
  const patterns = [
    /"hiRes":"(https:\\/\\/m\\.media-amazon\\.com\\/images\\/I\\/[^"]+)"/,
    /"large":"(https:\\/\\/m\\.media-amazon\\.com\\/images\\/I\\/[^"]+)"/,
    /<meta property="og:image" content="([^"]+)"/,
  ];
  let imageUrl = null;
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) { imageUrl = m[1].replace(/\\\\u([0-9a-fA-F]{4})/g, (s, h) => String.fromCharCode(parseInt(h, 16))).replace(/\\\\/g, ""); break; }
  }
  const titleMatch = html.match(/<span id="productTitle"[^>]*>([\\s\\S]*?)<\\/span>/);
  const title = titleMatch ? titleMatch[1].trim().replace(/\\s+/g, " ") : null;
  const ratingMatch = html.match(/([0-9.]+) out of 5 stars/);
  const rating = ratingMatch ? parseFloat(ratingMatch[1]) : null;
  const reviewCountMatch = html.match(/([0-9,]+) (?:global ratings|ratings|reviews)/i);
  const reviewCount = reviewCountMatch ? parseInt(reviewCountMatch[1].replace(/,/g, ""), 10) : null;
  const brandMatch = html.match(/<a id="bylineInfo"[^>]*>([\\s\\S]*?)<\\/a>/);
  let brand = null;
  if (brandMatch) {
    brand = brandMatch[1].replace(/<[^>]+>/g, "").replace(/^(?:Visit the|Brand:)\s*/i, "").replace(/\s*(?:Store|Brand)\s*$/i, "").trim();
  }
  const priceMatch = html.match(/class="a-offscreen">\\$([0-9.,]+)/);
  const price = priceMatch ? parseFloat(priceMatch[1].replace(/,/g, "")) : null;
  console.log(JSON.stringify({ found: !!(imageUrl || title), imageUrl, title, rating, reviewCount, brand, price }));
})().catch((err) => console.log(JSON.stringify({ found: false, error: err.message })));
`;

/* 密钥从 .env.local 读取，避免真实 Key 硬编码进仓库。
 * 本地运行时请把 .env.local 放在本文件同级目录（不提交到 Git）。 */
try {
  require("dotenv").config({ path: path.join(root, ".env.local") });
} catch (err) {
  /* dotenv 未安装时手动解析，支持 KEY=value 格式 */
  try {
    const envPath = path.join(root, ".env.local");
    if (fs.existsSync(envPath)) {
      fs.readFileSync(envPath, "utf8").split(/\r?\n/).forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) return;
        const eq = trimmed.indexOf("=");
        if (eq <= 0) return;
        const key = trimmed.slice(0, eq).trim();
        const value = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
        if (!(key in process.env)) process.env[key] = value;
      });
    }
  } catch (err2) { /* 忽略解析失败，使用空 Key */ }
}

const mime = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

const localDataCache = new Map();

const XIYOU_MCP_URL = "https://mcp.xydc.com/mcp";
const XIYOU_MCP_KEY = process.env.XIYOU_MCP_KEY || "";
const SORFTIME_MCP_AUTH = process.env.SORFTIME_MCP_AUTH || "";
const SIF_MCP_URL = "https://mcp.sif.com/mcp";
const SIF_MCP_KEY = process.env.SIF_MCP_KEY || "";
const LINGXING_MCP_URL = "https://openmcp.lingxing.com/mcp-servers/lingxing-mcp";
let LINGXING_MCP_KEY = process.env.LINGXING_MCP_KEY || "";

function readSorftimeUrl() {
  /* 优先读 config.toml；找不到时回退到内置官方地址（Key 由 SORFTIME_MCP_AUTH 环境变量提供） */
  try {
    const raw = fs.readFileSync(codexConfigPath, "utf8");
    const match = raw.match(/^\[mcp_servers\."Sorftime-MCP"\][\s\S]*?^url\s*=\s*"([^"]+)"/m);
    if (match) return match[1];
  } catch (err) { /* 读取失败时走内置地址 */ }
  return "https://mcp.sorftime.com";
}

async function proxyXiyouMcp(req, res) {
  try {
    const body = await readBody(req);
    const upstream = await fetch(XIYOU_MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": req.headers["content-type"] || "application/json",
        "Accept": req.headers.accept || "application/json, text/event-stream",
        "Authorization": "Bearer " + XIYOU_MCP_KEY,
      },
      body,
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(text);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err) });
  }
}

async function proxySorftimeMcp(req, res) {
  try {
    const targetUrl = readSorftimeUrl();
    const body = await readBody(req);
    const upstream = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": req.headers["content-type"] || "application/json",
        "Accept": req.headers.accept || "application/json, text/event-stream",
        "Authorization": SORFTIME_MCP_AUTH,
      },
      body,
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(text);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err) });
  }
}

async function proxySifMcp(req, res) {
  try {
    const body = await readBody(req);
    let key = SIF_MCP_KEY;
    const clientKey = req.headers["x-sif-key"] || req.headers["secret-key"];
    if (typeof clientKey === "string" && clientKey.trim()) key = clientKey.trim();
    const upstream = await fetch(SIF_MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": req.headers["content-type"] || "application/json",
        "Accept": req.headers.accept || "application/json, text/event-stream",
        "secret-key": key,
      },
      body,
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(text);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err) });
  }
}

async function proxyLingXingMcp(req, res) {
  try {
    const body = await readBody(req);
    let key = LINGXING_MCP_KEY;
    const clientKey = req.headers["x-lingxing-key"];
    if (typeof clientKey === "string" && clientKey.trim()) key = clientKey.trim();
    const headers = {
      "Content-Type": req.headers["content-type"] || "application/json",
      "Accept": req.headers.accept || "application/json, text/event-stream",
    };
    if (key) headers["X-Mcp-Key"] = key;
    const upstream = await fetch(LINGXING_MCP_URL, {
      method: "POST",
      headers,
      body,
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(text);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err) });
  }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function pythonCandidates() {
  const list = [
    process.env.LOCAL_PYTHON,
    path.join(
      process.env.USERPROFILE || "",
      ".cache",
      "codex-runtimes",
      "codex-primary-runtime",
      "dependencies",
      "python",
      "python.exe"
    ),
    "python",
    "py",
  ].filter(Boolean);
  if (process.platform === "win32") {
    try {
      const wh = spawnSync("where.exe", ["python"], { encoding: "utf8", windowsHide: true });
      String(wh.stdout || "")
        .split(/\r?\n/)
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((p) => list.push(p));
    } catch (err) { /* ignore */ }
  }
  return [...new Set(list)];
}

/** 评论 Skill Worker 必须用装了 playwright 的 Python；Codex runtime 没有该包，spawn 后秒退。 */
function pythonCandidatesForReviews() {
  const preferred = [
    process.env.AMAZON_REVIEWS_PYTHON,
    process.env.LOCAL_PYTHON,
    "python",
    "py",
  ].filter(Boolean);
  if (process.platform === "win32") {
    try {
      const wh = spawnSync("where.exe", ["python"], { encoding: "utf8", windowsHide: true });
      String(wh.stdout || "")
        .split(/\r?\n/)
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((p) => preferred.push(p));
    } catch (err) { /* ignore */ }
  }
  const uniq = [...new Set(preferred)].filter((exe) => !/codex-primary-runtime/i.test(String(exe)));
  const ok = [];
  for (const exe of uniq) {
    try {
      const args = /(^|[\\/])py(\.exe)?$/i.test(exe)
        ? ["-3", "-c", "import playwright"]
        : ["-c", "import playwright"];
      const res = spawnSync(exe, args, { encoding: "utf8", timeout: 15000, windowsHide: true });
      if (!res.error && res.status === 0) ok.push(exe);
    } catch (err) { /* try next */ }
  }
  return ok.length ? ok : uniq;
}

function runPythonJson(script, payload) {
  let lastError = "";
  for (const exe of pythonCandidates()) {
    const env = Object.assign({}, process.env, {
      PYTHONIOENCODING: "utf-8",
      LOCAL_SCAN_PAYLOAD: JSON.stringify(payload),
    });
    const res = spawnSync(exe, ["-"], {
      input: script,
      encoding: "utf8",
      timeout: 45000,
      maxBuffer: 40 * 1024 * 1024,
      env,
    });
    if (!res.error && res.status === 0) return JSON.parse(res.stdout || "{}");
    lastError = (res.error && res.error.message) || res.stderr || ("exit " + res.status);
  }
  throw new Error("Unable to read local files: " + lastError);
}

const LOCAL_SCAN_SCRIPT = String.raw`
import sys, os, json, csv, re, datetime

payload = json.loads(os.environ.get("LOCAL_SCAN_PAYLOAD") or sys.stdin.read() or "{}")
ROOT = os.path.abspath(payload.get("root") or ".")
MODE = payload.get("mode") or "market"
NEEDLE = (payload.get("asin") or "").strip().upper()
OVERRIDE = (payload.get("fileOverride") or "").strip()
LIMIT = int(payload.get("limit") or 0)

try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None

SKIP_DIRS = {".git", "node_modules", ".chrome-check", "__pycache__", ".venv", "venv", "AppData"}
TEXT_EXTS = {".txt", ".csv", ".json", ".jsonl"}
EXCEL_EXTS = {".xlsx", ".xlsm"}

def inside_root(p):
    ap = os.path.abspath(p)
    return ap == ROOT or ap.startswith(ROOT + os.sep)

def norm_label(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    return re.sub(r"[\s\r\n\t:：,，、。.;；/\\()（）\\[\\]【】{}<>《》'\"·|\\-_%]+", "", text)

ALIASES = {
    "asin": "asin",
    "sku": "sku",
    "品牌": "brand",
    "brand": "brand",
    "品牌链接": "brandUrl",
    "商品标题": "title",
    "标题": "title",
    "title": "title",
    "商品详情页链接": "url",
    "链接": "url",
    "url": "url",
    "detailpageurl": "url",
    "图片": "image",
    "商品主图": "image",
    "image": "image",
    "mainimage": "image",
    "父asin": "parentAsin",
    "类目路径": "categoryPath",
    "所属类目": "categoryPath",
    "大类目": "categoryName",
    "大类bsr": "categoryRank",
    "大类排名": "categoryRank",
    "小类目": "subcategoryName",
    "小类bsr": "subcategoryRank",
    "小类排名": "subcategoryRank",
    "排名": "rank",
    "价格": "price",
    "价格$": "price",
    "售价": "price",
    "price": "price",
    "评分": "rating",
    "rating": "rating",
    "评分数": "reviewCount",
    "评论数": "reviewCount",
    "reviews": "reviewCount",
    "reviewcount": "reviewCount",
    "qa数": "qaCount",
    "q&a数": "qaCount",
    "上架时间": "launchDate",
    "上线时间": "launchDate",
    "上架天数": "daysOnSale",
    "已上架天数": "daysOnSale",
    "变体": "variants",
    "变体数": "variantCount",
    "变体数量": "variantCount",
    "材质": "material",
    "材料": "material",
    "material": "material",
    "颜色": "color",
    "色彩": "color",
    "color": "color",
    "colour": "color",
    "产品尺寸": "productSize",
    "商品尺寸": "productSize",
    "productdimensions": "productSize",
    "itemdimensions": "productSize",
    "产品重量": "productWeight",
    "商品重量": "productWeight",
    "itemweight": "productWeight",
    "productweight": "productWeight",
    "包装内容": "includedComponents",
    "包含组件": "includedComponents",
    "includedcomponents": "includedComponents",
    "详细参数": "productParams",
    "产品参数信息": "productParams",
    "包装尺寸及重量": "packageInfo",
    "包装尺寸": "packageSize",
    "包装尺寸单位换算": "packageSize",
    "包装重量": "packageWeight",
    "包装重量单位换算": "packageWeight",
    "月销量": "sales30d",
    "30天销量": "sales30d",
    "30天销量畅销变体": "sales30d",
    "历史月销": "monthlySales",
    "历史月销量": "monthlySales",
    "keepa趋势": "keepaTrend",
    "ai评论分析": "summary",
    "ai文本分析": "summary",
    "评论分析": "summary",
    "产品卖点": "sellingPoints",
    "好评点": "positiveReviews",
    "差评点": "negativeReviews",
    "待改善点": "improvementPoints",
    "使用人群": "targetAudience",
    "使用场景": "useScenarios",
    "优化方向": "optimizationDirection",
}

REVIEW_ALIASES = {
    "asin": "asin",
    "商品asin": "asin",
    "父asin": "parentAsin",
    "标题": "title",
    "reviewtitle": "title",
    "评论标题": "title",
    "评价标题": "title",
    "评论内容": "content",
    "评价内容": "content",
    "评论正文": "content",
    "内容": "content",
    "正文": "content",
    "reviewcontent": "content",
    "content": "content",
    "comment": "content",
    "text": "content",
    "body": "content",
    "summary": "summary",
    "reviewsummary": "summary",
    "commentsummary": "summary",
    "ai评论分析": "summary",
    "评论分析": "summary",
    "sellingpoints": "sellingPoints",
    "产品卖点": "sellingPoints",
    "positivereviews": "positiveReviews",
    "好评点": "positiveReviews",
    "negativereviews": "negativeReviews",
    "差评点": "negativeReviews",
    "improvementpoints": "improvementPoints",
    "待改善点": "improvementPoints",
    "targetaudience": "targetAudience",
    "使用人群": "targetAudience",
    "usescenarios": "useScenarios",
    "使用场景": "useScenarios",
    "optimizationdirection": "optimizationDirection",
    "优化方向": "optimizationDirection",
    "评分": "rating",
    "星级": "rating",
    "rating": "rating",
    "star": "rating",
    "stars": "rating",
    "日期": "date",
    "reviewdate": "date",
}

# 追加常见市场调研 / 竞品分析 / 评论明细表头映射，保持后续本地数据源可插拔。
# 这些别名不覆盖真实接口返回值，只用于把本地文件字段准确映射到统一数据模型。
ALIASES.update({
    "父asin": "parentAsin",
    "品牌名": "brand",
    "卖家": "sellerName",
    "店铺": "storeName",
    "产品标题": "title",
    "商品名称": "title",
    "详情页链接": "url",
    "商品链接": "url",
    "图片链接": "image",
    "图片地址": "image",
    "主图链接": "image",
    "主图地址": "image",
    "大类": "categoryName",
    "大类排名": "categoryRank",
    "小类": "subcategoryName",
    "小类排名": "subcategoryRank",
    "bsr排名": "rank",
    "现价": "price",
    "原价": "originalPrice",
    "折扣": "discount",
    "星级": "rating",
    "评价数": "reviewCount",
    "上市时间": "launchDate",
    "上架天数": "daysOnSale",
    "已上架天数": "daysOnSale",
    "产品大小": "productSize",
    "配件清单": "includedComponents",
    "产品参数": "productParams",
    "规格参数": "productParams",
    "包装尺寸单位换算": "packageSize",
    "包装重量单位换算": "packageWeight",
    "近30天销量": "sales30d",
    "30天销量畅销变体": "sales30d",
    "30天销量(畅销变体)": "sales30d",
    "30天销量（畅销变体）": "sales30d",
    "历史月销量": "monthlySales",
    "月销量趋势": "monthlySales",
    "历史月销量趋势": "monthlySales",
    "keepa走势图": "keepaTrend",
    "评论总结": "summary",
    "目标人群": "targetAudience",
    "应用场景": "useScenarios",
    "改进方向": "optimizationDirection",
})

REVIEW_ALIASES.update({
    "评论id": "reviewId",
    "评价id": "reviewId",
    "评论人id": "reviewerId",
    "用户id": "reviewerId",
    "买家id": "reviewerId",
    "评论人": "reviewerName",
    "评价人": "reviewerName",
    "用户名": "reviewerName",
    "买家": "reviewerName",
    "作者": "reviewerName",
    "评价正文": "content",
    "评论文本": "content",
    "星等": "rating",
    "时间": "date",
    "评论日期": "date",
    "评价日期": "date",
    "评论时间": "date",
    "评价时间": "date",
    "评论总结": "summary",
    "摘要": "summary",
    "目标人群": "targetAudience",
    "应用场景": "useScenarios",
    "改进方向": "optimizationDirection",
})

def clean(value, keep_formula=False):
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text or text in {"--", "/", "无", "无数据"}:
            return None
        if text.startswith("=") and not keep_formula:
            return None
        return text
    return value

def is_empty(value):
    return value is None or value == "" or value == [] or value == {}

def file_matches_needle(fp):
    return bool(NEEDLE and NEEDLE in os.path.basename(fp).upper())

def unique_join(a, b):
    parts = []
    seen = set()
    for value in [a, b]:
        if is_empty(value):
            continue
        if isinstance(value, list):
            lines = value
        else:
            lines = re.split(r"[\n;；]+", str(value))
        for line in lines:
            text = str(line).strip()
            if text and text not in seen:
                seen.add(text)
                parts.append(text)
    return "\n".join(parts) if parts else None

LINE_FIELDS = {"sellingPoints", "positiveReviews", "negativeReviews", "improvementPoints", "targetAudience", "useScenarios", "optimizationDirection", "summary"}
MONTHLY_FIELDS = {"monthlySales", "monthlyTrend"}

def merge_item(target, src):
    if not src:
        return target
    src_monthly_priority = int(src.get("_monthlySalesPriority") or 0)
    target_monthly_priority = int(target.get("_monthlySalesPriority") or 0)
    for key, value in src.items():
        if is_empty(value):
            continue
        if key in {"sourceFile", "sourceSheet"}:
            continue
        if key in MONTHLY_FIELDS:
            if is_empty(target.get(key)) and (target_monthly_priority == 0 or src_monthly_priority >= target_monthly_priority):
                target[key] = value
            elif src_monthly_priority > target_monthly_priority:
                target[key] = value
            if src_monthly_priority > target_monthly_priority:
                target["_monthlySalesPriority"] = src_monthly_priority
                target_monthly_priority = src_monthly_priority
            continue
        if key in LINE_FIELDS and not is_empty(target.get(key)):
            target[key] = unique_join(target.get(key), value)
        elif is_empty(target.get(key)):
            target[key] = value
    sources = target.setdefault("_sources", [])
    source = {"file": src.get("sourceFile"), "sheet": src.get("sourceSheet")}
    if source["file"] and source not in sources:
        sources.append(source)
    return target

def map_product_field(label):
    n = norm_label(label)
    if n in ALIASES:
        return ALIASES[n]
    raw = str(label or "").strip().lower()
    compact = re.sub(r"[\W_]+", "", raw)
    if not compact:
        return None
    if "asin" in compact:
        return "asin"
    if any(x in raw for x in ["商品主图", "主图", "图片链接", "图片地址"]) or any(x in compact for x in ["mainimage", "imageurl", "imgurl"]):
        return "image"
    if any(x in raw for x in ["商品详情页链接", "详情页链接", "商品链接", "链接"]) or any(x in compact for x in ["detailpageurl", "producturl", "url"]):
        return "url"
    if any(x in raw for x in ["商品标题", "产品标题", "标题", "名称"]) or any(x in compact for x in ["title", "productname", "producttitle"]):
        return "title"
    if any(x in raw for x in ["品牌", "牌子"]) or any(x in compact for x in ["brand", "manufacturer"]):
        return "brand"
    if any(x in raw for x in ["售价", "价格", "现价"]) or any(x in compact for x in ["price", "currentprice"]):
        return "price"
    if any(x in raw for x in ["评分", "星级"]) or any(x in compact for x in ["rating", "starrating"]):
        return "rating"
    if any(x in raw for x in ["评论数", "评分数", "ratings数"]) or any(x in compact for x in ["reviewcount", "ratingcount", "reviews"]):
        return "reviewCount"
    if any(x in raw for x in ["上架时间", "上线时间", "上市时间"]) or any(x in compact for x in ["launchdate", "availabledate", "firstavailable"]):
        return "launchDate"
    if any(x in raw for x in ["上架天数", "已上架天数"]) or any(x in compact for x in ["daysonsale"]):
        return "daysOnSale"
    if any(x in raw for x in ["大类bsr", "大类排名", "大类目排名"]) or any(x in compact for x in ["categoryrank", "mainrank"]):
        return "categoryRank"
    if any(x in raw for x in ["小类bsr", "小类排名", "小类目排名"]) or any(x in compact for x in ["subcategoryrank", "subrank"]):
        return "subcategoryRank"
    if "排名" in raw or "bsr" in compact or "rank" in compact:
        return "rank"
    if any(x in raw for x in ["变体数", "变体数量"]) or any(x in compact for x in ["variantcount", "variationcount"]):
        return "variantCount"
    if "变体" in raw or "variation" in compact or "variant" in compact:
        return "variants"
    if any(x in raw for x in ["材质", "材料"]) or "material" in compact:
        return "material"
    if "颜色" in raw or "color" in compact or "colour" in compact:
        return "color"
    if any(x in raw for x in ["产品尺寸", "商品尺寸"]) or any(x in compact for x in ["productdimensions", "itemdimensions"]):
        return "productSize"
    if any(x in raw for x in ["产品重量", "商品重量"]) or any(x in compact for x in ["productweight", "itemweight"]):
        return "productWeight"
    if any(x in raw for x in ["包装内容", "包含组件", "配件清单"]) or any(x in compact for x in ["includedcomponents", "packagecontents", "components"]):
        return "includedComponents"
    if "包装尺寸及重量" in raw:
        return "packageInfo"
    if "包装尺寸" in raw or "packagedimensions" in compact or "packagesize" in compact:
        return "packageSize"
    if "包装重量" in raw or "packageweight" in compact or "shippingweight" in compact:
        return "packageWeight"
    if any(x in raw for x in ["详细参数", "产品参数", "规格参数"]) or any(x in compact for x in ["specs", "specifications", "attributes"]):
        return "productParams"
    if any(x in raw for x in ["30天销量", "近30天销量", "月销量"]) or any(x in compact for x in ["saleslast30days", "sales30d", "monthsales"]):
        return "sales30d"
    if any(x in raw for x in ["历史月销", "历史月销量", "月销量趋势"]) or any(x in compact for x in ["monthlysales", "saleshistory"]):
        return "monthlySales"
    if "keepa" in compact:
        return "keepaTrend"
    if any(x in raw for x in ["ai评论分析", "评论分析", "评论总结"]) or any(x in compact for x in ["reviewsummary", "reviewsanalysis"]):
        return "summary"
    if "产品卖点" in raw or "sellingpoints" in compact or "highlights" in compact:
        return "sellingPoints"
    if "好评" in raw or "positive" in compact or "pros" in compact:
        return "positiveReviews"
    if "差评" in raw or "negative" in compact or "cons" in compact or "painpoints" in compact:
        return "negativeReviews"
    if "待改善" in raw or "improvement" in compact or "suggestion" in compact:
        return "improvementPoints"
    if "使用人群" in raw or "targetaudience" in compact or "persona" in compact:
        return "targetAudience"
    if "使用场景" in raw or "usescenarios" in compact or "usecases" in compact:
        return "useScenarios"
    if "优化方向" in raw or "optimization" in compact or "upgrade" in compact:
        return "optimizationDirection"
    if re.fullmatch(r"20\d{2}\d{2}", n) or re.fullmatch(r"20\d{2}年\d{1,2}月", n):
        return "monthlySales"
    return None

def map_review_field(label):
    n = norm_label(label)
    if n in REVIEW_ALIASES:
        return REVIEW_ALIASES.get(n)
    raw = str(label or "").strip().lower()
    compact = re.sub(r"[\W_]+", "", raw)
    if not compact:
        return None
    if "asin" in compact:
        return "asin"
    if compact in {"reviewid", "id"} or "reviewid" in compact or "评论id" in raw or "评价id" in raw:
        return "reviewId"
    if any(x in compact for x in ["reviewerid", "customerid", "userid", "profileid"]):
        return "reviewerId"
    if any(x in compact for x in ["reviewername", "customername", "username", "author", "profile"]):
        return "reviewerName"
    if any(x in compact for x in ["rating", "star", "score"]) or any(x in raw for x in ["评分", "星级", "星等"]):
        return "rating"
    if any(x in compact for x in ["reviewtitle", "title", "headline", "subject"]) or any(x in raw for x in ["评论标题", "评价标题", "标题"]):
        return "title"
    if any(x in compact for x in ["reviewcontent", "reviewtext", "reviewbody", "comment", "content", "body", "text"]) or any(x in raw for x in ["评论内容", "评价内容", "评论正文", "内容", "正文"]):
        return "content"
    if any(x in compact for x in ["reviewdate", "date", "time", "created"] ) or any(x in raw for x in ["评论时间", "评价时间", "日期", "时间"]):
        return "date"
    if any(x in compact for x in ["summary", "analysis", "reviewsummary"]) or any(x in raw for x in ["评论分析", "评论总结", "摘要"]):
        return "summary"
    if any(x in compact for x in ["sellingpoints", "highlights", "pros"]) or "产品卖点" in raw:
        return "sellingPoints"
    if any(x in compact for x in ["positivereviews", "positivetopics", "positivekeywords"]) or "好评" in raw:
        return "positiveReviews"
    if any(x in compact for x in ["negativereviews", "negativetopics", "negativekeywords", "painpoints", "cons"]) or "差评" in raw:
        return "negativeReviews"
    if any(x in compact for x in ["improvementpoints", "improvements", "suggestions", "recommendations"]) or "待改善" in raw:
        return "improvementPoints"
    if any(x in compact for x in ["targetaudience", "audience", "persona", "customers"]) or "使用人群" in raw:
        return "targetAudience"
    if any(x in compact for x in ["usescenarios", "scenarios", "usecases", "scene"]) or "使用场景" in raw:
        return "useScenarios"
    if any(x in compact for x in ["optimizationdirection", "optimization", "upgrade"]) or "优化方向" in raw:
        return "optimizationDirection"
    return None

def review_payload_has_content(review):
    if not review:
        return False
    keys = ("content", "title", "summary", "sellingPoints", "positiveReviews", "negativeReviews", "improvementPoints", "targetAudience", "useScenarios", "optimizationDirection")
    return any(not is_empty(review.get(key)) for key in keys)

def is_date_header(label):
    text = str(label or "").strip()
    return bool(re.match(r"^20\d{2}[-/年]\d{1,2}", text) or re.fullmatch(r"20\d{2}\d{2}", norm_label(label)))

def is_monthly_sales_date_header(label):
    text = str(label or "").strip().lower()
    compact = norm_label(text)
    if not is_date_header(text):
        return False
    if "$" in text or any(token in text or token in compact for token in ["销售额", "销售金额", "营收", "价格", "售价", "revenue", "amount", "price"]):
        return False
    return True

def monthly_sales_priority(sheet_title, labels=None):
    labels = labels or []
    text = (str(sheet_title or "") + " " + " ".join([str(v or "") for v in labels])).lower()
    compact = norm_label(text)
    bad_tokens = ["销售额", "销售金额", "营收", "价格", "售价", "评分", "排名", "bsr", "price", "revenue", "amount", "rating", "rank"]
    good_tokens = ["历史月销量", "历史月销", "月销量趋势", "月销趋势", "monthlysales", "monthsales", "salesvolume", "saleshistory"]
    if any(token.lower() in text or token.lower() in compact for token in bad_tokens):
        return 0
    if not any(token.lower() in text or token.lower() in compact for token in good_tokens):
        return 0
    if "子体" in text or "child" in compact or "variation" in compact:
        return 60
    if "产品历史月销量" in text or "product" in compact:
        return 95
    if "历史月销量" in text or "历史月销" in text:
        return 100
    return 80

def is_monthly_sales_context(sheet_title, labels=None):
    return monthly_sales_priority(sheet_title, labels) > 0

def normalize_item(item):
    if not item:
        return None
    if item.get("categoryRank") and item.get("categoryName"):
        item["category"] = "#" + str(item["categoryRank"]) + " in " + str(item["categoryName"])
    elif item.get("categoryName"):
        item["category"] = item.get("categoryName")
    if item.get("subcategoryRank") and item.get("subcategoryName"):
        item["subcategory"] = "#" + str(item["subcategoryRank"]) + " in " + str(item["subcategoryName"])
    elif item.get("subcategoryName"):
        item["subcategory"] = item.get("subcategoryName")
    if item.get("rank") and not item.get("category"):
        lines = [x.strip() for x in str(item["rank"]).splitlines() if x.strip()]
        item["category"] = lines[0] if lines else item.get("rank")
        if len(lines) > 1:
            item["subcategory"] = lines[1]
    if item.get("variantCount") is not None and not item.get("variants"):
        item["variants"] = str(item["variantCount"]) + " 个变体"
    if (item.get("packageSize") or item.get("packageWeight")) and not item.get("packageInfo"):
        item["packageInfo"] = "\n".join([str(x) for x in [item.get("packageSize"), item.get("packageWeight")] if not is_empty(x)])
    return item

def iter_candidate_files(exts):
    paths = []
    if OVERRIDE:
        candidate = os.path.abspath(OVERRIDE)
        if inside_root(candidate) and os.path.exists(candidate):
            if os.path.isfile(candidate):
                paths = [candidate]
            else:
                for dirpath, dirnames, filenames in os.walk(candidate):
                    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
                    for name in filenames:
                        if name.startswith("~$"):
                            continue
                        if os.path.splitext(name)[1].lower() in exts:
                            paths.append(os.path.join(dirpath, name))
    if not paths:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for name in filenames:
                if name.startswith("~$"):
                    continue
                if os.path.splitext(name)[1].lower() in exts:
                    fp = os.path.join(dirpath, name)
                    try:
                        if os.path.getsize(fp) > 80 * 1024 * 1024:
                            continue
                    except OSError:
                        continue
                    paths.append(fp)
    def priority(fp):
        base = os.path.basename(fp).lower()
        score = 10
        for token in ["竞品", "competitor", "bsr", "last-30", "市场", "销量", "review", "评论", "voc"]:
            if token in base:
                score -= 1
        if "-us" in base or "us-" in base:
            score -= 1
        return (score, len(fp), fp)
    return sorted(dict.fromkeys(paths), key=priority)

def cell(row, idx):
    return clean(row[idx]) if idx < len(row) else None

def parse_table_sheet(ws, source_file):
    results = []
    header_rows = []
    max_header = min(ws.max_row or 0, 30)
    for r_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=max_header, values_only=True), 1):
        labels = [clean(v) for v in row]
        if any(norm_label(v) == "asin" for v in labels if v is not None):
            header_rows.append((r_idx, labels))
    for header_idx, labels in header_rows[:3]:
        asin_cols = [i for i, v in enumerate(labels) if norm_label(v) == "asin"]
        if not asin_cols:
            continue
        asin_col = asin_cols[0]
        mapped = [(i, map_product_field(label), label) for i, label in enumerate(labels)]
        review_mapped = [(i, map_review_field(label), label) for i, label in enumerate(labels)]
        mapped_keys = {k for _, k, _ in mapped if k}
        review_keys_present = {k for _, k, _ in review_mapped if k in {"content", "reviewId", "reviewerId", "reviewerName", "date"}}
        strong_product_keys = {"brand", "image", "url", "price", "categoryRank", "subcategoryRank", "rank", "launchDate", "daysOnSale", "variants", "variantCount", "material", "color", "productSize", "productWeight", "includedComponents", "productParams", "packageInfo", "packageSize", "packageWeight", "sales30d", "monthlySales", "keepaTrend"}
        if review_keys_present and not (mapped_keys & strong_product_keys):
            continue
        date_cols = [i for i, label in enumerate(labels) if is_monthly_sales_date_header(label)]
        monthly_priority = monthly_sales_priority(ws.title, labels)
        monthly_sales_context = monthly_priority > 0
        for row in ws.iter_rows(min_row=header_idx + 1, values_only=True):
            asin_value = cell(row, asin_col)
            if not asin_value:
                continue
            if NEEDLE and str(asin_value).strip().upper() != NEEDLE:
                continue
            item = {"asin": str(asin_value).strip().upper(), "sourceFile": source_file, "sourceSheet": ws.title}
            for i, key, label in mapped:
                if not key:
                    continue
                value = cell(row, i)
                if is_empty(value):
                    continue
                if key == "monthlySales":
                    label_priority = monthly_sales_priority(label, [])
                    if is_date_header(label) and not monthly_sales_context:
                        continue
                    if label_priority or monthly_priority:
                        item["_monthlySalesPriority"] = max(int(item.get("_monthlySalesPriority") or 0), label_priority or monthly_priority)
                    item[key] = unique_join(item.get(key), value)
                else:
                    item[key] = value
            if date_cols:
                monthly = []
                for i in date_cols:
                    value = cell(row, i)
                    if not is_empty(value):
                        monthly.append(str(value))
                if monthly and monthly_sales_context:
                    item["monthlySales"] = ", ".join(monthly)
                    item["monthlyTrend"] = monthly
                    item["_monthlySalesPriority"] = max(int(item.get("_monthlySalesPriority") or 0), monthly_priority)
            review = {"asin": item["asin"], "sourceFile": source_file, "sourceSheet": ws.title}
            for i, key, label in review_mapped:
                if not key:
                    continue
                value = cell(row, i)
                if not is_empty(value):
                    review[key] = value
            if review.get("content") or review.get("title"):
                item.setdefault("_reviews", []).append(review)
            results.append(normalize_item(item))
            if NEEDLE:
                break
    return results

def parse_transposed_sheet(ws, source_file):
    max_rows = min(ws.max_row or 0, 120)
    max_cols = min(ws.max_column or 0, 20)
    rows = list(ws.iter_rows(min_row=1, max_row=max_rows, max_col=max_cols, values_only=True))
    asin_rows = []
    for r, row in enumerate(rows):
        if row and norm_label(row[0]) == "asin":
            asin_rows.append(r)
    results = []
    for asin_row in asin_rows:
        for col in range(1, max_cols):
            asin_value = clean(rows[asin_row][col]) if col < len(rows[asin_row]) else None
            if not asin_value:
                continue
            asin_text = str(asin_value).strip().upper()
            if NEEDLE and asin_text != NEEDLE:
                continue
            item = {"asin": asin_text, "sourceFile": source_file, "sourceSheet": ws.title}
            for row in rows:
                label = clean(row[0]) if row else None
                key = map_product_field(label)
                if not key:
                    continue
                value = clean(row[col]) if col < len(row) else None
                if is_empty(value):
                    continue
                if key == "monthlySales":
                    item["_monthlySalesPriority"] = max(int(item.get("_monthlySalesPriority") or 0), monthly_sales_priority(ws.title, [label]) or 70)
                item[key] = value
            results.append(normalize_item(item))
    return results

def parse_excel_products(fp):
    if load_workbook is None:
        return []
    out = []
    try:
        wb = load_workbook(fp, read_only=True, data_only=False)
        for ws in wb.worksheets:
            out.extend(parse_transposed_sheet(ws, fp))
            out.extend(parse_table_sheet(ws, fp))
    except Exception as exc:
        return []
    return out

def parse_excel_reviews(fp):
    if load_workbook is None:
        return []
    reviews = []
    try:
        wb = load_workbook(fp, read_only=True, data_only=False)
        file_scoped = file_matches_needle(fp)
        review_keys = {"content", "title", "summary", "sellingPoints", "positiveReviews", "negativeReviews", "improvementPoints", "targetAudience", "useScenarios", "optimizationDirection"}
        for ws in wb.worksheets:
            max_header = min(ws.max_row or 0, 30)
            headers = []
            for r_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=max_header, values_only=True), 1):
                labels = [clean(v) for v in row]
                mapped = [(i, map_review_field(label), label) for i, label in enumerate(labels)]
                has_asin = any(k == "asin" for _, k, _ in mapped)
                has_review = any(k in review_keys for _, k, _ in mapped)
                if has_review and (has_asin or file_scoped):
                    headers.append((r_idx, mapped))
            for header_idx, mapped in headers[:3]:
                asin_col = next((i for i, k, _ in mapped if k == "asin"), None)
                if asin_col is None and not file_scoped:
                    continue
                for row in ws.iter_rows(min_row=header_idx + 1, values_only=True):
                    asin_value = cell(row, asin_col) if asin_col is not None else None
                    asin_text = str(asin_value).strip().upper() if asin_value else (NEEDLE if file_scoped else "")
                    if not asin_text:
                        continue
                    if NEEDLE and asin_text != NEEDLE:
                        continue
                    review = {"asin": asin_text, "sourceFile": fp, "sourceSheet": ws.title}
                    for i, key, _ in mapped:
                        if not key:
                            continue
                        value = cell(row, i)
                        if not is_empty(value):
                            review[key] = value
                    if review_payload_has_content(review):
                        reviews.append(review)
    except Exception:
        return []
    return reviews

def parse_json_reviews(fp):
    try:
        with open(fp, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception:
        return []
    reviews = []
    file_scoped = file_matches_needle(fp)
    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            asin = str(node.get("asin") or node.get("ASIN") or node.get("parentAsin") or "").strip().upper()
            if NEEDLE and asin and asin != NEEDLE:
                return
            effective_asin = asin or (NEEDLE if file_scoped else "")
            if NEEDLE and not effective_asin:
                return
            text = node.get("content") or node.get("comment") or node.get("text") or node.get("body") or node.get("评论内容") or node.get("评论正文")
            title = node.get("title") or node.get("reviewTitle") or node.get("评论标题")
            review = {
                    "asin": effective_asin or NEEDLE,
                    "title": clean(title),
                    "content": clean(text),
                    "rating": clean(node.get("rating") or node.get("star") or node.get("星级") or node.get("评分")),
                    "date": clean(node.get("date") or node.get("reviewDate") or node.get("日期")),
                    "sourceFile": fp,
                }
            for key, aliases in {
                "summary": ["summary", "reviewSummary", "commentSummary", "aiSummary", "reviewAnalysis", "AI评论分析", "评论分析"],
                "sellingPoints": ["sellingPoints", "productSellingPoints", "highlights", "产品卖点"],
                "positiveReviews": ["positiveReviews", "positiveKeywordsText", "positiveSummary", "positiveThemesText", "好评点"],
                "negativeReviews": ["negativeReviews", "negativeKeywordsText", "negativeSummary", "painPointsText", "差评点"],
                "improvementPoints": ["improvementPoints", "improvements", "recommendations", "待改善点"],
                "targetAudience": ["targetAudience", "audience", "audienceText", "使用人群"],
                "useScenarios": ["useScenarios", "scenarios", "scenarioText", "使用场景"],
                "optimizationDirection": ["optimizationDirection", "optimization_direction", "优化方向"],
            }.items():
                for alias in aliases:
                    value = node.get(alias)
                    if not is_empty(value):
                        review[key] = value
                        break
            if (not NEEDLE or review["asin"] == NEEDLE) and review_payload_has_content(review):
                reviews.append(review)
            for value in node.values():
                if isinstance(value, (list, dict)):
                    visit(value)
    visit(data)
    return reviews

def parse_jsonl_reviews(fp):
    reviews = []
    file_scoped = file_matches_needle(fp)
    for enc in ["utf-8-sig", "utf-8", "gb18030"]:
        try:
            with open(fp, "r", encoding=enc) as f:
                for line in f:
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        node = json.loads(text)
                    except Exception:
                        continue
                    items = node if isinstance(node, list) else [node]
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        asin = str(item.get("asin") or item.get("ASIN") or item.get("parentAsin") or "").strip().upper()
                        if NEEDLE and asin and asin != NEEDLE:
                            continue
                        effective_asin = asin or (NEEDLE if file_scoped else "")
                        if NEEDLE and not effective_asin:
                            continue
                        review = {"asin": effective_asin or NEEDLE, "sourceFile": fp}
                        for name, value in item.items():
                            key = map_review_field(name)
                            if key and not is_empty(value):
                                review[key] = clean(value)
                        if review_payload_has_content(review):
                            reviews.append(review)
            return reviews
        except Exception:
            continue
    return reviews

def parse_csv_reviews(fp):
    reviews = []
    file_scoped = file_matches_needle(fp)
    for enc in ["utf-8-sig", "utf-8", "gb18030"]:
        try:
            with open(fp, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return []
                mapped = {name: map_review_field(name) for name in reader.fieldnames}
                asin_name = next((n for n, k in mapped.items() if k == "asin"), "")
                for row in reader:
                    asin = str(row.get(asin_name, "")).strip().upper() if asin_name else ""
                    if NEEDLE and asin and asin != NEEDLE:
                        continue
                    effective_asin = asin or (NEEDLE if file_scoped else "")
                    if NEEDLE and not effective_asin:
                        continue
                    review = {"asin": effective_asin or NEEDLE, "sourceFile": fp}
                    for name, key in mapped.items():
                        if key:
                            value = clean(row.get(name))
                            if not is_empty(value):
                                review[key] = value
                    if review_payload_has_content(review):
                        reviews.append(review)
            return reviews
        except Exception:
            continue
    return reviews

def parse_txt_reviews(fp):
    try:
        raw = None
        for enc in ["utf-8-sig", "utf-8", "gb18030"]:
            try:
                with open(fp, "r", encoding=enc) as f:
                    raw = f.read()
                break
            except Exception:
                continue
        if not raw:
            return []
        if NEEDLE and NEEDLE not in raw.upper() and NEEDLE not in os.path.basename(fp).upper():
            return []
        chunks = [x.strip() for x in re.split(r"\n\s*\n|\r\n\s*\r\n", raw) if x.strip()]
        if len(chunks) <= 1:
            chunks = [x.strip() for x in raw.splitlines() if x.strip()]
        reviews = []
        for chunk in chunks:
            if NEEDLE and NEEDLE in chunk.upper():
                chunk = re.sub(re.escape(NEEDLE), "", chunk, flags=re.I).strip(" ：:-")
            if len(chunk) < 6:
                continue
            reviews.append({"asin": NEEDLE, "content": chunk, "sourceFile": fp})
        return reviews
    except Exception:
        return []

def review_signature(review):
    if not review:
        return ""
    asin = str(review.get("asin") or review.get("ASIN") or NEEDLE or "").strip().upper()
    review_id = str(review.get("reviewId") or review.get("review_id") or review.get("id") or "").strip().upper()
    if review_id:
        return "id|" + asin + "|" + review_id
    date = str(review.get("date") or review.get("reviewDate") or "").strip()
    reviewer = str(review.get("reviewerId") or review.get("reviewer_id") or review.get("reviewerName") or review.get("reviewer") or review.get("author") or "").strip().upper()
    title = str(review.get("title") or "").strip()
    content = str(review.get("content") or review.get("text") or review.get("summary") or "").strip()
    rating = str(review.get("rating") or "").strip()
    text = re.sub(r"[\W_]+", "", (title + " " + content).lower())[:260]
    if date and reviewer:
        return "date-user|" + asin + "|" + date + "|" + reviewer
    return "text|" + asin + "|" + rating + "|" + text

def scoped_unique_reviews(reviews):
    out = []
    seen = set()
    for review in reviews or []:
        if not review:
            continue
        asin = str(review.get("asin") or review.get("ASIN") or "").strip().upper()
        if NEEDLE:
            if asin and asin != NEEDLE:
                continue
            review["asin"] = NEEDLE
        key = review_signature(review)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(review)
    return out

if MODE == "market":
    merged = {}
    matched_files = []
    for fp in iter_candidate_files(EXCEL_EXTS):
        if re.search(r"(reviews?|评论|评价|voc)", os.path.basename(fp), re.I):
            continue
        for item in parse_excel_products(fp):
            if not item:
                continue
            asin = str(item.get("asin") or "").upper()
            if NEEDLE and asin != NEEDLE:
                continue
            merged.setdefault(asin, {"asin": asin})
            merge_item(merged[asin], item)
            if fp not in matched_files:
                matched_files.append(fp)
    rows = [normalize_item(v) for v in merged.values() if v]
    print(json.dumps({"rows": rows, "searchedFiles": len(iter_candidate_files(EXCEL_EXTS)), "matchedFiles": matched_files}, ensure_ascii=False))
elif MODE == "reviews":
    reviews = []
    matched_files = []
    for fp in iter_candidate_files(EXCEL_EXTS | TEXT_EXTS):
        ext = os.path.splitext(fp)[1].lower()
        found = []
        if ext in EXCEL_EXTS:
            found = parse_excel_reviews(fp)
        elif ext == ".json":
            found = parse_json_reviews(fp)
        elif ext == ".jsonl":
            found = parse_jsonl_reviews(fp)
        elif ext == ".csv":
            found = parse_csv_reviews(fp)
        elif ext == ".txt":
            found = parse_txt_reviews(fp)
        if found:
            matched_files.append(fp)
            reviews.extend(found)
        if LIMIT and len(reviews) >= LIMIT:
            reviews = reviews[:LIMIT]
            break
    if not reviews:
        fallback_reviews = []
        fallback_files = []
        for fp in iter_candidate_files(EXCEL_EXTS):
            try:
                market_rows = parse_excel_products(fp)
            except Exception:
                continue
            for item in market_rows:
                asin = str(item.get("asin") or "").upper()
                if NEEDLE and asin != NEEDLE:
                    continue
                review = {"asin": asin or NEEDLE, "sourceFile": fp, "sourceSheet": item.get("sourceSheet")}
                for key in ["summary", "sellingPoints", "positiveReviews", "negativeReviews", "improvementPoints", "targetAudience", "useScenarios", "optimizationDirection"]:
                    value = item.get(key)
                    if not is_empty(value):
                        review[key] = value
                if review_payload_has_content(review):
                    fallback_reviews.append(review)
            if fallback_reviews:
                fallback_files.append(fp)
                reviews = fallback_reviews
                matched_files.extend(fallback_files)
                break
    raw_count = len(reviews)
    reviews = scoped_unique_reviews(reviews)
    print(json.dumps({"reviews": reviews, "rawCount": raw_count, "duplicateCount": max(0, raw_count - len(reviews)), "searchedFiles": len(iter_candidate_files(EXCEL_EXTS | TEXT_EXTS)), "matchedFiles": matched_files}, ensure_ascii=False))
else:
    print(json.dumps({"rows": [], "reviews": []}, ensure_ascii=False))
`;

function getLocalData(mode, asin, fileOverride, limit) {
  const cacheKey = [mode, asin || "", fileOverride || "", limit || "", scanRoot].join("|");
  const cached = localDataCache.get(cacheKey);
  if (cached && Date.now() - cached.ts < 5 * 60 * 1000) return cached.data;
  const data = runPythonJson(LOCAL_SCAN_SCRIPT, {
    root: scanRoot,
    mode,
    asin: String(asin || "").trim().toUpperCase(),
    fileOverride: fileOverride || "",
    limit: Number(limit) || 0,
  });
  localDataCache.set(cacheKey, { ts: Date.now(), data });
  return data;
}

function fetchAmazonProductPage(asin) {
  /* v3：脚本新增 sellingPoints 提取后升级缓存键，避免旧缓存缺少五点描述字段 */
  const cacheKey = "amz-page-v3|" + asin;
  const cached = localDataCache.get(cacheKey);
  if (cached && Date.now() - cached.ts < 30 * 60 * 1000) return cached.data;
  const scriptPath = path.join(root, "scripts", "fetch_amazon_product.js");
  const res = spawnSync(process.execPath, [scriptPath, asin], { encoding: "utf8", timeout: 30000, maxBuffer: 40 * 1024 * 1024 });
  if (res.error) throw new Error(res.error.message);
  const stdout = String(res.stdout || "").trim();
  if (!stdout) throw new Error(res.stderr || "亚马逊抓取脚本无输出");
  const data = JSON.parse(stdout);
  if (data && data.found) localDataCache.set(cacheKey, { ts: Date.now(), data });
  /* 亚马逊商品页评论用独立缓存键，30 分钟内直接复用，避免重复抓取 */
  if (data && data.found && Array.isArray(data.reviews) && data.reviews.length) {
    const reviewKey = "amz-page-reviews|" + asin;
    if (!localDataCache.has(reviewKey)) localDataCache.set(reviewKey, { ts: Date.now(), data: data.reviews });
  }
  return data;
}

function writeJson(res, status, payload) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(payload));
}

function serveLocalMarketResearch(url, res) {
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    const fileOverride = String(url.searchParams.get("file") || "").trim();
    writeJson(res, 200, getLocalData("market", asin, fileOverride, 0));
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err), rows: [] });
  }
}

function serveAmazonProductPage(url, res) {
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    if (!/^[A-Z0-9]{10}$/.test(asin)) {
      writeJson(res, 400, { found: false, error: "ASIN 格式无效" });
      return;
    }
    const data = fetchAmazonProductPage(asin);
    writeJson(res, 200, data || { found: false, error: "亚马逊页面抓取失败" });
  } catch (err) {
    writeJson(res, 500, { found: false, error: err.message || String(err) });
  }
}

/* 亚马逊商品页自带的部分真实评论（8~12 条），供评论分析兜底使用 */
function serveAmazonPageReviews(url, res) {
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    if (!/^[A-Z0-9]{10}$/.test(asin)) {
      writeJson(res, 400, { reviews: [], error: "ASIN 格式无效" });
      return;
    }
    fetchAmazonProductPage(asin);
    const cached = localDataCache.get("amz-page-reviews|" + asin);
    const reviews = cached ? cached.data : [];
    writeJson(res, 200, { reviews, searchedFiles: 0, matchedFiles: ["amazon.com/dp/" + asin], source: "amazon-page" });
  } catch (err) {
    writeJson(res, 200, { reviews: [], error: err.message || String(err) });
  }
}

/* 图片代理：浏览器直连亚马逊 CDN 可能被墙，由服务端经代理抓取后转发。 */
const IMAGE_ALLOWED_HOSTS = new Set([
  "m.media-amazon.com",
  "images-na.ssl-images-amazon.com",
  "ecx.images-amazon.com",
]);

function serveImageProxy(url, res) {
  const target = String(url.searchParams.get("url") || "");
  let parsed;
  try { parsed = new URL(target); } catch (err) {
    writeJson(res, 400, { error: "图片地址无效" });
    return;
  }
  if (!/^https?:$/.test(parsed.protocol) || !IMAGE_ALLOWED_HOSTS.has(parsed.hostname)) {
    writeJson(res, 403, { error: "仅允许亚马逊图片域名" });
    return;
  }
  const viaProxy = new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port: 7897, path: target, method: "GET", headers: { "User-Agent": "Mozilla/5.0", "Accept": "image/*" }, timeout: 20000 }, (up) => {
      const chunks = [];
      up.on("data", (c) => chunks.push(c));
      up.on("end", () => resolve({ status: up.statusCode, type: up.headers["content-type"], body: Buffer.concat(chunks) }));
    });
    req.on("timeout", () => req.destroy(new Error("代理请求超时")));
    req.on("error", reject);
    req.end();
  });
  const direct = new Promise((resolve, reject) => {
    const mod = parsed.protocol === "https:" ? https : http;
    const req = mod.request(parsed, { method: "GET", headers: { "User-Agent": "Mozilla/5.0", "Accept": "image/*" }, timeout: 20000 }, (up) => {
      const chunks = [];
      up.on("data", (c) => chunks.push(c));
      up.on("end", () => resolve({ status: up.statusCode, type: up.headers["content-type"], body: Buffer.concat(chunks) }));
    });
    req.on("timeout", () => req.destroy(new Error("直连超时")));
    req.on("error", reject);
    req.end();
  });
  (async () => {
    let result = null;
    try { result = await viaProxy; } catch (err) { /* 代理失败走直连 */ }
    if (!result || result.status !== 200 || !result.body.length) {
      try { result = await direct; } catch (err) { /* 直连也失败 */ }
    }
    if (!result || result.status !== 200 || !result.body.length) {
      writeJson(res, 502, { error: "图片获取失败" });
      return;
    }
    res.writeHead(200, { "Content-Type": result.type || "image/jpeg", "Cache-Control": "public, max-age=86400" });
    res.end(result.body);
  })();
}

function serveLocalReviews(url, res) {
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    const fileOverride = String(url.searchParams.get("file") || "").trim();
    const limit = Number(url.searchParams.get("limit") || 0) || 0;
    const { buildLocalReviewsResponse } = require("./server/amazon-reviews-bridge");
    writeJson(
      res,
      200,
      buildLocalReviewsResponse({
        scanRoot,
        root,
        asin,
        fileOverride,
        limit,
        getLocalData,
      })
    );
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err), reviews: [] });
  }
}

function reviewsApiScript() {
  return path.join(root, "scripts", "reviews_api.py");
}

function runReviewsApi(argv, opts) {
  opts = opts || {};
  const script = reviewsApiScript();
  if (!fs.existsSync(script)) throw new Error("缺少 scripts/reviews_api.py");
  let lastError = "";
  for (const exe of pythonCandidatesForReviews()) {
    const args = /(^|[\\/])py(\.exe)?$/i.test(exe) ? ["-3", script].concat(argv) : [script].concat(argv);
    const res = spawnSync(exe, args, {
      encoding: "utf8",
      timeout: opts.timeoutMs || 120000,
      maxBuffer: 20 * 1024 * 1024,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8", PYTHONUNBUFFERED: "1" }),
      cwd: path.dirname(script),
    });
    if (res.error) {
      lastError = res.error.message;
      continue;
    }
    const stdout = String(res.stdout || "").trim();
    const stderr = String(res.stderr || "").trim();
    if (!stdout) {
      lastError = stderr || ("python exit " + res.status);
      continue;
    }
    try {
      return JSON.parse(stdout.split(/\r?\n/).filter(Boolean).pop());
    } catch (err) {
      lastError = "invalid json: " + stdout.slice(0, 200);
    }
  }
  throw new Error(lastError || "无法调用 amazon-reviews-skill 桥接脚本");
}

function resolveAmazonReviewsSkillRoot() {
  const candidates = [
    path.resolve(root, "amazon-reviews-skill"),
    path.resolve(root, "..", "amazon-reviews-skill"),
    path.resolve(scanRoot, "amazon-reviews-skill"),
    path.resolve(scanRoot, "..", "amazon-reviews-skill"),
  ];
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, "amazon_reviews", "api.py"))) return dir;
  }
  return candidates[0];
}

function spawnReviewsWorker(taskId) {
  const script = reviewsApiScript();
  const skillRoot = resolveAmazonReviewsSkillRoot();
  const logDir = path.join(root, "logs");
  try { fs.mkdirSync(logDir, { recursive: true }); } catch (err) { /* ignore */ }
  const logFile = path.join(logDir, "reviews-worker-" + (taskId || "next") + ".log");
  const argsFor = (exe) => {
    /* Windows py launcher needs -3 before script */
    if (/(^|[\\/])py(\.exe)?$/i.test(exe)) {
      const a = ["-3", script, "run"];
      if (taskId) a.push("--task-id", taskId);
      return a;
    }
    const a = [script, "run"];
    if (taskId) a.push("--task-id", taskId);
    return a;
  };
  let started = null;
  const candidates = pythonCandidatesForReviews();
  if (!candidates.length) {
    return { error: "未找到带 playwright 的 Python（请用系统 python 安装：pip install playwright）", logFile };
  }
  for (const exe of candidates) {
    try {
      const outFd = fs.openSync(logFile, "a");
      fs.writeSync(outFd, "\n---- spawn " + new Date().toISOString() + " exe=" + exe + " task=" + (taskId || "") + " ----\n");
      const child = spawn(exe, argsFor(exe), {
        detached: true,
        stdio: ["ignore", outFd, outFd],
        cwd: fs.existsSync(skillRoot) ? skillRoot : path.dirname(script),
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8", PYTHONUNBUFFERED: "1" }),
        windowsHide: false,
      });
      /* 不要 closeSync(outFd)：detached 子进程仍要用这个 fd 写日志 */
      child.unref();
      started = { pid: child.pid, exe, logFile, skillRoot };
      break;
    } catch (err) {
      started = { error: err.message, exe, logFile, skillRoot };
    }
  }
  return started;
}

async function serveReviewsRun(req, res, url) {
  try {
    let taskId = "";
    if (req.method === "POST") {
      const raw = await readBody(req);
      const body = raw ? JSON.parse(String(raw) || "{}") : {};
      taskId = String(body.taskId || body.id || body.task_id || "").trim();
    } else {
      taskId = String((url && url.searchParams.get("id")) || "").trim();
    }
    if (!taskId) {
      writeJson(res, 400, { ok: false, error: "缺少 task id" });
      return;
    }
    const worker = spawnReviewsWorker(taskId);
    writeJson(res, 200, { ok: !!(worker && worker.pid), taskId, worker });
  } catch (err) {
    writeJson(res, 500, { ok: false, error: err.message || String(err) });
  }
}

async function serveReviewsEnqueue(req, res) {
  try {
    const raw = await readBody(req);
    const body = raw ? JSON.parse(String(raw)) : {};
    const asin = String(body.asin || "").trim().toUpperCase();
    if (!/^[A-Z0-9]{10}$/.test(asin)) {
      writeJson(res, 400, { ok: false, error: "ASIN 无效" });
      return;
    }
    const argv = [
      "enqueue",
      "--asin", asin,
      "--site", String(body.site || body.marketplace || "US"),
      "--account", String(body.accountId || body.account_id || "test-us-2"),
      "--target", String(body.target || 300),
      "--strategy", String(body.strategy || "show_more"),
      "--pace", String(body.pace || "cautious"),
      "--max-pace", String(body.maxPace || body.max_pace || "normal"),
    ];
    if (body.skillRoot) argv.push("--skill-root", String(body.skillRoot));
    const result = runReviewsApi(argv, { timeoutMs: 60000 });
    let worker = null;
    if (body.runWorker !== false && result && result.task && result.task.id) {
      worker = spawnReviewsWorker(result.task.id);
    }
    writeJson(res, 200, Object.assign({ worker }, result));
  } catch (err) {
    writeJson(res, 500, { ok: false, error: err.message || String(err) });
  }
}

function serveReviewsTask(url, res) {
  try {
    const id = String(url.searchParams.get("id") || "").trim();
    if (!id) {
      writeJson(res, 400, { ok: false, error: "缺少 task id" });
      return;
    }
    const argv = ["task", "--id", id];
    const skillRoot = String(url.searchParams.get("skillRoot") || "").trim();
    if (skillRoot) argv.push("--skill-root", skillRoot);
    writeJson(res, 200, runReviewsApi(argv, { timeoutMs: 30000 }));
  } catch (err) {
    writeJson(res, 500, { ok: false, error: err.message || String(err) });
  }
}

function serveReviewsStatus(url, res) {
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    if (!/^[A-Z0-9]{10}$/.test(asin)) {
      writeJson(res, 400, { ok: false, error: "ASIN 无效" });
      return;
    }
    const argv = ["status", "--asin", asin, "--site", String(url.searchParams.get("site") || "US")];
    const skillRoot = String(url.searchParams.get("skillRoot") || "").trim();
    if (skillRoot) argv.push("--skill-root", skillRoot);
    writeJson(res, 200, runReviewsApi(argv, { timeoutMs: 30000 }));
  } catch (err) {
    writeJson(res, 500, { ok: false, error: err.message || String(err) });
  }
}

function parseMultipartUpload(req, body) {
  const type = req.headers["content-type"] || "";
  const match = type.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
  if (!match) throw new Error("上传请求缺少 multipart boundary");
  const boundary = "--" + (match[1] || match[2]);
  const raw = body.toString("latin1");
  const parts = raw.split(boundary);
  for (const part of parts) {
    if (!/filename=/i.test(part)) continue;
    const idx = part.indexOf("\r\n\r\n");
    if (idx < 0) continue;
    const header = part.slice(0, idx);
    let content = part.slice(idx + 4);
    content = content.replace(/\r\n--$/, "").replace(/\r\n$/, "");
    const fileMatch = header.match(/filename="([^"]*)"/i);
    const nameMatch = header.match(/name="([^"]*)"/i);
    const filename = fileMatch && fileMatch[1] ? path.basename(fileMatch[1]).replace(/[^\w.\-\u4e00-\u9fa5]/g, "_") : "reviews-upload.dat";
    return {
      fieldName: nameMatch && nameMatch[1] || "file",
      filename,
      buffer: Buffer.from(content, "latin1"),
    };
  }
  throw new Error("未找到上传文件");
}

async function serveLocalReviewUpload(req, url, res) {
  let saved = "";
  try {
    const asin = String(url.searchParams.get("asin") || "").trim().toUpperCase();
    const limit = Number(url.searchParams.get("limit") || 0) || 0;
    const body = await readBody(req);
    const file = parseMultipartUpload(req, body);
    if (!file.buffer || !file.buffer.length) throw new Error("上传文件为空");
    const uploadDir = path.join(root, ".review_uploads");
    fs.mkdirSync(uploadDir, { recursive: true });
    saved = path.join(uploadDir, Date.now() + "-" + file.filename);
    fs.writeFileSync(saved, file.buffer);
    const data = getLocalData("reviews", asin, saved, limit);
    data.uploadedFile = file.filename;
    data.uploadedSize = file.buffer.length;
    writeJson(res, 200, data);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err), reviews: [] });
  } finally {
    if (saved) {
      try { fs.unlinkSync(saved); } catch (err) { /* ignore */ }
    }
  }
}

async function proxySorftimeMcp(req, res) {
  try {
    const targetUrl = readSorftimeUrl();
    const body = await readBody(req);
    const headers = {
      "Content-Type": req.headers["content-type"] || "application/json",
      "Accept": req.headers.accept || "application/json, text/event-stream",
    };
    if (SORFTIME_MCP_AUTH) headers.Authorization = SORFTIME_MCP_AUTH;
    const upstream = await fetch(targetUrl, {
      method: "POST",
      headers,
      body,
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(text);
  } catch (err) {
    writeJson(res, 500, { error: err.message || String(err) });
  }
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:3000");

  if (url.pathname === "/api/local/market-research") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveLocalMarketResearch(url, res);
    return;
  }

  if (url.pathname === "/api/local/reviews") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveLocalReviews(url, res);
    return;
  }

  if (url.pathname === "/api/reviews/run") {
    if (req.method !== "POST" && req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await serveReviewsRun(req, res, url);
    return;
  }
  if (url.pathname === "/api/reviews/enqueue") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await serveReviewsEnqueue(req, res);
    return;
  }

  if (url.pathname === "/api/reviews/task") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveReviewsTask(url, res);
    return;
  }

  if (url.pathname === "/api/reviews/status") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveReviewsStatus(url, res);
    return;
  }

  if (url.pathname === "/api/local/reviews/upload") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await serveLocalReviewUpload(req, url, res);
    return;
  }

  if (url.pathname === "/api/amazon/product-page") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveAmazonProductPage(url, res);
    return;
  }

  if (url.pathname === "/api/image-proxy") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveImageProxy(url, res);
    return;
  }

  if (url.pathname === "/api/amazon/page-reviews") {
    if (req.method !== "GET") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    serveAmazonPageReviews(url, res);
    return;
  }

  if (url.pathname === "/api/mcp/sorftime") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await proxySorftimeMcp(req, res);
    return;
  }

  if (url.pathname === "/api/mcp/xiyou") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await proxyXiyouMcp(req, res);
    return;
  }

  if (url.pathname === "/api/mcp/sif") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await proxySifMcp(req, res);
    return;
  }

  if (url.pathname === "/api/mcp/lingxing") {
    if (req.method !== "POST") {
      res.writeHead(405);
      res.end("Method Not Allowed");
      return;
    }
    await proxyLingXingMcp(req, res);
    return;
  }

  const requestPath = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
  const filePath = path.resolve(root, "." + requestPath);
  if (!filePath.startsWith(root + path.sep) && filePath !== root) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    const headers = { "Content-Type": mime[path.extname(filePath).toLowerCase()] || "application/octet-stream" };
    /* HTML 禁缓存，保证修复后的前端代码立刻生效 */
    if (path.extname(filePath) === ".html") headers["Cache-Control"] = "no-store";
    res.writeHead(200, headers);
    res.end(data);
  });
}).listen(3000, "127.0.0.1", () => {
  console.log("Serving " + root + " at http://127.0.0.1:3000");
  console.log("Local file scan root: " + scanRoot);
});
