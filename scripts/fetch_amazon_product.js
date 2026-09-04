#!/usr/bin/env node
/* 用途：抓取亚马逊商品页 HTML，解析主图/标题/品牌/价格/评分/评论数。
 * 只抓公开商品页，不访问评论页（评论页需登录）。走本机代理 127.0.0.1:7897。 */
"use strict";
const { execFileSync } = require("child_process");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { URL } = require("url");

const asin = String(process.argv[2] || "").trim().toUpperCase();
if (!/^[A-Z0-9]{10}$/.test(asin)) {
  console.log(JSON.stringify({ found: false, error: "ASIN 格式无效" }));
  process.exit(0);
}

const target = new URL("https://www.amazon.com/dp/" + asin);
const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.9",
};

function fetchOnce(opts) {
  return new Promise((resolve, reject) => {
    const req = http.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf8") }));
    });
    req.on("timeout", () => req.destroy(new Error("请求超时")));
    req.on("error", reject);
    req.end();
  });
}

/* 从商品页 HTML 的评论区 medley 中解析真实评论（商品页自带 8~12 条置顶评论） */
function extractReviews(html, asin) {
  const reviews = [];
  const containerRe = /data-hook="reviewContainer"/g;
  const positions = [];
  let m;
  while ((m = containerRe.exec(html))) positions.push(m.index);
  positions.push(html.length);
  const clean = (s) => String(s || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;|&apos;|&rsquo;/g, "'")
    .replace(/&ldquo;|&rdquo;/g, "\"")
    .replace(/&mdash;|&ndash;/g, "-")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  for (let i = 0; i < positions.length - 1; i++) {
    const chunk = html.slice(positions[i], positions[i + 1]);
    const ratingM = chunk.match(/([0-9.]+) out of 5 stars/);
    const titleM = chunk.match(/data-hook="reviewTitle"[\s\S]*?<span[^>]*>([\s\S]*?)<\/span>/);
    const dateM = chunk.match(/data-hook="review-date"[\s\S]*?>([\s\S]*?)<\/span>/);
    const textIdx = chunk.indexOf("data-hook=\"reviewRichContentContainer\"");
    let text = null;
    if (textIdx >= 0) {
      const openIdx = chunk.indexOf(">", textIdx) + 1;
      let depth = 1;
      let j = openIdx;
      while (j < chunk.length && depth > 0) {
        const nextTag = chunk.indexOf("<", j);
        if (nextTag < 0) break;
        if (chunk.startsWith("<div", nextTag)) { depth++; j = nextTag + 4; }
        else if (chunk.startsWith("</div", nextTag)) {
          depth--;
          j = nextTag + 5;
          if (depth === 0) { text = chunk.slice(openIdx, nextTag); break; }
        } else { j = nextTag + 1; }
      }
      if (text === null) text = chunk.slice(openIdx, openIdx + 5000);
    }
    const content = clean(text);
    if (!content || content.length < 15) continue;
    reviews.push({
      asin,
      title: clean(titleM && titleM[1]) || null,
      rating: ratingM ? parseFloat(ratingM[1]) : null,
      date: clean(dateM && dateM[1]) || null,
      content,
      source: "amazon-page",
    });
  }
  return reviews;
}

/* 从商品页 HTML 解析产品参数（Product Overview / detailBullets 表格）和包装信息。
 * 只提取真实存在的字段，抓不到就不返回，不编造。 */
function extractProductAttributes(html) {
  const clean = (s) => String(s || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;|&apos;|&rsquo;/g, "'")
    .replace(/&ldquo;|&rdquo;/g, "\"")
    .replace(/&mdash;|&ndash;/g, "-")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const productParams = {};
  const packageInfo = {};

  const parseTableRows = (section) => {
    if (!section) return;
    const rowRe = /<tr[\s\S]*?<\/tr>/g;
    let m;
    while ((m = rowRe.exec(section))) {
      const row = m[0];
      const thMatch = row.match(/<th[^>]*>([\s\S]*?)<\/th>/);
      const tdMatch = row.match(/<td[^>]*>([\s\S]*?)<\/td>/);
      if (!thMatch || !tdMatch) continue;
      const key = clean(thMatch[1]).replace(/[:：]\s*$/, "");
      const value = clean(tdMatch[1]);
      if (key && value && key.length < 60 && value.length < 200) {
        productParams[key] = value;
        if (/package\s*dimensions|package\s*size/i.test(key)) packageInfo.packageSize = value;
        if (/item\s*weight|package\s*weight|shipping\s*weight/i.test(key)) packageInfo.packageWeight = value;
      }
    }
  };

  const findSection = (id) => {
    const idx = html.indexOf(id);
    if (idx < 0) return "";
    const start = html.indexOf("<table", idx);
    if (start < 0) return "";
    const end = html.indexOf("</table>", start);
    if (end < 0) return "";
    return html.slice(start, end);
  };

  parseTableRows(findSection("prodDetails"));
  parseTableRows(findSection("productDetails_detailBullets_sections1"));
  parseTableRows(findSection("productDetails_techSpec_section_1"));
  if (!Object.keys(productParams).length) {
    const tables = html.match(/<table[^>]*class="[^"]*prodDetTable[^"]*"[\s\S]*?<\/table>/g) || [];
    tables.forEach((table) => parseTableRows(table));
  }

  const detailIdx = html.indexOf("detailBullets_feature_div");
  if (detailIdx >= 0) {
    const ulStart = html.indexOf("<ul", detailIdx);
    const ulEnd = html.indexOf("</ul>", ulStart);
    if (ulStart >= 0 && ulEnd > ulStart) {
      const section = html.slice(ulStart, ulEnd);
      const liRe = /<li><span class="a-text-bold">([\s\S]*?)<\/span>\s*([^<]+)</g;
      let li;
      while ((li = liRe.exec(section))) {
        const key = clean(li[1]).replace(/[:：]\s*$/, "");
        const value = clean(li[2]);
        if (key && value && key.length < 60 && value.length < 200) {
          productParams[key] = value;
          if (/package\s*dimensions|package\s*size/i.test(key)) packageInfo.packageSize = value;
          if (/item\s*weight|package\s*weight|shipping\s*weight/i.test(key)) packageInfo.packageWeight = value;
        }
      }
    }
  }
  if (!Object.keys(productParams).length) {
    const attrRe = /<th[^>]*class="[^"]*prodDetSectionEntry[^"]*"[^>]*>([\s\S]*?)<\/th>\s*<td[^>]*class="[^"]*prodDetAttrValue[^"]*"[^>]*>([\s\S]*?)<\/td>/g;
    let m;
    while ((m = attrRe.exec(html))) {
      const key = clean(m[1]).replace(/[:：]\s*$/, "");
      const value = clean(m[2]);
      if (key && value && key.length < 60 && value.length < 200) {
        productParams[key] = value;
        if (/package\s*dimensions|package\s*size/i.test(key)) packageInfo.packageSize = value;
        if (/item\s*weight|package\s*weight|shipping\s*weight/i.test(key)) packageInfo.packageWeight = value;
      }
    }
  }

  return { productParams, packageInfo };
}

/* 通过 curl 抓取（本机 Clash 代理 127.0.0.1:7897）。
 * 用 Node http 模块走同一代理会 502，curl 走得通，实测稳定。 */
function extractProductAttributesV2(html) {
  const clean = (s) => String(s || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;|&apos;|&rsquo;/g, "'")
    .replace(/&ldquo;|&rdquo;/g, "\"")
    .replace(/&mdash;|&ndash;/g, "-")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const productParams = {};
  const packageInfo = {};
  const seen = new Set();
  const record = (keyRaw, valueRaw) => {
    const key = clean(keyRaw).replace(/[:：]\s*$/, "").trim();
    const value = clean(valueRaw);
    if (!key || !value || key.length > 80 || value.length > 500) return;
    const sig = key + "|" + value;
    if (seen.has(sig)) return;
    seen.add(sig);
    productParams[key] = value;
    if (!packageInfo.packageSize && /package\s*dimensions|package\s*size|shipping\s*dimensions/i.test(key)) packageInfo.packageSize = value;
    if (!packageInfo.packageWeight && /package\s*weight|shipping\s*weight/i.test(key)) packageInfo.packageWeight = value;
  };
  const scan = (re) => {
    let m;
    while ((m = re.exec(html))) record(m[1], m[2]);
  };

  scan(/<th[^>]*class="[^"]*prodDetSectionEntry[^"]*"[^>]*>([\s\S]*?)<\/th>\s*<td[^>]*class="[^"]*prodDetAttrValue[^"]*"[^>]*>([\s\S]*?)<\/td>/g);
  scan(/<li[^>]*>\s*<span class="a-text-bold">([\s\S]*?)<\/span>\s*([\s\S]*?)(?=<li|<\/ul>|<\/div>|<\/section>|$)/g);
  scan(/<tr[^>]*>\s*<th[^>]*>([\s\S]*?)<\/th>\s*<td[^>]*>([\s\S]*?)<\/td>\s*<\/tr>/g);
  scan(/<tr[^>]*>\s*<td[^>]*class="[^"]*label[^"]*"[^>]*>([\s\S]*?)<\/td>\s*<td[^>]*class="[^"]*value[^"]*"[^>]*>([\s\S]*?)<\/td>\s*<\/tr>/g);
  scan(/<span[^>]*class="[^"]*prodDetSectionEntry[^"]*"[^>]*>([\s\S]*?)<\/span>\s*<span[^>]*class="[^"]*prodDetAttrValue[^"]*"[^>]*>([\s\S]*?)<\/span>/g);

  if (!packageInfo.packageSize) {
    packageInfo.packageSize = productParams["Package Dimensions"]
      || productParams["Item Package Dimensions L x W x H"]
      || productParams["Shipping Dimensions"]
      || null;
  }
  if (!packageInfo.packageWeight) {
    packageInfo.packageWeight = productParams["Package Weight"] || productParams["Shipping Weight"] || null;
  }

  return { productParams, packageInfo };
}

/* 从商品页 #feature-bullets 区域提取真实五点描述原文；抓不到时返回空数组，不虚构。 */
function extractFeatureBullets(html) {
  const items = [];
  const seen = new Set();
  const container = html.match(/<div[^>]*id="feature-bullets"[^>]*>([\s\S]*?)<\/div>/i);
  const scope = container ? container[1] : html;
  const liRe = /<li[^>]*>([\s\S]*?)<\/li>/gi;
  let m;
  while ((m = liRe.exec(scope))) {
    const text = String(m[1] || "")
      .replace(/<span[^>]*class="[^"]*a-list-item[^"]*"[^>]*>/gi, "")
      .replace(/<[^>]+>/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&quot;/g, "\"")
      .replace(/&#39;|&apos;|&rsquo;/g, "'")
      .replace(/&ldquo;|&rdquo;/g, "\"")
      .replace(/&mdash;|&ndash;/g, "-")
      .replace(/&nbsp;/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    const sig = text.toLowerCase();
    if (!text || text.length < 4 || text.length > 360 || seen.has(sig)) continue;
    if (/^(see more|see less|videos for this product)$/i.test(text)) continue;
    seen.add(sig);
    items.push(text);
  }
  return items.slice(0, 12);
}

function fetchViaCurl(proxyUrl) {
  const tmpFile = path.join(os.tmpdir(), "amz_page_" + Date.now() + ".html");
  const args = [
    "-s", "-L", "--max-time", "35",
    "-A", HEADERS["User-Agent"],
    "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-o", tmpFile,
    "-w", "%{http_code}",
    target.toString(),
  ];
  if (proxyUrl) args.splice(4, 0, "-x", proxyUrl);
  const code = execFileSync("curl.exe", args, { encoding: "utf8", timeout: 45000, windowsHide: true });
  const status = parseInt(String(code).trim(), 10) || 0;
  let body = "";
  try { body = fs.readFileSync(tmpFile, "utf8"); } catch (err) { /* 读取失败时返回空 */ }
  try { fs.unlinkSync(tmpFile); } catch (err) { /* 忽略 */ }
  return { status, body };
}

(async () => {
  let result = null;
  try { result = fetchViaCurl("http://127.0.0.1:7897"); } catch (err) { result = null; }
  if (!result || result.status !== 200) {
    try { result = fetchViaCurl(""); } catch (err) { result = null; }
  }
  if (!result || result.status !== 200) {
    console.log(JSON.stringify({ found: false, error: "亚马逊页面返回 " + (result ? result.status : "网络失败") }));
    return;
  }
  const html = result.body;
  const cleanImageUrl = (value) => String(value || "")
    .replace(/\\u002F/gi, "/")
    .replace(/\\\//g, "/")
    .replace(/&amp;/g, "&")
    .trim();
  const patterns = [
    /"(?:hiRes|large)"\s*:\s*"([^"]*m\.media-amazon\.com[^"]+)"/,
    /"landingImage"\s*:\s*"([^"]*m\.media-amazon\.com[^"]+)"/,
    /data-old-hires="([^"]*m\.media-amazon\.com[^"]+)"/,
    /<img[^>]+id="landingImage"[^>]+src="([^"]+)"/,
    /<meta property="og:image" content="([^"]+)"/,
  ];
  let imageUrl = null;
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) { imageUrl = cleanImageUrl(m[1]); break; }
  }
  const titleMatch = html.match(/<span id="productTitle"[^>]*>([\s\S]*?)<\/span>/);
  const title = titleMatch ? titleMatch[1].trim().replace(/\s+/g, " ") : null;
  const ratingMatch = html.match(/([0-9.]+) out of 5 stars/);
  const rating = ratingMatch ? parseFloat(ratingMatch[1]) : null;
  const reviewCountMatch = html.match(/([0-9,]+) (?:global ratings|ratings|reviews)/i);
  const reviewCount = reviewCountMatch ? parseInt(reviewCountMatch[1].replace(/,/g, ""), 10) : null;
  const brandMatch = html.match(/<a id="bylineInfo"[^>]*>([\s\S]*?)<\/a>/);
  let brand = null;
  if (brandMatch) {
    brand = brandMatch[1].replace(/<[^>]+>/g, "").replace(/^(?:Visit the|Brand:)\s*/i, "").replace(/\s*(?:Store|Brand)\s*$/i, "").trim();
  }
  const priceMatch = html.match(/class="a-offscreen">\$([0-9.,]+)/);
  const price = priceMatch ? parseFloat(priceMatch[1].replace(/,/g, "")) : null;
  const reviews = extractReviews(html, asin);
  const attrs = extractProductAttributesV2(html);
  const sellingPoints = extractFeatureBullets(html);
  console.log(JSON.stringify({
    found: !!(imageUrl || title),
    imageUrl, title, rating, reviewCount, brand, price,
    sellingPoints,
    reviews,
    productParams: attrs.productParams,
    packageInfo: attrs.packageInfo,
  }));
})().catch((err) => console.log(JSON.stringify({ found: false, error: err.message })));
