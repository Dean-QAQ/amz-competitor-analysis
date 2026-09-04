#!/usr/bin/env node
/* 用途：抓取亚马逊商品页 HTML，解析主图/标题/品牌/价格/评分/评论数。
 * 只抓公开商品页，不访问评论页（评论页需登录）。走本机代理 127.0.0.1:7897。 */
"use strict";
const https = require("https");
const http = require("http");
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

function fetchViaProxy() {
  return fetchOnce({ host: "127.0.0.1", port: 7897, path: target.toString(), method: "GET", headers: HEADERS, timeout: 20000 });
}

function fetchDirect() {
  const opts = { hostname: target.hostname, path: target.pathname, method: "GET", headers: HEADERS, timeout: 20000 };
  return new Promise((resolve, reject) => {
    const req = https.request(opts, (res) => {
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
    try { result = await fetchDirect(); } catch (err) { /* 直连也失败时使用最后结果 */ }
  }
  if (!result || result.status !== 200) {
    console.log(JSON.stringify({ found: false, error: "亚马逊页面返回 " + (result ? result.status : "网络失败") }));
    return;
  }
  const html = result.body;
  const patterns = [
    /"hiRes":"(https:\/\/m\.media-amazon\.com\/images\/I\/[^"]+)"/,
    /"large":"(https:\/\/m\.media-amazon\.com\/images\/I\/[^"]+)"/,
    /<meta property="og:image" content="([^"]+)"/,
  ];
  let imageUrl = null;
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) { imageUrl = m[1].replace(/\\/g, ""); break; }
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
  console.log(JSON.stringify({ found: !!(imageUrl || title), imageUrl, title, rating, reviewCount, brand, price, reviews }));
})().catch((err) => console.log(JSON.stringify({ found: false, error: err.message })));
