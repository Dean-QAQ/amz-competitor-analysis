const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname);
const port = Number(process.env.PORT || 3002);
const host = process.env.HOST || "0.0.0.0";

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

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
};

const XIYOU_MCP_URL = "https://mcp.xydc.com/mcp";
const XIYOU_MCP_KEY = process.env.XIYOU_MCP_KEY || "";
const SORFTIME_MCP_URL = process.env.SORFTIME_MCP_URL || "";
const SORFTIME_MCP_AUTH = process.env.SORFTIME_MCP_AUTH || "";
const SIF_MCP_URL = "https://mcp.sif.com/mcp";
const SIF_MCP_KEY = process.env.SIF_MCP_KEY || "";
const LINGXING_MCP_URL = "https://openmcp.lingxing.com/mcp-servers/lingxing-mcp";
let LINGXING_MCP_KEY = process.env.LINGXING_MCP_KEY || "";

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
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
    send(res, 500, JSON.stringify({ error: err.message || String(err) }), { "Content-Type": "application/json; charset=utf-8" });
  }
}

async function proxySorftimeMcp(req, res) {
  try {
    const body = await readBody(req);
    const upstream = await fetch(SORFTIME_MCP_URL, {
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
    send(res, 500, JSON.stringify({ error: err.message || String(err) }), { "Content-Type": "application/json; charset=utf-8" });
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
    send(res, 500, JSON.stringify({ error: err.message || String(err) }), { "Content-Type": "application/json; charset=utf-8" });
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
    send(res, 500, JSON.stringify({ error: err.message || String(err) }), { "Content-Type": "application/json; charset=utf-8" });
  }
}

function safeJoin(base, target) {
  const targetPath = path.resolve(base, "." + target);
  if (!targetPath.startsWith(base)) return null;
  return targetPath;
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, Object.assign({ "Content-Type": "text/plain; charset=utf-8" }, headers));
  res.end(body);
}

  const server = http.createServer((req, res) => {
    if (req.url && /^\/api\/mcp\/(xiyou|sorftime|sif|lingxing)/.test(req.url)) {
      if (req.method !== "POST") return send(res, 405, "Method Not Allowed");
      const handler = req.url.startsWith("/api/mcp/xiyou") ? proxyXiyouMcp
        : req.url.startsWith("/api/mcp/sorftime") ? proxySorftimeMcp
        : req.url.startsWith("/api/mcp/sif") ? proxySifMcp
        : proxyLingXingMcp;
      handler(req, res).catch((err) => send(res, 500, JSON.stringify({ error: err.message || String(err) }), { "Content-Type": "application/json; charset=utf-8" }));
      return;
    }
    let urlPath = req.url || "/";
  try {
    urlPath = decodeURIComponent(urlPath.split("?")[0]);
  } catch (err) {}
  if (urlPath === "/") urlPath = "/index.html";
  const target = safeJoin(root, urlPath);
  if (!target) return send(res, 403, "Forbidden");

  fs.stat(target, (err, stat) => {
    if (err) {
      return send(res, 404, "Not Found");
    }
    const filePath = stat.isDirectory() ? path.join(target, "index.html") : target;
    fs.readFile(filePath, (readErr, data) => {
      if (readErr) return send(res, 404, "Not Found");
      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { "Content-Type": mimeTypes[ext] || "application/octet-stream" });
      res.end(data);
    });
  });
});

server.listen(port, host, () => {
  console.log(`Serving ${root} at http://${host}:${port}`);
});
