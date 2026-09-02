# -*- coding: utf-8 -*-
"""Generate the single-file competitor comparison page from the Excel template."""
import glob
import json
import os
from openpyxl import load_workbook


SRC = max(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.xlsx")), key=os.path.getsize)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

wb = load_workbook(SRC, data_only=True)
ws = wb["竞品分析"]


def cell(row, col):
    v = ws.cell(row=row, column=col).value
    if v is None:
        return None
    s = str(v)
    if s.startswith("=") and "DISPIMG" in s:
        return None
    if s.strip() in ("", "/", "-", "—"):
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    return s.strip()


raw_data = []
analysis_data = []

for col in range(2, 8):
    asin = cell(3, col)
    if not asin:
        continue
    rank_text = cell(8, col)
    rank_cat = rank_sub = None
    if rank_text:
        parts = [p.strip() for p in rank_text.split("\n") if p.strip()]
        rank_cat = parts[0] if parts else None
        rank_sub = parts[1] if len(parts) > 1 else None

    raw_data.append(
        {
            "brand": cell(1, col),
            "asin": asin,
            "url": cell(4, col),
            "title": cell(5, col),
            "price": None,
            "originalPrice": None,
            "discount": None,
            "launchDate": cell(7, col),
            "rankCategory": rank_cat,
            "rankSubcategory": rank_sub,
            "rating": cell(9, col),
            "reviewCount": cell(10, col),
            "variants": None,
            "productParams": cell(12, col),
            "packageInfo": cell(13, col),
            "sales30d": None,
            "monthlySales": None,
            "keepaTrend": None,
            "aiCommentScreenshot": cell(17, col),
        }
    )
    analysis_data.append(
        {
            "asin": asin,
            "sellingPoints": cell(18, col),
            "positiveReviews": cell(19, col),
            "negativeReviews": cell(20, col),
            "improvementPoints": cell(21, col),
            "targetAudience": cell(22, col),
            "useScenarios": cell(23, col),
            "optimizationDirection": cell(24, col),
        }
    )

data_json = json.dumps({"raw": raw_data, "analysis": analysis_data}, ensure_ascii=False)

TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>亚马逊竞品自动化分析系统</title>
    <style>
      :root {
        --bg: #f2f4f7;
        --card: #ffffff;
        --line: #e3e8ef;
        --text: #1f2937;
        --muted: #7c8a9a;
        --blue: #e8f1fb;
        --blue-border: #c4dcf5;
        --gray: #eef1f4;
        --gray-border: #dde3ea;
        --red: #fdecec;
        --red-border: #f3c9c9;
        --orange: #fdf2e4;
        --orange-border: #f0d4ac;
        --green: #eaf6f0;
        --green-border: #c8e6d4;
        --gold: #f59e0b;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; }
      html { font-size: 16px; }
      body {
        background: var(--bg);
        color: var(--text);
        font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
      }
      .page {
        max-width: 1200px;
        margin: 0 auto;
        padding: 28px 18px 48px;
      }

      .top-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 20px 22px 16px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
      }
      .top-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      .top-head h1 { font-size: 22px; font-weight: 700; letter-spacing: 0; }
      .top-head .sub { font-size: 12px; color: var(--muted); margin-top: 6px; }
      .query-row { display: flex; align-items: center; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
      .query-row input {
        flex: 1 1 420px;
        height: 40px;
        padding: 0 14px;
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        font-size: 14px;
        color: var(--text);
        background: #fbfcfe;
        outline: none;
      }
      .query-row input:focus { border-color: #6fa8dc; box-shadow: 0 0 0 3px rgba(111, 168, 220, 0.18); }
      .btn {
        height: 40px;
        padding: 0 18px;
        border-radius: 6px;
        border: 1px solid transparent;
        font-size: 14px;
        cursor: pointer;
        white-space: nowrap;
        transition: background 0.15s ease, border-color 0.15s ease;
      }
      .btn-primary { background: #2563eb; color: #fff; }
      .btn-primary:hover { background: #1d4ed8; }
      .btn-secondary { background: #fff; border-color: #cfd8e3; color: #374151; }
      .btn-secondary:hover { border-color: #9fb2c8; background: #f8fafc; }
      .btn-ghost { background: #fff; border-color: #d7e3f1; color: #2563eb; }
      .btn-ghost:hover { background: #eef5fd; }
      .query-row .actions { display: flex; gap: 10px; }
      .status-line {
        margin-top: 14px;
        padding: 10px 14px;
        background: #f7f9fc;
        border: 1px solid #e6ebf2;
        border-radius: 6px;
        font-size: 13px;
        color: #4b5563;
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        align-items: center;
      }
      .status-line .dot { width: 8px; height: 8px; border-radius: 50%; background: #34d399; display: inline-block; margin-right: 6px; }
      .status-line .source { color: var(--muted); }

      .table-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
      }
      .table-scroll { overflow-x: auto; overflow-y: visible; }
      table { border-collapse: separate; border-spacing: 0; width: max-content; min-width: 100%; }

      th, td { border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
      .sticky { position: sticky; left: 0; z-index: 4; }
      thead th { z-index: 7; }
      thead .sticky { z-index: 8; }

      .dim-head {
        min-width: 176px;
        width: 176px;
        background: #f8fafc;
        padding: 14px 12px;
        font-size: 14px;
        font-weight: 700;
        color: #334155;
        text-align: center;
        vertical-align: middle;
        border-bottom: 2px solid #cdd8e4;
      }
      .product-head {
        min-width: 320px;
        width: 320px;
        padding: 13px 14px;
        background: #f8fafc;
        text-align: left;
        vertical-align: top;
        border-bottom: 2px solid #cdd8e4;
      }
      .head-brand { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; }
      .head-brand .badge { font-size: 11px; font-weight: 500; color: #6b7280; background: #eef2f6; border: 1px solid #dfe6ee; padding: 1px 7px; border-radius: 999px; }
      .asin-copy-row { margin-top: 7px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
      .asin-copy {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #fff;
        border: 1px solid #cfd8e3;
        border-radius: 5px;
        padding: 4px 9px;
        font-size: 13px;
        color: #2563eb;
        cursor: pointer;
        font-family: Consolas, "Courier New", monospace;
      }
      .asin-copy:hover { background: #eef5fd; border-color: #6fa8dc; }
      .asin-copy svg { flex: 0 0 auto; }
      .head-link { font-size: 12px; color: var(--muted); text-decoration: none; }
      .head-link:hover { color: #2563eb; text-decoration: underline; }
      .unmatched { color: #ef4444; font-size: 12px; font-weight: 600; }

      .group-row th, .group-row td { padding: 0; border-bottom: 1px solid var(--line); }
      .group-label {
        min-width: 176px;
        width: 176px;
        text-align: left;
        padding: 10px 14px;
        font-size: 14px;
        font-weight: 700;
      }
      .group-span { text-align: left; padding: 10px 14px; font-size: 12px; color: rgba(31, 41, 55, 0.45); }
      .tone-blue { background: var(--blue); }
      .tone-blue .group-span { color: #2563eb; }
      .tone-gray { background: var(--gray); }
      .tone-gray .group-span { color: #64748b; }
      .tone-red { background: var(--red); }
      .tone-red .group-span { color: #b91c1c; }
      .tone-orange { background: var(--orange); }
      .tone-orange .group-span { color: #b45309; }
      .tone-green { background: var(--green); }
      .tone-green .group-span { color: #047857; }
      .group-label.tone-blue { border-right: 1px solid var(--blue-border); }
      .group-label.tone-gray { border-right: 1px solid var(--gray-border); }
      .group-label.tone-red { border-right: 1px solid var(--red-border); }
      .group-label.tone-orange { border-right: 1px solid var(--orange-border); }
      .group-label.tone-green { border-right: 1px solid var(--green-border); }

      .row-label {
        min-width: 176px;
        width: 176px;
        background: #ffffff;
        padding: 12px 14px;
        font-size: 13px;
        font-weight: 700;
        color: #374151;
        text-align: left;
        vertical-align: top;
        line-height: 1.5;
      }
      .cell {
        min-width: 320px;
        width: 320px;
        padding: 12px 14px;
        font-size: 13px;
        line-height: 1.7;
        vertical-align: top;
        background: #ffffff;
        color: #374151;
      }
      .cell .rich-text { white-space: pre-wrap; word-break: break-word; }
      .cell .empty { color: #a3aebc; }
      .cell .muted { color: var(--muted); font-size: 12px; }
      .cell .label-note { color: var(--muted); font-size: 11px; margin-top: 6px; }

      .col-hot { background: #fff9e8 !important; }
      .col-hot .row-label { background: #ffffff; }
      .col-hot .img-box, .col-hot .shot-box, .col-hot .chart-box { border-color: #e5cf8f; }

      .img-box {
        aspect-ratio: 1 / 1;
        max-width: 170px;
        border: 1px dashed #b9c6d4;
        border-radius: 6px;
        background: #f6f8fb;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: #64748b;
        font-size: 13px;
        text-align: center;
        padding: 10px;
      }
      .img-box .brand-mark {
        width: 42px; height: 42px;
        border-radius: 8px;
        background: #dbe7f5;
        color: #2563eb;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 17px;
      }
      .shot-box {
        min-height: 96px;
        border: 1px dashed #b9c6d4;
        border-radius: 6px;
        background: #f6f8fb;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 6px;
        color: #64748b;
        font-size: 12px;
        padding: 10px;
        text-align: center;
      }
      .shot-box svg { opacity: 0.65; }

      .price-box { display: flex; flex-direction: column; gap: 6px; }
      .price-value { font-size: 26px; font-weight: 800; color: #dc2626; letter-spacing: 0; }
      .price-empty { color: #a3aebc; font-size: 26px; font-weight: 700; }
      .discount-chip { display: inline-block; background: #fee2e2; color: #b91c1c; font-size: 12px; padding: 2px 8px; border-radius: 999px; }

      .star-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
      .star-track { position: relative; font-size: 15px; letter-spacing: 2px; color: #e2e8f0; line-height: 1; }
      .star-fill { position: absolute; left: 0; top: 0; overflow: hidden; white-space: nowrap; color: var(--gold); }
      .rating-num { font-size: 17px; font-weight: 800; color: #1f2937; }

      .mini-bars { display: flex; align-items: flex-end; gap: 4px; height: 34px; margin-top: 10px; }
      .mini-bars span { width: 7px; border-radius: 2px 2px 0 0; background: #9cc2e8; }
      .chart-box {
        border: 1px dashed #b9c6d4;
        border-radius: 6px;
        background: #fbfcfe;
        padding: 12px 10px 8px;
        margin-top: 8px;
      }
      .chart-box .chart-title { font-size: 11px; color: #64748b; margin-bottom: 8px; text-align: center; }
      .bar-chart { display: flex; align-items: flex-end; gap: 6px; height: 92px; padding: 0 6px; }
      .bar-chart span { flex: 1; border-radius: 3px 3px 0 0; background: #7fb0e4; min-height: 6px; }
      .keepa-svg { width: 100%; height: 110px; display: block; }
      .legend { display: flex; gap: 12px; justify-content: center; margin-top: 6px; font-size: 11px; color: #64748b; }
      .legend i { display: inline-block; width: 10px; height: 3px; margin-right: 5px; vertical-align: middle; }

      .tone-tag { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-bottom: 6px; }
      .tone-green-tag { background: #dcf5e8; color: #047857; }
      .tone-red-tag { background: #fde3e3; color: #b91c1c; }
      .tone-orange-tag { background: #fdeeda; color: #b45309; }
      .tone-blue-tag { background: #e0eefc; color: #1d4ed8; }

      .foot-note { margin-top: 14px; font-size: 12px; color: var(--muted); text-align: center; }

      #toast {
        position: fixed;
        left: 50%;
        bottom: 34px;
        transform: translateX(-50%) translateY(16px);
        background: #111827;
        color: #fff;
        font-size: 13px;
        padding: 10px 18px;
        border-radius: 6px;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.18s ease, transform 0.18s ease;
        z-index: 999;
        max-width: 80vw;
      }
      #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

      #tip {
        position: fixed;
        max-width: 460px;
        max-height: 70vh;
        overflow: auto;
        background: #1f2937;
        color: #f3f4f6;
        font-size: 12px;
        line-height: 1.7;
        padding: 10px 14px;
        border-radius: 6px;
        white-space: pre-wrap;
        word-break: break-word;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.28);
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.12s ease;
      }
      #tip.show { opacity: 1; }

      @media (max-width: 700px) {
        .page { padding: 14px 8px 30px; }
        .top-card { padding: 16px 14px 12px; }
        .top-head h1 { font-size: 18px; }
        .query-row input { flex-basis: 100%; }
        .query-row .btn { flex: 1 1 auto; }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <header class="top-card">
        <div class="top-head">
          <div>
            <h1>亚马逊竞品自动化分析系统</h1>
            <p class="sub">6 竞品横向对比 · 模块与行维度 1:1 对齐 Excel 分析模板</p>
          </div>
        </div>
        <div class="query-row">
          <input
            id="asinInput"
            type="text"
            autocomplete="off"
            placeholder="请输入ASIN，最多6个，用英文逗号分隔，如 B0C5DLQNDW,XXXXXXX,XXXXXXX"
          />
          <div class="actions">
            <button class="btn btn-primary" id="queryBtn" type="button">查询</button>
            <button class="btn btn-secondary" id="resetBtn" type="button">重置</button>
            <button class="btn btn-ghost" id="copyBtn" type="button">复制报告</button>
          </div>
        </div>
        <div class="status-line">
          <span><span class="dot"></span><span id="statusAsins">已加载：--</span></span>
          <span class="source">当前使用模拟数据，后续可接入MCP获取真实亚马逊数据</span>
        </div>
      </header>

      <section class="table-card">
        <div class="table-scroll" id="tableScroll">
          <table id="compareTable">
            <thead id="tableHead"></thead>
            <tbody id="tableBody"></tbody>
          </table>
        </div>
      </section>

      <p class="foot-note">横向滚动查看全部竞品；点击 ASIN 可复制，悬停长文本可查看完整内容。</p>
    </main>
    <div id="toast" role="status" aria-live="polite"></div>
    <div id="tip"></div>

    <script>
      const DATA = __DATA_JSON__;

      const DEFAULT_ASINS = DATA.raw.map((p) => p.asin);
      const rawMap = {};
      const analysisMap = {};
      DATA.raw.forEach((p) => { rawMap[p.asin] = p; });
      DATA.analysis.forEach((p) => { analysisMap[p.asin] = p; });

      const MODULES = [
        {
          key: "basic",
          label: "基础商品信息",
          tone: "blue",
          span: "图片 / ASIN / 标题 / 售价 / 上线时间 / 排名 / 评分 / 评论数 / 截图",
          rows: ["image", "asin", "title", "price", "launch", "rank", "rating", "reviews", "entityShot", "params", "package"],
        },
        {
          key: "sales",
          label: "销量数据模块",
          tone: "gray",
          span: "30天销量 / 历史月销 / Keepa趋势",
          rows: ["sales30d", "monthly", "keepa"],
        },
        {
          key: "ai",
          label: "AI评论分析模块",
          tone: "red",
          span: "AI标引 / 产品卖点 / 好评点 / 差评点 / 待改善点",
          rows: ["aiShot", "selling", "positive", "negative", "improve"],
        },
        {
          key: "audience",
          label: "使用人群&场景模块",
          tone: "orange",
          span: "使用人群 / 使用场景",
          rows: ["audience", "scenarios"],
        },
        {
          key: "optimize",
          label: "优化方向模块",
          tone: "green",
          span: "A/B/C 级改进建议（支持未来 MCP 分级数据）",
          rows: ["optimize"],
        },
      ];

      const ROW_LABELS = {
        image: "图片",
        asin: "ASIN",
        title: "标题",
        price: "售价",
        launch: "上线时间",
        rank: "排名",
        rating: "评分",
        reviews: "评论数",
        entityShot: "实体截图占位",
        params: "产品参数信息",
        package: "包装尺寸及重量",
        sales30d: "30天销量（畅销变体）",
        monthly: "历史月销",
        keepa: "Keepa趋势",
        aiShot: "AI评论分析标引",
        selling: "产品卖点",
        positive: "好评点",
        negative: "差评点",
        improve: "待改善点",
        audience: "使用人群",
        scenarios: "使用场景",
        optimize: "优化方向",
      };

      const BAR_HEIGHTS = ["32%", "58%", "45%", "74%", "52%", "86%", "62%", "95%", "70%"];

      function esc(s) {
        return String(s ?? "").replace(/[&<>"']/g, (c) => (
          { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
        ));
      }

      function fmt(n) {
        if (n === null || n === undefined || n === "") return null;
        if (typeof n === "number") return n.toLocaleString("en-US");
        return String(n);
      }

      function empty() {
        return '<span class="empty">--</span>';
      }

      function rich(text) {
        const t = esc(text);
        return '<div class="rich-text" data-tip="' + t + '">' + t + "</div>";
      }

      function starLine(rating) {
        const r = Number(rating) || 0;
        const pct = Math.max(0, Math.min(100, (r / 5) * 100));
        return (
          '<div class="star-line"><span class="rating-num">' + esc(rating) + "</span>" +
          '<span class="star-track">★★★★★<span class="star-fill" style="width:' + pct + '%">★★★★★</span></span>' +
          "</div>"
        );
      }

      function miniBars() {
        return (
          '<div class="mini-bars" aria-hidden="true">' +
          BAR_HEIGHTS.slice(0, 6).map((h) => "<span style=\"height:" + h + "\"></span>").join("") +
          "</div>"
        );
      }

      function barChart() {
        return (
          '<div class="chart-box" aria-label="历史月销趋势模拟占位">' +
          '<div class="chart-title">历史月销趋势 · 模拟占位</div>' +
          '<div class="bar-chart">' +
          BAR_HEIGHTS.map((h) => "<span style=\"height:" + h + "\"></span>").join("") +
          "</div></div>"
        );
      }

      function keepaChart() {
        return (
          '<div class="chart-box" aria-label="Keepa 趋势模拟占位">' +
          '<div class="chart-title">Keepa 价格 / BSR 趋势 · 模拟占位</div>' +
          '<svg class="keepa-svg" viewBox="0 0 280 110" role="img">' +
          '<polyline fill="none" stroke="#3b82f6" stroke-width="2" points="8,78 40,70 72,82 104,58 136,64 168,44 200,52 232,30 272,38" />' +
          '<polyline fill="none" stroke="#f59e0b" stroke-width="2" points="8,28 40,36 72,30 104,48 136,42 168,62 200,56 232,74 272,68" stroke-dasharray="4 3" />' +
          "</svg>" +
          '<div class="legend"><span><i style="background:#3b82f6"></i>价格</span><span><i style="background:#f59e0b"></i>BSR</span></div>' +
          "</div>"
        );
      }

      function shotBox(text, svg) {
        return (
          '<div class="shot-box">' +
          svg +
          "<span>" + esc(text) + "</span>" +
          "</div>"
        );
      }

      const IMAGE_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.6"/><path d="M21 15l-5-5L5 21"/></svg>';
      const SHOT_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 3l18 18M21 3L3 21"/></svg>';
      const AI_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/><circle cx="12" cy="12" r="3.2"/></svg>';

      const RENDERERS = {
        image: (c) => {
          if (!c.matched) return empty();
          const initial = c.brand ? String(c.brand).charAt(0).toUpperCase() : "?";
          return (
            '<div class="img-box" data-tip="' + esc(c.brand || "") + ' 商品主图（Excel 内嵌图片占位）">' +
            '<span class="brand-mark">' + esc(initial) + "</span>" +
            "<span>" + esc(c.brand || "商品主图") + "</span>" +
            '<span class="label-note">商品主图占位</span>' +
            "</div>"
          );
        },
        asin: (c) => {
          if (!c.matched) return empty();
          const link = c.url
            ? '<a class="head-link" href="' + esc(c.url) + '" target="_blank" rel="noopener">打开商品链接</a>'
            : "";
          return (
            '<div class="asin-block">' +
            '<button class="asin-copy" type="button" data-asin="' + esc(c.asin) + '">' +
            "<svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"9\" y=\"9\" width=\"12\" height=\"12\" rx=\"2\"/><path d=\"M5 15V5a2 2 0 0 1 2-2h10\"/></svg>" +
            esc(c.asin) + "</button><span class=\"muted\">点击复制</span><br>" + link +
            "</div>"
          );
        },
        title: (c) => (c.matched && c.title ? rich(c.title) : empty()),
        price: (c) => {
          if (!c.matched) return empty();
          if (c.price === null || c.price === undefined) {
            return (
              '<div class="price-box">' +
              '<span class="price-empty">--</span>' +
              '<span class="muted">价格截图占位（Excel 内嵌图片）</span>' +
              "</div>"
            );
          }
          const priceHtml = '<span class="price-value">$' + esc(c.price) + "</span>";
          const origHtml = c.originalPrice ? '<span class="muted">原价 $' + esc(c.originalPrice) + "</span>" : "";
          const discHtml = c.discount ? '<span class="discount-chip">-' + esc(c.discount) + "%</span>" : "";
          return '<div class="price-box">' + priceHtml + origHtml + discHtml + "</div>";
        },
        launch: (c) => (c.matched && c.launchDate ? rich(c.launchDate) : empty()),
        rank: (c) => {
          if (!c.matched) return empty();
          const cat = c.rankCategory ? esc(c.rankCategory) : "--";
          const sub = c.rankSubcategory ? esc(c.rankSubcategory) : "--";
          return '<div class="rich-text"><div>大类：' + cat + "</div><div>小类：" + sub + "</div></div>";
        },
        rating: (c) => (c.matched && c.rating !== null && c.rating !== undefined ? starLine(c.rating) : empty()),
        reviews: (c) => (c.matched && c.reviewCount !== null && c.reviewCount !== undefined ? '<span style="font-size:16px;font-weight:700">' + esc(fmt(c.reviewCount)) + "</span>" : empty()),
        entityShot: (c) => (c.matched ? shotBox("实体截图占位（Excel 内嵌图片）", SHOT_SVG) : empty()),
        params: (c) => (c.matched && c.productParams ? rich(c.productParams) : empty()),
        package: (c) => (c.matched && c.packageInfo ? rich(c.packageInfo) : empty()),
        sales30d: (c) => {
          if (!c.matched) return empty();
          const num = c.sales30d === null || c.sales30d === undefined
            ? '<span class="empty">--</span>'
            : '<span style="font-size:18px;font-weight:800">' + esc(fmt(c.sales30d)) + "</span>";
          return '<div>' + num + '<span class="muted"> 件 / 30天</span></div>' + miniBars() + '<div class="label-note">迷你趋势 · 模拟占位</div>';
        },
        monthly: (c) => (c.matched ? barChart() : empty()),
        keepa: (c) => (c.matched ? keepaChart() : empty()),
        aiShot: (c) => (c.matched ? shotBox("AI 评论分析截图占位（Excel 内嵌图片）", AI_SVG) : empty()),
        selling: (c) => (c.matched && c.sellingPoints ? '<span class="tone-tag tone-blue-tag">产品卖点</span>' + rich(c.sellingPoints) : empty()),
        positive: (c) => (c.matched && c.positiveReviews ? '<span class="tone-tag tone-green-tag">好评点</span>' + rich(c.positiveReviews) : empty()),
        negative: (c) => (c.matched && c.negativeReviews ? '<span class="tone-tag tone-red-tag">差评点</span>' + rich(c.negativeReviews) : empty()),
        improve: (c) => (c.matched && c.improvementPoints ? '<span class="tone-tag tone-orange-tag">待改善点</span>' + rich(c.improvementPoints) : empty()),
        audience: (c) => (c.matched && c.targetAudience ? '<span class="tone-tag tone-orange-tag">使用人群</span>' + rich(c.targetAudience) : empty()),
        scenarios: (c) => (c.matched && c.useScenarios ? '<span class="tone-tag tone-orange-tag">使用场景</span>' + rich(c.useScenarios) : empty()),
        optimize: (c) => {
          if (!c.matched || !c.optimizationDirection) return empty();
          const dir = c.optimizationDirection;
          if (typeof dir === "string") return '<span class="tone-tag tone-green-tag">优化方向</span>' + rich(dir);
          const blocks = [];
          if (dir.a) blocks.push('<div class="tone-tag tone-green-tag">A级 · 核心必备</div>' + rich(dir.a));
          if (dir.b) blocks.push('<div class="tone-tag tone-blue-tag">B级 · 体验优化</div>' + rich(dir.b));
          if (dir.c) blocks.push('<div class="tone-tag tone-orange-tag">C级 · 长期迭代</div>' + rich(dir.c));
          return blocks.join('<div style="height:10px"></div>');
        },
      };

      function buildCompetitor(asin) {
        const raw = rawMap[asin] || {};
        const ana = analysisMap[asin] || {};
        return Object.assign({}, raw, ana, { asin, matched: !!rawMap[asin] });
      }

      function renderHead(asins) {
        const head = document.getElementById("tableHead");
        head.innerHTML =
          "<tr>" +
          '<th class="dim-head sticky">分析维度</th>' +
          asins
            .map((asin, i) => {
              const c = buildCompetitor(asin);
              const brand = c.matched ? esc(c.brand) : "未匹配";
              const badge = c.matched
                ? '<span class="badge">' + (i + 1) + "</span>"
                : '<span class="unmatched">未匹配</span>';
              const link = c.matched && c.url
                ? '<a class="head-link" href="' + esc(c.url) + '" target="_blank" rel="noopener">Amazon 链接</a>'
                : "";
              return (
                '<th class="product-head" data-col="' + i + '">' +
                '<div class="head-brand">' + badge + "<span>" + brand + "</span></div>" +
                '<div class="asin-copy-row">' +
                '<button class="asin-copy" type="button" data-asin="' + esc(asin) + '">' +
                "<svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><rect x=\"9\" y=\"9\" width=\"12\" height=\"12\" rx=\"2\"/><path d=\"M5 15V5a2 2 0 0 1 2-2h10\"/></svg>" +
                esc(asin) + "</button>" + link +
                "</div></th>"
              );
            })
            .join("") +
          "</tr>";
      }

      function renderBody(asins) {
        const body = document.getElementById("tableBody");
        let html = "";
        MODULES.forEach((mod) => {
          html +=
            '<tr class="group-row">' +
            '<th class="group-label sticky tone-' + mod.tone + '">' + esc(mod.label) + "</th>" +
            '<td class="group-span tone-' + mod.tone + '" colspan="' + asins.length + '">' + esc(mod.span) + "</td>" +
            "</tr>";
          mod.rows.forEach((rowId) => {
            html +=
              '<tr class="data-row">' +
              '<th class="row-label sticky">' + esc(ROW_LABELS[rowId] || rowId) + "</th>" +
              asins
                .map((asin, i) => {
                  const c = buildCompetitor(asin);
                  const renderer = RENDERERS[rowId];
                  const content = renderer ? renderer(c) : empty();
                  return '<td class="cell" data-col="' + i + '">' + content + "</td>";
                })
                .join("") +
              "</tr>";
          });
        });
        body.innerHTML = html;
      }

      function render(asins) {
        renderHead(asins);
        renderBody(asins);
        document.getElementById("statusAsins").textContent = "已加载：" + asins.length + " 个 ASIN（" + asins.join("、") + "）";
      }

      function parseAsins(input) {
        const parts = String(input || "")
          .split(/[,，;；\s]+/)
          .map((s) => s.trim())
          .filter(Boolean);
        if (parts.length > 6) {
          showToast("最多支持 6 个 ASIN，已取前 6 个");
          return parts.slice(0, 6);
        }
        return parts;
      }

      function doQuery() {
        const asins = parseAsins(document.getElementById("asinInput").value);
        if (!asins.length) {
          showToast("请输入至少 1 个 ASIN");
          return;
        }
        render(asins);
        showToast("已查询 " + asins.length + " 个竞品");
      }

      function doReset() {
        document.getElementById("asinInput").value = DEFAULT_ASINS.join(",");
        render(DEFAULT_ASINS);
        showToast("已重置为 Excel 示例竞品");
      }

      let toastTimer = null;
      function showToast(msg) {
        const el = document.getElementById("toast");
        el.textContent = msg;
        el.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => el.classList.remove("show"), 1800);
      }

      async function copyText(text, msg) {
        try {
          await navigator.clipboard.writeText(text);
        } catch (err) {
          const ta = document.createElement("textarea");
          ta.value = text;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        }
        showToast(msg || "已复制");
      }

      function buildReport() {
        const asins = parseAsins(document.getElementById("asinInput").value);
        const lines = [];
        lines.push("亚马逊竞品自动化分析系统 - 横向对比报告");
        lines.push("数据来源：当前使用模拟数据，后续可接入 MCP 获取真实亚马逊数据");
        lines.push("");
        asins.forEach((asin, idx) => {
          const c = buildCompetitor(asin);
          lines.push("【竞品 " + (idx + 1) + "】" + (c.matched ? c.brand + " / " : "") + asin);
          if (!c.matched) {
            lines.push("  暂无该商品数据");
            lines.push("");
            return;
          }
          if (c.title) lines.push("  标题：" + c.title);
          if (c.price !== null && c.price !== undefined) lines.push("  售价：$" + c.price);
          if (c.launchDate) lines.push("  上线时间：" + c.launchDate);
          if (c.rankCategory || c.rankSubcategory) lines.push("  排名：" + (c.rankCategory || "--") + " / " + (c.rankSubcategory || "--"));
          if (c.rating !== null && c.rating !== undefined) lines.push("  评分：" + c.rating);
          if (c.reviewCount !== null && c.reviewCount !== undefined) lines.push("  评论数：" + c.reviewCount);
          if (c.productParams) lines.push("  产品参数信息：" + c.productParams);
          if (c.packageInfo) lines.push("  包装尺寸及重量：" + c.packageInfo);
          const anaFields = [
            ["产品卖点", c.sellingPoints],
            ["好评点", c.positiveReviews],
            ["差评点", c.negativeReviews],
            ["待改善点", c.improvementPoints],
            ["使用人群", c.targetAudience],
            ["使用场景", c.useScenarios],
            ["优化方向", typeof c.optimizationDirection === "string" ? c.optimizationDirection : null],
          ];
          anaFields.forEach(([label, val]) => {
            if (val) lines.push("  " + label + "：\n" + val);
          });
          lines.push("");
        });
        return lines.join("\n");
      }

      let currentCol = null;
      function clearColumnHighlight() {
        if (currentCol === null) return;
        document.querySelectorAll('[data-col="' + currentCol + '"]').forEach((el) => el.classList.remove("col-hot"));
        currentCol = null;
      }

      document.getElementById("compareTable").addEventListener("mouseover", (e) => {
        const cell = e.target.closest("[data-col]");
        if (!cell) {
          clearColumnHighlight();
          return;
        }
        const col = cell.dataset.col;
        if (col === currentCol) return;
        clearColumnHighlight();
        currentCol = col;
        document.querySelectorAll('[data-col="' + col + '"]').forEach((el) => el.classList.add("col-hot"));
      });

      document.addEventListener("mouseover", (e) => {
        const t = e.target.closest("[data-tip]");
        const tip = document.getElementById("tip");
        if (t) {
          tip.textContent = t.dataset.tip;
          tip.classList.add("show");
          const rect = t.getBoundingClientRect();
          const left = Math.min(rect.left, window.innerWidth - 480);
          const top = Math.min(rect.bottom + 8, window.innerHeight - 80);
          tip.style.left = Math.max(8, left) + "px";
          tip.style.top = Math.max(8, top) + "px";
        } else {
          tip.classList.remove("show");
        }
      });

      document.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-asin]");
        if (btn) {
          copyText(btn.dataset.asin, "已复制：" + btn.dataset.asin);
        }
      });

      document.getElementById("queryBtn").addEventListener("click", doQuery);
      document.getElementById("resetBtn").addEventListener("click", doReset);
      document.getElementById("copyBtn").addEventListener("click", () => {
        const text = buildReport();
        copyText(text, "报告已复制");
      });
      document.getElementById("asinInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") doQuery();
      });

      function mergeRaw(list) {
        const arr = Array.isArray(list) ? list : Object.values(list || {});
        arr.forEach((p) => {
          if (p && p.asin) rawMap[p.asin] = Object.assign({}, rawMap[p.asin], p);
        });
      }

      function mergeAnalysis(list) {
        const arr = Array.isArray(list) ? list : Object.values(list || {});
        arr.forEach((p) => {
          if (p && p.asin) analysisMap[p.asin] = Object.assign({}, analysisMap[p.asin], p);
        });
      }

      /*
       * MCP 预留适配入口：
       * 1. setRawData 只替换模块1-3原始商品/销量/Keepa数据，模块4-6与页面结构不变；
       * 2. setAnalysis 可选替换模块4-6 AI 分析产物；
       * 3. render 用于数据更新后重绘当前查询列。
       */
      window.mcpCompetitorAdapter = {
        setRawData: (list) => {
          mergeRaw(list);
          render(currentAsins());
        },
        setAnalysis: (list) => {
          mergeAnalysis(list);
          render(currentAsins());
        },
        getRawData: () => Object.assign({}, rawMap),
        getAnalysis: () => Object.assign({}, analysisMap),
        render: () => render(currentAsins()),
      };
      window.mcpImport = (payload) => {
        if (payload && payload.raw) window.mcpCompetitorAdapter.setRawData(payload.raw);
        if (payload && payload.analysis) window.mcpCompetitorAdapter.setAnalysis(payload.analysis);
      };

      function currentAsins() {
        return parseAsins(document.getElementById("asinInput").value);
      }

      doReset();
    </script>
  </body>
</html>
'''

html = TEMPLATE.replace("__DATA_JSON__", data_json)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("Generated:", OUT)
print("Size:", os.path.getsize(OUT), "bytes")
print("Competitors:", len(raw_data))
