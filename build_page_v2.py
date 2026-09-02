# -*- coding: utf-8 -*-
"""Generate the single-file multi-provider competitor comparison page."""
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
      .page { max-width: 1200px; margin: 0 auto; padding: 28px 18px 48px; }

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
      .top-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
      .source-picker { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #4b5563; }
      .source-picker select {
        height: 34px;
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        padding: 0 10px;
        font-size: 13px;
        background: #fbfcfe;
        color: var(--text);
        outline: none;
      }
      .icon-btn {
        height: 34px;
        padding: 0 12px;
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        background: #fff;
        color: #374151;
        font-size: 13px;
        cursor: pointer;
        white-space: nowrap;
      }
      .icon-btn:hover { background: #f8fafc; border-color: #9fb2c8; }
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
      .btn-small { height: 28px; padding: 0 12px; font-size: 12px; border-radius: 5px; }
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

      .progress-wrap {
        margin-top: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 13px;
        color: #4b5563;
      }
      .progress-wrap[hidden] { display: none; }
      .progress-bar {
        flex: 1 1 220px;
        height: 8px;
        border-radius: 999px;
        background: #e5eaf1;
        overflow: hidden;
      }
      .progress-bar i {
        display: block;
        height: 100%;
        width: 0;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #38bdf8);
        transition: width 0.2s ease;
      }

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
      .head-brand .state-chip { font-size: 11px; font-weight: 500; color: #2563eb; background: #e0eefc; border-radius: 999px; padding: 1px 8px; }
      .head-brand .state-chip.error { color: #b91c1c; background: #fde3e3; }
      .head-brand .state-chip.done { color: #047857; background: #dcf5e8; }
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
      .col-status { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
      .degrade-banner {
        background: var(--orange);
        border: 1px solid var(--orange-border);
        color: #b45309;
        font-size: 12px;
        line-height: 1.5;
        padding: 6px 9px;
        border-radius: 5px;
      }
      .error-banner {
        background: var(--red);
        border: 1px solid var(--red-border);
        color: #b91c1c;
        font-size: 12px;
        padding: 6px 9px;
        border-radius: 5px;
        cursor: pointer;
      }
      .error-banner:hover { background: #fadcdc; }
      .cached-chip { font-size: 11px; color: #6b7280; }

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
      .cell-error {
        border: 1px dashed #e2b6b6;
        border-radius: 6px;
        background: #fff7f7;
        color: #b91c1c;
        padding: 18px 12px;
        text-align: center;
        font-size: 13px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
      }

      .skeleton { pointer-events: none; }
      .sk {
        display: block;
        height: 12px;
        border-radius: 4px;
        background: linear-gradient(90deg, #eef2f6 25%, #e2e8f0 37%, #eef2f6 63%);
        background-size: 400% 100%;
        animation: shimmer 1.2s ease infinite;
        margin-bottom: 9px;
      }
      .sk.w60 { width: 60%; }
      .sk.w80 { width: 80%; }
      .sk.w40 { width: 40%; }
      .sk.img { width: 110px; height: 110px; border-radius: 6px; }
      @keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }

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
        overflow: hidden;
      }
      .img-box img { max-width: 100%; max-height: 150px; object-fit: contain; border-radius: 4px; }
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
      .mock-chip {
        display: inline-block;
        background: #eef2f6;
        border: 1px solid #dfe6ee;
        color: #6b7280;
        font-size: 11px;
        padding: 1px 7px;
        border-radius: 999px;
        vertical-align: middle;
      }

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

      .modal-mask {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.45);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 900;
        padding: 18px;
      }
      .modal-mask[hidden] { display: none; }
      .modal {
        width: min(760px, 96vw);
        max-height: 90vh;
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.3);
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .modal-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid var(--line);
      }
      .modal-head h2 { font-size: 17px; font-weight: 700; }
      .modal-close { border: 0; background: none; font-size: 22px; color: #6b7280; cursor: pointer; line-height: 1; padding: 4px; }
      .tabs { display: flex; gap: 2px; padding: 0 16px; border-bottom: 1px solid var(--line); background: #f8fafc; }
      .tab {
        border: 0;
        background: none;
        padding: 12px 14px;
        font-size: 13px;
        color: #6b7280;
        cursor: pointer;
        border-bottom: 2px solid transparent;
      }
      .tab.active { color: #2563eb; font-weight: 700; border-bottom-color: #2563eb; }
      .tab-body { padding: 16px 20px 8px; overflow-y: auto; }
      .tab-panel { display: none; }
      .tab-panel.active { display: block; }
      .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 16px; }
      .form-grid label, .field label { display: flex; flex-direction: column; gap: 6px; font-size: 12px; color: #4b5563; font-weight: 600; }
      .field { margin-bottom: 14px; }
      .field input, .form-grid input, .form-grid select, .field select {
        height: 36px;
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        padding: 0 10px;
        font-size: 13px;
        color: var(--text);
        background: #fff;
        outline: none;
        width: 100%;
      }
      .field input:focus, .form-grid input:focus { border-color: #6fa8dc; box-shadow: 0 0 0 3px rgba(111, 168, 220, 0.15); }
      .password-row { display: flex; gap: 8px; }
      .password-row input { flex: 1; }
      .password-row .btn { height: 36px; }
      .hint { font-size: 12px; color: var(--muted); margin-top: 12px; line-height: 1.7; }
      .test-row { display: flex; align-items: center; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
      .status-light { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; }
      .light { width: 10px; height: 10px; border-radius: 50%; background: #cbd5e1; display: inline-block; }
      .light.green { background: #22c55e; }
      .light.red { background: #ef4444; }
      .light.gray { background: #cbd5e1; }
      .modal-foot {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding: 14px 20px;
        border-top: 1px solid var(--line);
        background: #f8fafc;
      }

      @media (max-width: 700px) {
        .page { padding: 14px 8px 30px; }
        .top-card { padding: 16px 14px 12px; }
        .top-head h1 { font-size: 18px; }
        .query-row input { flex-basis: 100%; }
        .query-row .btn { flex: 1 1 auto; }
        .form-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <header class="top-card">
        <div class="top-head">
          <div>
            <h1>亚马逊竞品自动化分析系统</h1>
            <p class="sub">6 竞品横向对比 · 可插拔多数据源架构（模拟 / 卖家精灵MCP / PA-API / Keepa）</p>
          </div>
          <div class="top-tools">
            <label class="source-picker">
              <span>数据源</span>
              <select id="sourceSelect"></select>
            </label>
            <button class="icon-btn" id="configBtn" type="button">⚙️ 数据源配置</button>
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
          <span><span class="dot"></span><span id="statusAsins">尚未查询</span></span>
          <span id="sourceStatus" class="source">当前使用模拟数据，后续可接入MCP获取真实亚马逊数据</span>
        </div>
        <div class="progress-wrap" id="progressWrap" hidden>
          <div class="progress-bar"><i id="progressFill"></i></div>
          <span id="progressText">正在查询 0/0...</span>
          <button class="btn btn-secondary btn-small" id="cancelBtn" type="button">取消查询</button>
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

    <div class="modal-mask" id="configModal" hidden>
      <div class="modal" role="dialog" aria-modal="true" aria-label="数据源配置">
        <div class="modal-head">
          <h2>数据源配置</h2>
          <button class="modal-close" id="configClose" type="button" aria-label="关闭">×</button>
        </div>
        <div class="tabs">
          <button class="tab active" type="button" data-tab="general">通用设置</button>
          <button class="tab" type="button" data-tab="sellersprite">卖家精灵MCP</button>
          <button class="tab" type="button" data-tab="pa">亚马逊 PA-API</button>
          <button class="tab" type="button" data-tab="keepa">Keepa API</button>
        </div>
        <div class="tab-body">
          <div class="tab-panel active" id="tab-general">
            <div class="form-grid">
              <label>站点选择
                <select id="siteSelect">
                  <option value="US">US - 美国</option>
                  <option value="CA">CA - 加拿大</option>
                  <option value="UK">UK - 英国</option>
                  <option value="DE">DE - 德国</option>
                  <option value="JP">JP - 日本</option>
                  <option value="AU">AU - 澳大利亚</option>
                </select>
              </label>
              <label>超时时间（秒）
                <input id="timeoutInput" type="number" min="1" max="120" step="1" />
              </label>
              <label>重试次数
                <input id="retriesInput" type="number" min="0" max="5" step="1" />
              </label>
              <label>并发请求数
                <input id="concurrencyInput" type="number" min="1" max="6" step="1" />
              </label>
              <label>请求间隔（毫秒）
                <input id="intervalInput" type="number" min="0" max="5000" step="100" />
              </label>
              <label>混合模式
                <select id="modeSelect">
                  <option value="single">关闭（单一数据源）</option>
                  <option value="mixed">启用（PA-API + 卖家精灵 + Keepa）</option>
                </select>
              </label>
            </div>
            <p class="hint" id="mixedHint">混合模式映射：基础信息 = PA-API，销量 = 卖家精灵，趋势 = Keepa，评论/参数 = 模拟数据。未配置的数据源会自动降级到主数据源或模拟数据。</p>
          </div>

          <div class="tab-panel" id="tab-sellersprite">
            <div class="field">
              <label>MCP 服务器地址
                <input id="mcpUrl" type="text" placeholder="https://your-mcp-server.example.com" />
              </label>
            </div>
            <div class="field">
              <label>API Key
                <span class="password-row">
                  <input id="mcpKey" type="password" placeholder="填入卖家精灵 MCP API Key" autocomplete="off" />
                  <button class="btn btn-secondary btn-small" id="mcpKeyToggle" type="button">显示</button>
                </span>
              </label>
            </div>
            <div class="test-row">
              <button class="btn btn-secondary btn-small" id="testMcpBtn" type="button">测试连接</button>
              <span class="status-light"><i class="light gray" id="mcpLight"></i><span id="mcpStatusText">未配置</span></span>
            </div>
            <p class="hint">接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询。MCP 方法已预留：get_product_sales、get_asins_sales_rank、get_product_info 等。</p>
          </div>

          <div class="tab-panel" id="tab-pa">
            <div class="form-grid">
              <label>Access Key
                <input id="paAccess" type="password" placeholder="AWS Access Key" autocomplete="off" />
              </label>
              <label>Secret Key
                <input id="paSecret" type="password" placeholder="AWS Secret Key" autocomplete="off" />
              </label>
              <label>Partner Tag
                <input id="paTag" type="text" placeholder="例如 yourtag-20" />
              </label>
              <label>Partner Type
                <select id="paType">
                  <option value="Associates">Associates</option>
                  <option value="NativeShopping">NativeShopping</option>
                </select>
              </label>
            </div>
            <div class="test-row">
              <button class="btn btn-secondary btn-small" id="testPaBtn" type="button">测试连接</button>
              <span class="status-light"><i class="light gray" id="paLight"></i><span id="paStatusText">未配置</span></span>
            </div>
            <p class="hint">接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询。已实现 GetItems / SearchItems 结构与 PA-API 5.0 数据转换层，签名请求在 AmazonPaApiProvider._paApiRequest 中预留。</p>
          </div>

          <div class="tab-panel" id="tab-keepa">
            <div class="form-grid">
              <label>Keepa API Key
                <input id="keepaKey" type="password" placeholder="填入 Keepa API Key" autocomplete="off" />
              </label>
              <label>站点 Domain ID
                <select id="keepaDomain">
                  <option value="1">1 = US</option>
                  <option value="2">2 = UK</option>
                  <option value="3">3 = DE</option>
                  <option value="4">4 = FR</option>
                  <option value="5">5 = JP</option>
                  <option value="6">6 = CA</option>
                  <option value="12">12 = AU</option>
                </select>
              </label>
            </div>
            <div class="test-row">
              <button class="btn btn-secondary btn-small" id="testKeepaBtn" type="button">测试连接</button>
              <span class="status-light"><i class="light gray" id="keepaLight"></i><span id="keepaStatusText">未配置</span></span>
              <span class="status-light">剩余额度：<b id="keepaQuota">--</b></span>
            </div>
            <p class="hint">接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询。Keepa 的 CSV 时间序列已在 KeepaApiProvider._parseKeepaCsv 中转换为统一趋势格式。</p>
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-secondary" id="configCancel" type="button">取消</button>
          <button class="btn btn-primary" id="configSave" type="button">保存配置并重新查询</button>
        </div>
      </div>
    </div>

    <div id="toast" role="status" aria-live="polite"></div>
    <div id="tip"></div>

    <script>
      const DATA = __DATA_JSON__;
      const DEFAULT_ASINS = DATA.raw.map((p) => p.asin);

      /*
       * ============================================================
       * 1. 基础工具与统一数据格式
       * ============================================================
       * 所有 Provider 的 5 个方法都返回下方统一字段，页面只认这套格式。
       */
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
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : "id-" + Date.now() + "-" + Math.random().toString(36).slice(2));

      const MARKETPLACES = { US: "US", CA: "CA", UK: "UK", DE: "DE", JP: "JP", AU: "AU" };
      const KEEPA_DOMAINS = { US: 1, UK: 2, DE: 3, FR: 4, JP: 5, CA: 6, AU: 12 };

      function parseLaunch(s) {
        if (!s) return { launchDate: null, daysOnSale: null };
        const m = String(s).match(/^(.+?)\s*\(([\d,]+)天\)/);
        if (!m) return { launchDate: String(s), daysOnSale: null };
        return { launchDate: m[1], daysOnSale: parseInt(m[2].replace(/,/g, ""), 10) };
      }

      function emptyShape(kind, asin, marketplace) {
        const base = { asin, marketplace, found: false };
        if (kind === "basicInfo") return Object.assign(base, { brand: null, title: null, url: null, price: null, originalPrice: null, discount: null, imageUrl: null, imageLabel: null, category: null, subcategory: null, launchDate: null, daysOnSale: null, rating: null, reviewCount: null, isMockEstimate: false });
        if (kind === "salesData") return Object.assign(base, { sales30d: null, monthlySales: null, monthlyTrend: null, bsrCategory: null, bsrSubcategory: null, salesTrend: null, isMockEstimate: false });
        if (kind === "keepaData") return Object.assign(base, { priceTrend: null, bsrTrend: null, buyBoxOwnership: null, updatedAt: null, isMockEstimate: false });
        if (kind === "reviewsData") return Object.assign(base, { summary: null, sellingPoints: null, positiveReviews: null, negativeReviews: null, improvementPoints: null, targetAudience: null, useScenarios: null, optimizationDirection: null, positiveKeywords: [], negativeKeywords: [], isMockEstimate: false });
        return Object.assign(base, { material: null, productSize: null, packageSize: null, packageWeight: null, variants: null, variantCount: null, productParams: null, packageInfo: null, isMockEstimate: false });
      }

      function empty(kind, asin, marketplace) {
        return JSON.parse(JSON.stringify(emptyShape(kind, asin, marketplace)));
      }

      /*
       * ============================================================
       * 2. 配置与缓存（localStorage）
       * ============================================================
       */
      const CFG_KEY = "amz_provider_config_v1";
      const CACHE_KEY = "amz_provider_cache_v1";
      const QUOTA_KEY = "amz_keepa_quota";
      const CACHE_TTL = 24 * 60 * 60 * 1000;

      function defaultConfig() {
        return {
          mainProvider: "mock",
          general: { site: "US", timeout: 10, retries: 2, concurrency: 3, requestIntervalMs: 500, mode: "single" },
          mixed: { basicInfo: "amazon-pa-api", salesData: "sellersprite-mcp", keepaData: "keepa-api", reviewsData: "mock", specs: "mock" },
          sellersprite: { mcpServerUrl: "", apiKey: "" },
          pa: { accessKey: "", secretKey: "", partnerTag: "", partnerType: "Associates" },
          keepa: { keepaApiKey: "", domainId: 1 },
        };
      }

      function loadConfig() {
        try {
          const raw = localStorage.getItem(CFG_KEY);
          if (!raw) return defaultConfig();
          const saved = JSON.parse(raw);
          return Object.assign(defaultConfig(), saved, {
            general: Object.assign(defaultConfig().general, saved.general || {}),
            mixed: Object.assign(defaultConfig().mixed, saved.mixed || {}),
            sellersprite: Object.assign(defaultConfig().sellersprite, saved.sellersprite || {}),
            pa: Object.assign(defaultConfig().pa, saved.pa || {}),
            keepa: Object.assign(defaultConfig().keepa, saved.keepa || {}),
          });
        } catch (err) {
          return defaultConfig();
        }
      }

      function saveConfig(cfg) {
        try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch (err) { console.warn("配置保存失败", err); }
      }

      function loadCache() {
        try {
          const raw = localStorage.getItem(CACHE_KEY);
          return raw ? JSON.parse(raw) : {};
        } catch (err) { return {}; }
      }
      function saveCache(cache) {
        try {
          const serialized = JSON.stringify(cache);
          localStorage.setItem(CACHE_KEY, serialized);
          /* 回读校验：部分环境（隐私模式/受限存储）会静默失败，保证内存与存储一致 */
          const readback = localStorage.getItem(CACHE_KEY);
          if (readback === null) {
            console.warn("localStorage 不可用，缓存仅保留在内存");
          }
        } catch (err) { console.warn("缓存保存失败", err); }
      }
      function loadKeepaQuota() {
        try { return Number(localStorage.getItem(QUOTA_KEY)) || null; } catch (err) { return null; }
      }
      function saveKeepaQuota(n) {
        try { localStorage.setItem(QUOTA_KEY, String(n)); } catch (err) {}
      }

      /*
       * ============================================================
       * 3. Provider 基类与统一接口
       * ============================================================
       * 新增数据源只需继承 ProductDataProvider 并实现 5 个方法。
       */
      class ProviderNotConfiguredError extends Error {
        constructor(msg) { super(msg); this.code = "NOT_CONFIGURED"; }
      }
      class ProviderRequestError extends Error {
        constructor(msg, cause) { super(msg); this.code = "REQUEST_FAILED"; this.cause = cause; }
      }

      class ProductDataProvider {
        constructor(config = {}) { this.config = config || {}; }
        get id() { throw new Error("请实现 provider id"); }
        get label() { return this.id; }
        isConfigured() { return true; }
        async getProductBasicInfo(asin, marketplace) { throw new Error(this.id + " 未实现 getProductBasicInfo"); }
        async getSalesData(asin, marketplace) { throw new Error(this.id + " 未实现 getSalesData"); }
        async getKeepaData(asin, marketplace) { throw new Error(this.id + " 未实现 getKeepaData"); }
        async getReviewsData(asin, marketplace) { throw new Error(this.id + " 未实现 getReviewsData"); }
        async getProductSpecs(asin, marketplace) { throw new Error(this.id + " 未实现 getProductSpecs"); }
        async testConnection() { return { ok: false, status: "unsupported", message: "该数据源不支持连接测试" }; }
      }

      /*
       * ============================================================
       * 4. 适配器 A：模拟数据（MockDataProvider）—— 默认数据源
       * ============================================================
       * 接入步骤：无需配置，默认即生效。
       * 数据来源：Excel 模板真实字段 + 明确标注的演示估算值（isMockEstimate=true）。
       */
      const MOCK_EXTRA = {
        B0B441L1K6: { price: 79.99, originalPrice: 99.99, discount: 20, sales30d: 2850, monthlyTrend: [18, 22, 19, 26, 24, 30, 28, 33], salesTrend: [24, 28, 26, 31, 29, 34], priceTrend: [82, 80, 81, 78, 79, 76, 75, 72], bsrTrend: [820, 760, 690, 640, 600, 570, 540, 520], buyBoxOwnership: 100 },
        B09B9LRBM5: { price: 80.74, originalPrice: 99.99, discount: 19, sales30d: 1980, monthlyTrend: [12, 15, 14, 18, 16, 21, 20, 24], salesTrend: [16, 19, 17, 22, 20, 24], priceTrend: [85, 83, 84, 81, 82, 79, 78, 74], bsrTrend: [4200, 3900, 3600, 3400, 3200, 3000, 2900, 2800], buyBoxOwnership: 98 },
        B0D698PPRS: { price: 62.68, originalPrice: 99.99, discount: 37, sales30d: 1520, monthlyTrend: [9, 12, 11, 15, 14, 17, 16, 19], salesTrend: [12, 15, 13, 17, 15, 19], priceTrend: [66, 64, 65, 63, 64, 61, 60, 58], bsrTrend: [21000, 19500, 18300, 17600, 16900, 16500, 16000, 15600], buyBoxOwnership: 97 },
        B0D3V62NND: { price: 69.99, originalPrice: 89.99, discount: 22, sales30d: 410, monthlyTrend: [2, 3, 3, 4, 4, 5, 5, 6], salesTrend: [3, 4, 4, 5, 5, 6], priceTrend: [74, 72, 73, 70, 71, 68, 67, 65], bsrTrend: [38000, 36000, 34500, 33500, 32500, 32000, 31500, 31000], buyBoxOwnership: 95 },
        B0D78VM6PR: { price: 54.99, originalPrice: 69.99, discount: 21, sales30d: 335, monthlyTrend: [2, 2, 3, 3, 3, 4, 4, 5], salesTrend: [3, 3, 4, 4, 4, 5], priceTrend: [58, 57, 58, 56, 55, 54, 53, 52], bsrTrend: [17000, 16500, 15800, 15200, 14800, 14500, 14000, 13700], buyBoxOwnership: 93 },
        B0FGJ3R8F1: { price: 89.99, originalPrice: 119.99, discount: 25, sales30d: 220, monthlyTrend: [1, 2, 2, 2, 3, 3, 3, 4], salesTrend: [2, 2, 3, 3, 3, 4], priceTrend: [98, 96, 97, 94, 92, 91, 90, 88], bsrTrend: [19000, 18200, 17400, 16800, 16200, 15800, 15200, 15000], buyBoxOwnership: 90 },
      };

      const MOCK_CATALOG = {};
      DATA.raw.forEach((raw) => {
        const ana = DATA.analysis.find((a) => a.asin === raw.asin) || {};
        const ex = MOCK_EXTRA[raw.asin] || {};
        const launch = parseLaunch(raw.launchDate);
        MOCK_CATALOG[raw.asin] = {
          basicInfo: Object.assign(empty("basicInfo", raw.asin, "US"), {
            found: true, brand: raw.brand, title: raw.title, url: raw.url,
            price: ex.price ?? null, originalPrice: ex.originalPrice ?? null, discount: ex.discount ?? null,
            imageUrl: null, imageLabel: raw.brand + " 商品主图",
            category: raw.rankCategory, subcategory: raw.rankSubcategory,
            launchDate: launch.launchDate, daysOnSale: launch.daysOnSale,
            rating: raw.rating, reviewCount: raw.reviewCount,
            isMockEstimate: ex.price !== undefined,
          }),
          salesData: Object.assign(empty("salesData", raw.asin, "US"), {
            found: true, sales30d: ex.sales30d ?? null, monthlySales: ex.monthlyTrend ?? null,
            monthlyTrend: ex.monthlyTrend ?? null, bsrCategory: raw.rankCategory, bsrSubcategory: raw.rankSubcategory,
            salesTrend: ex.salesTrend ?? null, isMockEstimate: ex.sales30d !== undefined,
          }),
          keepaData: Object.assign(empty("keepaData", raw.asin, "US"), {
            found: true, priceTrend: ex.priceTrend ?? null, bsrTrend: ex.bsrTrend ?? null,
            buyBoxOwnership: ex.buyBoxOwnership ?? null, updatedAt: null, isMockEstimate: ex.priceTrend !== undefined,
          }),
          reviewsData: Object.assign(empty("reviewsData", raw.asin, "US"), {
            found: true, summary: null,
            sellingPoints: ana.sellingPoints ?? null,
            positiveReviews: ana.positiveReviews ?? null,
            negativeReviews: ana.negativeReviews ?? null,
            improvementPoints: ana.improvementPoints ?? null,
            targetAudience: ana.targetAudience ?? null,
            useScenarios: ana.useScenarios ?? null,
            optimizationDirection: ana.optimizationDirection ?? null,
            positiveKeywords: [], negativeKeywords: [],
          }),
          specs: Object.assign(empty("specs", raw.asin, "US"), {
            found: true, material: null, productSize: null, packageSize: null, packageWeight: null,
            variants: raw.variants ?? null, variantCount: null,
            productParams: raw.productParams ?? null, packageInfo: raw.packageInfo ?? null,
          }),
        };
      });

      class MockDataProvider extends ProductDataProvider {
        get id() { return "mock"; }
        get label() { return "模拟数据"; }
        isConfigured() { return true; }
        _entry(kind, asin, marketplace) {
          const entry = MOCK_CATALOG[asin];
          if (!entry || !entry[kind]) return empty(kind, asin, marketplace);
          return JSON.parse(JSON.stringify(entry[kind]));
        }
        async getProductBasicInfo(asin, marketplace) { return this._entry("basicInfo", asin, marketplace); }
        async getSalesData(asin, marketplace) { return this._entry("salesData", asin, marketplace); }
        async getKeepaData(asin, marketplace) { return this._entry("keepaData", asin, marketplace); }
        async getReviewsData(asin, marketplace) { return this._entry("reviewsData", asin, marketplace); }
        async getProductSpecs(asin, marketplace) { return this._entry("specs", asin, marketplace); }
        async testConnection() { return { ok: true, status: "connected", message: "模拟数据源始终可用" }; }
      }

      /*
       * ============================================================
       * 5. 适配器 B：卖家精灵 MCP（SellerspriteMCPProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
       * 配置项：mcpServerUrl、apiKey
       * 已预留 MCP 方法：
       *   get_product_info(asin, marketplace)         → 基础信息
       *   get_product_sales(asin, marketplace, period) → 销量（salesLast30Days / monthSales）
       *   get_asins_sales_rank(asin, marketplace)      → BSR 大类/小类排名
       *   get_product_reviews(asin, marketplace)       → 评论关键词与摘要
       */
      class SellerspriteMCPProvider extends ProductDataProvider {
        get id() { return "sellersprite-mcp"; }
        get label() { return "卖家精灵MCP"; }
        isConfigured() { return !!(this.config.apiKey && this.config.mcpServerUrl); }

        async _callMcp(method, params) {
          if (!this.isConfigured()) throw new ProviderNotConfiguredError("卖家精灵MCP未配置");
          /*
           * 此处填入真实请求逻辑。
           * 卖家精灵 MCP 按 JSON-RPC 2.0 协议调用，例如：
           *   POST {mcpServerUrl}/mcp
           *   Headers: { "Content-Type": "application/json", "Authorization": "Bearer " + apiKey }
           *   Body: { "jsonrpc":"2.0", "id":1, "method":"tools/call",
           *           "params":{ "name": method, "arguments": params } }
           * 若你的网关是 OpenAPI 风格，改成对应的 HTTP 接口即可。
           */
          throw new ProviderRequestError("卖家精灵 MCP 尚未接入：请在 SellerspriteMCPProvider._callMcp 中填入真实请求逻辑");
        }

        /*
         * 卖家精灵字段 → 统一格式：
         * raw.price / raw.listPrice                 → price / originalPrice
         * raw.salesLast30Days                       → sales30d（30天销量）
         * raw.monthSales                            → monthlySales（历史月销）
         * raw.salesRank.categoryRank                → bsrCategory
         * raw.salesRank.subCategoryRank             → bsrSubcategory
         * raw.reviewStat.positiveKeywords           → positiveKeywords
         * raw.reviewStat.negativeKeywords           → negativeKeywords
         */
        _toBasic(asin, marketplace, raw) {
          const out = empty("basicInfo", asin, marketplace);
          out.found = !!(raw && (raw.title || raw.asin));
          out.brand = raw?.brand ?? null;
          out.title = raw?.title ?? null;
          out.url = raw?.url ?? "https://www.amazon.com/dp/" + asin;
          out.price = raw?.price ?? null;
          out.originalPrice = raw?.listPrice ?? null;
          out.discount = raw?.discount ?? null;
          out.imageUrl = raw?.mainImage ?? null;
          out.imageLabel = raw?.imageLabel ?? null;
          out.category = raw?.category ?? null;
          out.subcategory = raw?.subCategory ?? null;
          out.launchDate = raw?.launchDate ?? null;
          out.daysOnSale = raw?.daysOnSale ?? null;
          out.rating = raw?.starRating ?? null;
          out.reviewCount = raw?.reviewCount ?? null;
          return out;
        }
        _toSales(asin, marketplace, raw) {
          const out = empty("salesData", asin, marketplace);
          out.found = !!(raw && (raw.salesLast30Days !== undefined || raw.monthSales !== undefined || raw.salesRank));
          out.sales30d = raw?.salesLast30Days ?? null;
          out.monthlySales = raw?.monthSales ?? null;
          out.monthlyTrend = raw?.monthlyTrend ?? null;
          out.bsrCategory = raw?.salesRank?.categoryRank ?? null;
          out.bsrSubcategory = raw?.salesRank?.subCategoryRank ?? null;
          out.salesTrend = raw?.salesTrend ?? null;
          return out;
        }
        _toReviews(asin, marketplace, raw) {
          const out = empty("reviewsData", asin, marketplace);
          out.found = !!(raw && (raw.summary || raw.positiveKeywords || raw.sellingPoints));
          out.summary = raw?.summary ?? null;
          out.sellingPoints = raw?.sellingPoints ?? null;
          out.positiveReviews = raw?.positiveReviews ?? raw?.positiveKeywordsText ?? null;
          out.negativeReviews = raw?.negativeReviews ?? raw?.negativeKeywordsText ?? null;
          out.improvementPoints = raw?.improvementPoints ?? null;
          out.targetAudience = raw?.targetAudience ?? null;
          out.useScenarios = raw?.useScenarios ?? null;
          out.optimizationDirection = raw?.optimizationDirection ?? null;
          out.positiveKeywords = Array.isArray(raw?.positiveKeywords) ? raw.positiveKeywords : [];
          out.negativeKeywords = Array.isArray(raw?.negativeKeywords) ? raw.negativeKeywords : [];
          return out;
        }
        _toSpecs(asin, marketplace, raw) {
          const out = empty("specs", asin, marketplace);
          out.found = !!(raw && (raw.specs || raw.variantCount));
          out.material = raw?.specs?.material ?? null;
          out.productSize = raw?.specs?.productSize ?? null;
          out.packageSize = raw?.specs?.packageSize ?? null;
          out.packageWeight = raw?.specs?.packageWeight ?? null;
          out.variants = raw?.variants ?? null;
          out.variantCount = raw?.variantCount ?? null;
          out.productParams = raw?.productParams ?? null;
          out.packageInfo = raw?.packageInfo ?? null;
          return out;
        }

        async getProductBasicInfo(asin, marketplace) {
          const raw = await this._callMcp("get_product_info", { asin, marketplace });
          return this._toBasic(asin, marketplace, raw);
        }
        async getSalesData(asin, marketplace) {
          const salesRaw = await this._callMcp("get_product_sales", { asin, marketplace, period: "30d" });
          let rankRaw = {};
          try { rankRaw = await this._callMcp("get_asins_sales_rank", { asin, marketplace }); } catch (err) {}
          return this._toSales(asin, marketplace, Object.assign({}, salesRaw, rankRaw));
        }
        async getKeepaData(asin, marketplace) {
          const raw = await this._callMcp("get_keepa_trend", { asin, marketplace });
          const out = empty("keepaData", asin, marketplace);
          out.found = !!(raw && (raw.priceTrend || raw.bsrTrend));
          out.priceTrend = raw?.priceTrend ?? null;
          out.bsrTrend = raw?.bsrTrend ?? null;
          out.buyBoxOwnership = raw?.buyBoxOwnership ?? null;
          out.updatedAt = raw?.updatedAt ?? null;
          return out;
        }
        async getReviewsData(asin, marketplace) {
          const raw = await this._callMcp("get_product_reviews", { asin, marketplace, starFilter: "1-3,4-5" });
          return this._toReviews(asin, marketplace, raw);
        }
        async getProductSpecs(asin, marketplace) {
          const raw = await this._callMcp("get_product_specs", { asin, marketplace });
          return this._toSpecs(asin, marketplace, raw);
        }
        async testConnection() {
          if (!this.isConfigured()) return { ok: false, status: "unconfigured", message: "未配置 MCP 服务器地址或 API Key" };
          try {
            const res = await this._callMcp("test_connection", {});
            return { ok: true, status: "connected", message: "连接成功", data: res };
          } catch (err) {
            return { ok: false, status: "failed", message: "连接失败：" + err.message };
          }
        }
      }

      /*
       * ============================================================
       * 6. 适配器 C：亚马逊 PA-API 5.0（AmazonPaApiProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
       * 配置项：accessKey、secretKey、partnerTag、partnerType
       * 已实现 GetItems / SearchItems 结构与 Item → 统一格式转换。
       */
      const PA_ENDPOINTS = {
        US: { host: "webservices.amazon.com", region: "us-east-1" },
        CA: { host: "webservices.amazon.ca", region: "us-east-1" },
        UK: { host: "webservices.amazon.co.uk", region: "eu-west-1" },
        DE: { host: "webservices.amazon.de", region: "eu-west-1" },
        JP: { host: "webservices.amazon.co.jp", region: "us-west-2" },
        AU: { host: "webservices.amazon.com.au", region: "us-west-2" },
      };

      class AmazonPaApiProvider extends ProductDataProvider {
        get id() { return "amazon-pa-api"; }
        get label() { return "亚马逊PA-API"; }
        isConfigured() { return !!(this.config.accessKey && this.config.secretKey && this.config.partnerTag); }

        async _paApiRequest(endpoint, payload, marketplace) {
          if (!this.isConfigured()) throw new ProviderNotConfiguredError("PA-API未配置");
          const ep = PA_ENDPOINTS[marketplace] || PA_ENDPOINTS.US;
          /*
           * 此处填入真实请求逻辑。
           * PA-API 5.0 使用 AWS Signature Version 4 签名：
           *   1. CanonicalRequest = HTTPMethod + "\n" + CanonicalURI + "\n" + CanonicalQueryString
           *      + "\n" + CanonicalHeaders + "\n" + SignedHeaders + "\n" + SHA256(payload)
           *   2. StringToSign = "AWS4-HMAC-SHA256" + "\n" + timestamp + "\n" + scope + "\n" + SHA256(CanonicalRequest)
           *   3. signingKey = HMAC-SHA256 逐级派生（date/region/service/aws4_request）
           *   4. Authorization 头 = AWS4-HMAC-SHA256 Credential=..., SignedHeaders=..., Signature=...
           * 请求头需包含 Host、X-Amz-Date、Content-Type: application/json；Payload 需 UTF-8 JSON。
           * 浏览器端不建议暴露 Secret Key，生产环境应把本方法改为调用后端签名代理。
           */
          const res = await fetch("https://" + ep.host + "/paapi5/" + endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(Object.assign({
              PartnerTag: this.config.partnerTag,
              PartnerType: this.config.partnerType || "Associates",
              Marketplace: ep.host,
            }, payload)),
          });
          if (!res.ok) throw new ProviderRequestError("PA-API HTTP " + res.status);
          return res.json();
        }

        /*
         * PA-API Item 结构 → 统一格式：
         * Item.ItemInfo.Title.DisplayValue                 → title
         * Item.ItemInfo.ByLineInfo.Brand.DisplayValue      → brand
         * Item.Offers.Listings[0].Price.DisplayAmount      → price
         * Item.Offers.Listings[0].Price.Savings.Percentage → discount
         * Item.Images.Primary.Large.URL                    → imageUrl
         * Item.CustomerReviews.Count / StarRating          → reviewCount / rating
         * Item.BrowseNodeInfo.BrowseNodes[].SalesRank      → category rank
         */
        _toBasic(asin, marketplace, item) {
          const out = empty("basicInfo", asin, marketplace);
          out.found = !!(item && (item.ItemInfo || item.Images));
          out.brand = item?.ItemInfo?.ByLineInfo?.Brand?.DisplayValue ?? null;
          out.title = item?.ItemInfo?.Title?.DisplayValue ?? null;
          out.url = item?.DetailPageURL ?? "https://www.amazon.com/dp/" + asin;
          const offer = item?.Offers?.Listings && item.Offers.Listings[0];
          out.price = offer?.Price?.Amount ?? offer?.Price?.DisplayAmount ?? null;
          out.originalPrice = offer?.Price?.Savings?.Price?.Amount ?? null;
          out.discount = offer?.Price?.Savings?.Percentage ?? null;
          out.imageUrl = item?.Images?.Primary?.Large?.URL ?? null;
          out.category = item?.BrowseNodeInfo?.BrowseNodes?.[0]?.DisplayName ?? null;
          out.subcategory = item?.BrowseNodeInfo?.BrowseNodes?.[0]?.SalesRank ? ("SalesRank " + item.BrowseNodeInfo.BrowseNodes[0].SalesRank) : null;
          out.rating = item?.CustomerReviews?.StarRating ?? null;
          out.reviewCount = item?.CustomerReviews?.Count ?? null;
          out.launchDate = item?.ItemInfo?.ExternalIds?.LaunchDate?.DisplayValue ?? null;
          return out;
        }

        async getProductBasicInfo(asin, marketplace) {
          const payload = {
            ItemIds: [asin],
            Resources: [
              "Images.Primary.Large",
              "ItemInfo.Title",
              "ItemInfo.ByLineInfo",
              "ItemInfo.Classifications",
              "ItemInfo.ExternalIds",
              "Offers.Listings.Price",
              "CustomerReviews.Count",
              "CustomerReviews.StarRating",
              "BrowseNodeInfo.BrowseNodes",
            ],
          };
          const raw = await this._paApiRequest("getitems", payload, marketplace);
          const item = raw?.ItemsResult?.Items?.[0];
          if (!item) throw new ProviderRequestError("PA-API 未返回商品：" + asin);
          return this._toBasic(asin, marketplace, item);
        }
        async getSalesData(asin, marketplace) {
          /* PA-API 不提供销量；保留统一结构，返回空数据避免破坏表格。 */
          const out = empty("salesData", asin, marketplace);
          out.found = false;
          return out;
        }
        async getKeepaData(asin, marketplace) {
          const out = empty("keepaData", asin, marketplace);
          out.found = false;
          return out;
        }
        async getReviewsData(asin, marketplace) {
          /* PA-API 不提供评论语义分析；返回空结构。 */
          const out = empty("reviewsData", asin, marketplace);
          out.found = false;
          return out;
        }
        async getProductSpecs(asin, marketplace) {
          const payload = {
            ItemIds: [asin],
            Resources: ["ItemInfo.Features", "ItemInfo.ProductInfo", "ItemInfo.ManufactureInfo", "Offers.Listings.Price"],
          };
          try {
            const raw = await this._paApiRequest("getitems", payload, marketplace);
            const item = raw?.ItemsResult?.Items?.[0];
            const out = empty("specs", asin, marketplace);
            out.found = !!(item && (item.ItemInfo?.ProductInfo || item.ItemInfo?.Features));
            out.material = item?.ItemInfo?.ProductInfo?.IsAdultProduct ? "（见 ProductInfo）" : null;
            out.productSize = item?.ItemInfo?.ProductInfo?.ItemDimensions?.Height?.DisplayValue ? (item.ItemInfo.ProductInfo.ItemDimensions.Height.DisplayValue + "H") : null;
            out.packageSize = item?.ItemInfo?.ProductInfo?.PackageDimensions?.Height?.DisplayValue ? (item.ItemInfo.ProductInfo.PackageDimensions.Height.DisplayValue + "H") : null;
            out.packageWeight = item?.ItemInfo?.ProductInfo?.PackageDimensions?.Weight?.DisplayValue ?? null;
            out.productParams = item?.ItemInfo?.Features?.DisplayValues?.join("\n") ?? null;
            return out;
          } catch (err) {
            if (err instanceof ProviderNotConfiguredError) throw err;
            return empty("specs", asin, marketplace);
          }
        }
        async testConnection() {
          if (!this.isConfigured()) return { ok: false, status: "unconfigured", message: "未配置 Access Key / Secret Key / Partner Tag" };
          try {
            await this._paApiRequest("getitems", {
              ItemIds: ["B0B441L1K6"],
              Resources: ["ItemInfo.Title"],
            }, "US");
            return { ok: true, status: "connected", message: "PA-API 连接成功" };
          } catch (err) {
            return { ok: false, status: "failed", message: "连接失败：" + err.message };
          }
        }
      }

      /*
       * ============================================================
       * 7. 适配器 D：Keepa API（KeepaApiProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
       * 配置项：keepaApiKey、domainId
       * Domain ID 对应站点：1=US, 2=UK, 3=DE, 4=FR, 5=JP, 6=CA, 12=AU
       */
      class KeepaApiProvider extends ProductDataProvider {
        get id() { return "keepa-api"; }
        get label() { return "Keepa API"; }
        isConfigured() { return !!this.config.keepaApiKey; }

        async _callProduct(asin, marketplace, light = false) {
          if (!this.isConfigured()) throw new ProviderNotConfiguredError("Keepa API未配置");
          const domain = this.config.domainId || KEEPA_DOMAINS[marketplace] || 1;
          /*
           * 此处填入真实请求逻辑。
           * Keepa Product API：
           *   GET https://api.keepa.com/product
           *   ?key={keepaApiKey}&asin={asin}&domain={domain}&range=365&buybox=1&stats=90
           * 响应 JSON：{ products: [{ asin, title, csv, buybox, ... }] }
           * csv 数组为 Keepa 压缩时间序列：[起始时间戳, 数值1, 数值2, ...]，0 表示无数据。
           */
          const url = "https://api.keepa.com/product?key=" + encodeURIComponent(this.config.keepaApiKey) +
            "&asin=" + encodeURIComponent(asin) + "&domain=" + domain +
            "&range=" + (light ? 30 : 365) + "&buybox=" + (light ? 0 : 1) + "&stats=" + (light ? 0 : 90);
          const res = await fetch(url);
          if (!res.ok) throw new ProviderRequestError("Keepa HTTP " + res.status);
          const quota = Number(res.headers.get("X-Keepa-Token")) || null;
          if (quota) { saveKeepaQuota(quota); window.dispatchEvent(new CustomEvent("keepa-quota-update", { detail: quota })); }
          const json = await res.json();
          if (!json.products || !json.products.length) throw new ProviderRequestError("Keepa 未返回商品：" + asin);
          return json.products[0];
        }

        /*
         * Keepa CSV 时间序列 → 统一趋势格式 [{ t, value }]
         * csv[0] 为第一个数据点时间戳（毫秒），csv[1..] 按天递增。
         */
        _parseKeepaCsv(csv) {
          if (!Array.isArray(csv) || csv.length < 2) return [];
          const t0 = Number(csv[0]);
          const out = [];
          for (let i = 1; i < csv.length; i++) {
            const v = Number(csv[i]);
            if (v > 0 && Number.isFinite(v)) out.push({ t: t0 + (i - 1) * 86400000, value: v });
          }
          return out;
        }

        async getKeepaData(asin, marketplace) {
          const raw = await this._callProduct(asin, marketplace);
          const out = empty("keepaData", asin, marketplace);
          out.found = true;
          out.priceTrend = this._parseKeepaCsv(raw.csv?.[0]);
          out.bsrTrend = this._parseKeepaCsv(raw.csv?.[1]);
          out.buyBoxOwnership = raw?.buybox ? 100 : null;
          out.updatedAt = raw?.lastUpdate ? new Date(raw.lastUpdate).toISOString() : null;
          return out;
        }
        async getProductBasicInfo(asin, marketplace) {
          const out = empty("basicInfo", asin, marketplace);
          try {
            const raw = await this._callProduct(asin, marketplace, true);
            out.found = true;
            out.title = raw?.title ?? null;
            out.url = "https://www.amazon.com/dp/" + asin;
            out.brand = raw?.brand ?? null;
            out.rating = raw?.rating ?? null;
            out.reviewCount = raw?.reviewCount ?? null;
            out.launchDate = raw?.launchDate ? new Date(raw.launchDate).toISOString().slice(0, 10) : null;
            return out;
          } catch (err) {
            if (err instanceof ProviderNotConfiguredError) throw err;
            return out;
          }
        }
        async getSalesData(asin, marketplace) {
          const out = empty("salesData", asin, marketplace);
          try {
            const raw = await this._callProduct(asin, marketplace, true);
            out.found = true;
            const monthly = this._parseKeepaCsv(raw.csv?.[2]);
            out.monthlySales = monthly.length ? monthly.map((p) => p.value) : null;
            out.salesTrend = monthly.slice(-12).map((p) => p.value);
            return out;
          } catch (err) {
            if (err instanceof ProviderNotConfiguredError) throw err;
            return out;
          }
        }
        async getReviewsData(asin, marketplace) {
          const out = empty("reviewsData", asin, marketplace);
          out.found = false;
          return out;
        }
        async getProductSpecs(asin, marketplace) {
          const out = empty("specs", asin, marketplace);
          out.found = false;
          return out;
        }
        async testConnection() {
          if (!this.isConfigured()) return { ok: false, status: "unconfigured", message: "未配置 Keepa API Key" };
          try {
            const raw = await this._callProduct("B0B441L1K6", "US", true);
            return { ok: true, status: "connected", message: "Keepa 连接成功：" + (raw.title || raw.asin) };
          } catch (err) {
            return { ok: false, status: "failed", message: "连接失败：" + err.message };
          }
        }
      }

      /*
       * ============================================================
       * 8. Provider 注册表 + DataProviderManager
       * ============================================================
       * 后续新增数据源只需向 registry 注册一个 Provider 工厂：
       *   window.ProductDataProviderRegistry.register({ id, name, configKey, create });
       * 页面代码（表格、渲染、队列）无需任何改动。
       */
      const PROVIDER_REGISTRY = {
        "mock": { id: "mock", name: "模拟数据", configKey: null, create: (cfg) => new MockDataProvider(cfg) },
        "sellersprite-mcp": { id: "sellersprite-mcp", name: "卖家精灵MCP", configKey: "sellersprite", create: (cfg) => new SellerspriteMCPProvider(cfg) },
        "amazon-pa-api": { id: "amazon-pa-api", name: "PA-API", configKey: "pa", create: (cfg) => new AmazonPaApiProvider(cfg) },
        "keepa-api": { id: "keepa-api", name: "Keepa API", configKey: "keepa", create: (cfg) => new KeepaApiProvider(cfg) },
      };
      window.ProductDataProviderRegistry = {
        providers: Object.assign({}, PROVIDER_REGISTRY),
        register(meta) {
          if (!meta || !meta.id || typeof meta.create !== "function") throw new Error("Provider 注册信息不完整");
          this.providers[meta.id] = meta;
        },
        list() { return Object.values(this.providers); },
      };

      class DataProviderManager {
        constructor() {
          this.config = loadConfig();
          this.cache = loadCache();
          this.mockProvider = new MockDataProvider({});
          this.activeMain = this.config.mainProvider || "mock";
          this.lastRequestAt = 0;
          this.abort = null;
        }

        listProviders() { return window.ProductDataProviderRegistry.list(); }

        _create(id) {
          const meta = window.ProductDataProviderRegistry.providers[id] || window.ProductDataProviderRegistry.providers.mock;
          const section = meta.configKey ? (this.config[meta.configKey] || {}) : {};
          return meta.create(section);
        }

        resolve(id) {
          const meta = window.ProductDataProviderRegistry.providers[id];
          if (!meta) return { provider: this.mockProvider, degraded: true, reason: "未知数据源，已使用模拟数据" };
          const provider = this._create(id);
          if (!provider.isConfigured()) {
            return { provider: this.mockProvider, degraded: true, reason: provider.label + "未配置，已使用模拟数据" };
          }
          return { provider, degraded: false };
        }

        providerFor(kind) {
          const general = this.config.general || {};
          if (general.mode === "mixed" && this.config.mixed && this.config.mixed[kind]) {
            let r = this.resolve(this.config.mixed[kind]);
            if (!r.degraded) return r;
            r = this.resolve(this.activeMain);
            if (!r.degraded) return r;
            return this.resolve("mock");
          }
          return this.resolve(this.activeMain);
        }

        fingerprint() {
          const general = this.config.general || {};
          if (general.mode === "mixed") return this.activeMain + "+mixed+" + JSON.stringify(this.config.mixed || {});
          return this.activeMain;
        }

        async _throttle(providerId) {
          const interval = Number(this.config.general?.requestIntervalMs) || 500;
          if (providerId === "mock") { await sleep(110); return; }
          const now = Date.now();
          const wait = Math.max(0, this.lastRequestAt + interval - now);
          if (wait > 0) await sleep(wait);
          this.lastRequestAt = Date.now();
        }

        async _callMethod(provider, method, asin, marketplace) {
          const retries = Math.max(0, Number(this.config.general?.retries) || 0);
          let lastErr;
          for (let i = 0; i <= retries; i++) {
            try {
              await this._throttle(provider.id);
              return await provider[method](asin, marketplace);
            } catch (err) {
              lastErr = err;
              if (err instanceof ProviderNotConfiguredError) throw err;
              if (i < retries) await sleep(260 * (i + 1));
            }
          }
          throw lastErr;
        }

        _getCache(key) {
          const entry = this.cache[key];
          if (!entry) return null;
          if (Date.now() - entry.ts > CACHE_TTL) {
            delete this.cache[key];
            saveCache(this.cache);
            return null;
          }
          return entry.data;
        }

        _setCache(key, data) {
          this.cache[key] = { ts: Date.now(), data };
          const keys = Object.keys(this.cache);
          if (keys.length > 300) {
            keys.sort((a, b) => (this.cache[a].ts || 0) - (this.cache[b].ts || 0));
            keys.slice(0, keys.length - 300).forEach((k) => delete this.cache[k]);
          }
          saveCache(this.cache);
        }

        async fetchOne(asin, marketplace) {
          const key = asin.toUpperCase() + "|" + (marketplace || "US") + "|" + this.fingerprint();
          const cached = this._getCache(key);
          if (cached) return Object.assign({}, cached, { asin, cached: true });

          const result = {
            asin, marketplace: marketplace || "US", matched: false,
            source: null, degraded: null, cached: false, fetchedAt: Date.now(),
            data: {},
          };
          const plan = [
            ["basicInfo", "getProductBasicInfo"],
            ["specs", "getProductSpecs"],
            ["salesData", "getSalesData"],
            ["keepaData", "getKeepaData"],
            ["reviewsData", "getReviewsData"],
          ];
          for (const [kind, method] of plan) {
            const r = this.providerFor(kind);
            try {
              const data = await this._callMethod(r.provider, method, asin, marketplace || "US");
              result.data[kind] = data;
              result.source = result.source || r.provider.label;
              if (r.degraded && !result.degraded) {
                result.degraded = { message: r.reason, provider: r.provider.label };
              }
            } catch (err) {
              try {
                const mockData = await this.mockProvider[method](asin, marketplace || "US");
                result.data[kind] = mockData;
                result.source = result.source || "模拟数据";
                if (!result.degraded) {
                  result.degraded = { message: "接口请求失败，已使用模拟数据", provider: r.provider.label };
                }
              } catch (mockErr) {
                result.data[kind] = null;
                if (!result.degraded) {
                  result.degraded = { message: "接口请求失败，已使用模拟数据", provider: r.provider.label };
                }
              }
            }
          }
          const basic = result.data.basicInfo;
          result.matched = !!(basic && (basic.found || basic.brand || basic.title));
          if (result.matched) this._setCache(key, result);
          return result;
        }

        async queryBatch(asins, callbacks) {
          this.abort = new AbortController();
          const cfg = this.config.general || {};
          const concurrency = Math.max(1, Math.min(6, Number(cfg.concurrency) || 3));
          const total = asins.length;
          const start = performance.now();
          const results = {};
          const queue = asins.slice();
          let done = 0, success = 0, failed = 0;
          callbacks.onStart && callbacks.onStart({ total });

          const worker = async () => {
            while (queue.length && !this.abort.signal.aborted) {
              const asin = queue.shift();
              try {
                const res = await this.fetchOne(asin, cfg.site || "US");
                if (this.abort.signal.aborted) return;
                results[asin] = Object.assign({}, res, { ok: true });
                success++;
                callbacks.onColumn && callbacks.onColumn(results[asin]);
              } catch (err) {
                if (this.abort.signal.aborted) return;
                results[asin] = { asin, matched: false, ok: false, error: true, degraded: null, data: {}, source: null };
                failed++;
                callbacks.onColumn && callbacks.onColumn(results[asin]);
              }
              done++;
              callbacks.onProgress && callbacks.onProgress({ done, total, success, failed, elapsed: (performance.now() - start) / 1000 });
            }
          };

          const workers = [];
          for (let i = 0; i < Math.min(concurrency, total); i++) workers.push(worker());
          await Promise.all(workers);
          const elapsed = (performance.now() - start) / 1000;
          if (this.abort.signal.aborted) {
            callbacks.onCancel && callbacks.onCancel({ done, total, success, failed, elapsed });
          } else {
            callbacks.onDone && callbacks.onDone({ done, total, success, failed, elapsed });
          }
          return results;
        }

        cancel() { if (this.abort) this.abort.abort(); }
      }

      /*
       * ============================================================
       * 9. 页面渲染
       * ============================================================
       */
      const manager = new DataProviderManager();
      const state = { asins: [], products: {}, running: false, lastResult: null };

      const MODULES = [
        { key: "basic", label: "基础商品信息", tone: "blue", span: "图片 / ASIN / 标题 / 售价 / 上线时间 / 排名 / 评分 / 评论数 / 截图", rows: ["image", "asin", "title", "price", "launch", "rank", "rating", "reviews", "entityShot", "params", "package"] },
        { key: "sales", label: "销量数据模块", tone: "gray", span: "30天销量 / 历史月销 / Keepa趋势", rows: ["sales30d", "monthly", "keepa"] },
        { key: "ai", label: "AI评论分析模块", tone: "red", span: "AI标引 / 产品卖点 / 好评点 / 差评点 / 待改善点", rows: ["aiShot", "selling", "positive", "negative", "improve"] },
        { key: "audience", label: "使用人群&场景模块", tone: "orange", span: "使用人群 / 使用场景", rows: ["audience", "scenarios"] },
        { key: "optimize", label: "优化方向模块", tone: "green", span: "A/B/C 级改进建议（支持未来 MCP 分级数据）", rows: ["optimize"] },
      ];
      const ROW_LABELS = {
        image: "图片", asin: "ASIN", title: "标题", price: "售价", launch: "上线时间", rank: "排名",
        rating: "评分", reviews: "评论数", entityShot: "实体截图占位", params: "产品参数信息", package: "包装尺寸及重量",
        sales30d: "30天销量（畅销变体）", monthly: "历史月销", keepa: "Keepa趋势", aiShot: "AI评论分析标引",
        selling: "产品卖点", positive: "好评点", negative: "差评点", improve: "待改善点",
        audience: "使用人群", scenarios: "使用场景", optimize: "优化方向",
      };
      const BAR_HEIGHTS = ["32%", "58%", "45%", "74%", "52%", "86%", "62%", "95%", "70%"];

      function buildCompetitor(p) {
        const d = p.data || {};
        const b = d.basicInfo || {};
        const s = d.salesData || {};
        const k = d.keepaData || {};
        const r = d.reviewsData || {};
        const sp = d.specs || {};
        return {
          asin: p.asin, matched: p.matched, source: p.source, degraded: p.degraded, cached: p.cached,
          brand: b.brand, url: b.url, title: b.title, price: b.price, originalPrice: b.originalPrice,
          discount: b.discount, imageUrl: b.imageUrl, imageLabel: b.imageLabel,
          launchDate: b.launchDate, daysOnSale: b.daysOnSale,
          rankCategory: b.category || s.bsrCategory, rankSubcategory: b.subcategory || s.bsrSubcategory,
          rating: b.rating, reviewCount: b.reviewCount,
          productParams: sp.productParams, packageInfo: sp.packageInfo, material: sp.material,
          productSize: sp.productSize, packageSize: sp.packageSize, packageWeight: sp.packageWeight,
          variants: sp.variants, variantCount: sp.variantCount,
          sales30d: s.sales30d, monthlySales: s.monthlySales || s.monthlyTrend,
          salesTrend: s.salesTrend, priceTrend: k.priceTrend, bsrTrend: k.bsrTrend,
          buyBoxOwnership: k.buyBoxOwnership,
          sellingPoints: r.sellingPoints, positiveReviews: r.positiveReviews, negativeReviews: r.negativeReviews,
          improvementPoints: r.improvementPoints, targetAudience: r.targetAudience, useScenarios: r.useScenarios,
          optimizationDirection: r.optimizationDirection,
          positiveKeywords: r.positiveKeywords, negativeKeywords: r.negativeKeywords,
          priceMock: b.isMockEstimate, salesMock: s.isMockEstimate, keepaMock: k.isMockEstimate,
        };
      }

      function skeletonHtml(rowId) {
        if (rowId === "image") return '<div class="skeleton"><span class="sk img"></span><span class="sk w60"></span></div>';
        if (rowId === "title") return '<div class="skeleton"><span class="sk w80"></span><span class="sk w60"></span><span class="sk w80"></span></div>';
        if (rowId === "selling" || rowId === "positive" || rowId === "negative" || rowId === "improve" || rowId === "optimize") {
          return '<div class="skeleton"><span class="sk w40"></span><span class="sk w80"></span><span class="sk w60"></span><span class="sk w80"></span><span class="sk w40"></span></div>';
        }
        return '<div class="skeleton"><span class="sk w80"></span><span class="sk w60"></span><span class="sk w40"></span></div>';
      }

      function emptyHtml() { return '<span class="empty">--</span>'; }
      function rich(text) {
        const t = esc(text);
        return '<div class="rich-text" data-tip="' + t + '">' + t + "</div>";
      }
      function starLine(rating) {
        const r = Number(rating) || 0;
        const pct = Math.max(0, Math.min(100, (r / 5) * 100));
        return '<div class="star-line"><span class="rating-num">' + esc(rating) + "</span>" +
          '<span class="star-track">★★★★★<span class="star-fill" style="width:' + pct + '%">★★★★★</span></span></div>';
      }
      function mockChip() { return ' <span class="mock-chip">模拟估算</span>'; }
      function miniBars(values) {
        const heights = Array.isArray(values) && values.length
          ? values.map((v) => Math.max(8, Math.min(100, (Number(v) / Math.max(...values)) * 100)) + "%")
          : BAR_HEIGHTS.slice(0, 6);
        return '<div class="mini-bars" aria-hidden="true">' + heights.slice(0, 9).map((h) => "<span style=\"height:" + h + "\"></span>").join("") + "</div>";
      }
      function barChart(values) {
        const heights = Array.isArray(values) && values.length
          ? values.map((v) => Math.max(8, Math.min(100, (Number(v) / Math.max(...values)) * 100)) + "%")
          : BAR_HEIGHTS;
        return '<div class="chart-box" aria-label="历史月销趋势"><div class="chart-title">历史月销趋势 · ' + (Array.isArray(values) ? "实时数据" : "模拟占位") + '</div>' +
          '<div class="bar-chart">' + heights.map((h) => "<span style=\"height:" + h + "\"></span>").join("") + "</div></div>";
      }
      function keepaChart(p) {
        let svg = '<svg class="keepa-svg" viewBox="0 0 280 110" role="img">' +
          '<polyline fill="none" stroke="#3b82f6" stroke-width="2" points="8,78 40,70 72,82 104,58 136,64 168,44 200,52 232,30 272,38" />' +
          '<polyline fill="none" stroke="#f59e0b" stroke-width="2" points="8,28 40,36 72,30 104,48 136,42 168,62 200,56 232,74 272,68" stroke-dasharray="4 3" /></svg>';
        if (Array.isArray(p.priceTrend) && p.priceTrend.length) {
          const pts = p.priceTrend.slice(-12).map((d, i) => {
            const x = 8 + (i / 11) * 264;
            const y = 96 - (d.value / Math.max(...p.priceTrend.map((q) => q.value))) * 80;
            return x.toFixed(1) + "," + y.toFixed(1);
          });
          const bsr = p.bsrTrend && p.bsrTrend.length ? p.bsrTrend.slice(-12) : null;
          const bsrPts = bsr ? bsr.map((d, i) => {
            const x = 8 + (i / 11) * 264;
            const y = 96 - (d.value / Math.max(...bsr.map((q) => q.value))) * 80;
            return x.toFixed(1) + "," + y.toFixed(1);
          }) : null;
          svg = '<svg class="keepa-svg" viewBox="0 0 280 110" role="img">' +
            '<polyline fill="none" stroke="#3b82f6" stroke-width="2" points="' + pts.join(" ") + '" />' +
            (bsrPts ? '<polyline fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4 3" points="' + bsrPts.join(" ") + '" />' : "") +
            "</svg>";
        }
        const buyBox = p.buyBoxOwnership !== null && p.buyBoxOwnership !== undefined
          ? '<div class="label-note">买盒占有率：' + esc(p.buyBoxOwnership) + "%" + (p.keepaMock ? mockChip() : "") + "</div>" : "";
        return '<div class="chart-box" aria-label="Keepa 趋势">' +
          '<div class="chart-title">Keepa 价格 / BSR 趋势 · ' + (Array.isArray(p.priceTrend) && p.priceTrend.length ? "实时数据" : "模拟占位") + "</div>" +
          svg + '<div class="legend"><span><i style="background:#3b82f6"></i>价格</span><span><i style="background:#f59e0b"></i>BSR</span></div>' + buyBox + "</div>";
      }
      function shotBox(text, svg) {
        return '<div class="shot-box">' + svg + "<span>" + esc(text) + "</span></div>";
      }

      const IMAGE_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.6"/><path d="M21 15l-5-5L5 21"/></svg>';
      const SHOT_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 3l18 18M21 3L3 21"/></svg>';
      const AI_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/><circle cx="12" cy="12" r="3.2"/></svg>';

      const RENDERERS = {
        image: (c) => {
          if (!c.matched) return emptyHtml();
          if (c.imageUrl) return '<div class="img-box"><img src="' + esc(c.imageUrl) + '" alt="' + esc(c.brand || "商品主图") + '" /></div>';
          const initial = c.brand ? String(c.brand).charAt(0).toUpperCase() : "?";
          return '<div class="img-box" data-tip="' + esc(c.brand || "") + ' 商品主图占位">' +
            '<span class="brand-mark">' + esc(initial) + "</span><span>" + esc(c.brand || "商品主图") + "</span>" +
            '<span class="label-note">商品主图占位</span></div>';
        },
        asin: (c) => {
          if (!c.matched) return emptyHtml();
          const link = c.url ? '<a class="head-link" href="' + esc(c.url) + '" target="_blank" rel="noopener">打开商品链接</a>' : "";
          return '<div class="asin-block">' +
            '<button class="asin-copy" type="button" data-asin="' + esc(c.asin) + '">' +
            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>' +
            esc(c.asin) + '</button><span class="muted">点击复制</span><br>' + link + "</div>";
        },
        title: (c) => (c.matched && c.title ? rich(c.title) : emptyHtml()),
        price: (c) => {
          if (!c.matched) return emptyHtml();
          if (c.price === null || c.price === undefined) {
            return '<div class="price-box"><span class="price-empty">--</span><span class="muted">价格数据缺失</span></div>';
          }
          const priceHtml = '<span class="price-value">$' + esc(c.price) + "</span>" + (c.priceMock ? mockChip() : "");
          const origHtml = c.originalPrice ? '<span class="muted">原价 $' + esc(c.originalPrice) + "</span>" : "";
          const discHtml = c.discount ? '<span class="discount-chip">-' + esc(c.discount) + "%</span>" : "";
          return '<div class="price-box">' + priceHtml + origHtml + discHtml + "</div>";
        },
        launch: (c) => {
          if (!c.matched) return emptyHtml();
          const days = c.daysOnSale ? '<span class="muted">（已上架 ' + esc(fmt(c.daysOnSale)) + " 天）</span>" : "";
          return '<div class="rich-text">' + esc(c.launchDate || "--") + " " + days + "</div>";
        },
        rank: (c) => {
          if (!c.matched) return emptyHtml();
          return '<div class="rich-text"><div>大类：' + esc(c.rankCategory || "--") + "</div><div>小类：" + esc(c.rankSubcategory || "--") + "</div></div>";
        },
        rating: (c) => (c.matched && c.rating !== null && c.rating !== undefined ? starLine(c.rating) : emptyHtml()),
        reviews: (c) => (c.matched && c.reviewCount !== null && c.reviewCount !== undefined ? '<span style="font-size:16px;font-weight:700">' + esc(fmt(c.reviewCount)) + "</span>" : emptyHtml()),
        entityShot: (c) => (c.matched ? shotBox("实体截图占位（Excel 内嵌图片）", SHOT_SVG) : emptyHtml()),
        params: (c) => (c.matched && c.productParams ? rich(c.productParams) : emptyHtml()),
        package: (c) => (c.matched && c.packageInfo ? rich(c.packageInfo) : emptyHtml()),
        sales30d: (c) => {
          if (!c.matched) return emptyHtml();
          const num = c.sales30d === null || c.sales30d === undefined
            ? '<span class="empty">--</span>'
            : '<span style="font-size:18px;font-weight:800">' + esc(fmt(c.sales30d)) + "</span>" + (c.salesMock ? mockChip() : "");
          return '<div>' + num + '<span class="muted"> 件 / 30天</span></div>' + miniBars(c.salesTrend) + '<div class="label-note">迷你趋势</div>';
        },
        monthly: (c) => (c.matched ? barChart(c.monthlySales) : emptyHtml()),
        keepa: (c) => (c.matched ? keepaChart(c) : emptyHtml()),
        aiShot: (c) => (c.matched ? shotBox("AI 评论分析截图占位（Excel 内嵌图片）", AI_SVG) : emptyHtml()),
        selling: (c) => (c.matched && c.sellingPoints ? '<span class="tone-tag tone-blue-tag">产品卖点</span>' + rich(c.sellingPoints) : emptyHtml()),
        positive: (c) => (c.matched && c.positiveReviews ? '<span class="tone-tag tone-green-tag">好评点</span>' + rich(c.positiveReviews) : emptyHtml()),
        negative: (c) => (c.matched && c.negativeReviews ? '<span class="tone-tag tone-red-tag">差评点</span>' + rich(c.negativeReviews) : emptyHtml()),
        improve: (c) => (c.matched && c.improvementPoints ? '<span class="tone-tag tone-orange-tag">待改善点</span>' + rich(c.improvementPoints) : emptyHtml()),
        audience: (c) => (c.matched && c.targetAudience ? '<span class="tone-tag tone-orange-tag">使用人群</span>' + rich(c.targetAudience) : emptyHtml()),
        scenarios: (c) => (c.matched && c.useScenarios ? '<span class="tone-tag tone-orange-tag">使用场景</span>' + rich(c.useScenarios) : emptyHtml()),
        optimize: (c) => {
          if (!c.matched || !c.optimizationDirection) return emptyHtml();
          const dir = c.optimizationDirection;
          if (typeof dir === "string") return '<span class="tone-tag tone-green-tag">优化方向</span>' + rich(dir);
          const blocks = [];
          if (dir.a) blocks.push('<span class="tone-tag tone-green-tag">A级 · 核心必备</span>' + rich(dir.a));
          if (dir.b) blocks.push('<span class="tone-tag tone-blue-tag">B级 · 体验优化</span>' + rich(dir.b));
          if (dir.c) blocks.push('<span class="tone-tag tone-orange-tag">C级 · 长期迭代</span>' + rich(dir.c));
          return blocks.join('<div style="height:10px"></div>');
        },
      };

      function columnStatusHtml(p) {
        const chips = [];
        if (p.loading) chips.push('<span class="state-chip">加载中</span>');
        else if (p.cancelled) chips.push('<span class="state-chip error">已取消</span>');
        else if (p.error) chips.push('<span class="state-chip error">加载失败</span>');
        else if (p.done) {
          chips.push('<span class="state-chip done">' + esc(p.source || "模拟数据") + "</span>");
          if (p.cached) chips.push('<span class="cached-chip">缓存</span>');
        }
        let banner = "";
        if (p.degraded && p.degraded.message) {
          banner = '<div class="degrade-banner" data-tip="' + esc(p.degraded.message + "（来自 " + (p.degraded.provider || "") + "）") + '">' + esc(p.degraded.message) + "</div>";
        }
        if (p.error) {
          banner = '<button class="error-banner" type="button" data-retry="' + esc(p.asin) + '">数据加载失败，点击重试</button>';
        }
        return (chips.length ? '<div class="col-status">' + chips.join("") + banner + "</div>" : (banner ? '<div class="col-status">' + banner + "</div>" : ""));
      }

      function renderHead(asins) {
        const head = document.getElementById("tableHead");
        head.innerHTML = "<tr>" +
          '<th class="dim-head sticky">分析维度</th>' +
          asins.map((asin, i) => {
            const p = state.products[asin] || { asin, loading: true };
            const c = buildCompetitor(p);
            let brand = p.loading ? "查询中..." : (p.error ? "加载失败" : (p.cancelled ? "查询已取消" : (p.matched ? esc(c.brand) : "未匹配")));
            const badge = p.matched
              ? '<span class="badge">' + (i + 1) + "</span>"
              : (p.error ? '<span class="state-chip error">失败</span>' : '<span class="unmatched">未匹配</span>');
            const link = c.matched && c.url ? '<a class="head-link" href="' + esc(c.url) + '" target="_blank" rel="noopener">Amazon 链接</a>' : "";
            return '<th class="product-head" data-col="' + i + '">' +
              '<div class="head-brand">' + badge + "<span>" + brand + "</span></div>" +
              '<div class="asin-copy-row">' +
              '<button class="asin-copy" type="button" data-asin="' + esc(asin) + '">' +
              '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>' +
              esc(asin) + "</button>" + link + "</div>" +
              columnStatusHtml(p) +
              "</th>";
          }).join("") +
          "</tr>";
      }

      function renderBody(asins) {
        const body = document.getElementById("tableBody");
        let html = "";
        MODULES.forEach((mod) => {
          html += '<tr class="group-row">' +
            '<th class="group-label sticky tone-' + mod.tone + '">' + esc(mod.label) + "</th>" +
            '<td class="group-span tone-' + mod.tone + '" colspan="' + asins.length + '">' + esc(mod.span) + "</td></tr>";
          mod.rows.forEach((rowId) => {
            html += '<tr class="data-row">' +
              '<th class="row-label sticky">' + esc(ROW_LABELS[rowId] || rowId) + "</th>" +
              asins.map((asin, i) => {
                const p = state.products[asin] || { asin, loading: true };
                let content;
                if (p.loading) content = skeletonHtml(rowId);
                else if (p.error) content = '<div class="cell-error"><span>数据加载失败，点击重试</span><button class="btn btn-secondary btn-small" type="button" data-retry="' + esc(asin) + '">重试</button></div>';
                else if (p.cancelled) content = '<div class="cell-error"><span>查询已取消</span><button class="btn btn-secondary btn-small" type="button" data-retry="' + esc(asin) + '">重新查询</button></div>';
                else {
                  const c = buildCompetitor(p);
                  content = RENDERERS[rowId] ? RENDERERS[rowId](c) : emptyHtml();
                }
                return '<td class="cell" data-col="' + i + '">' + content + "</td>";
              }).join("") +
              "</tr>";
          });
        });
        body.innerHTML = html;
      }

      function render(asins) {
        state.asins = asins;
        renderHead(asins);
        renderBody(asins);
      }

      function parseAsins(input) {
        const parts = String(input || "").split(/[,，;；\s]+/).map((s) => s.trim()).filter(Boolean);
        if (parts.length > 6) {
          showToast("最多支持 6 个 ASIN，已取前 6 个");
          return parts.slice(0, 6);
        }
        return parts;
      }
      function currentAsins() { return parseAsins(document.getElementById("asinInput").value); }

      /*
       * ============================================================
       * 10. 批量查询队列 / 进度 / 取消 / 重试
       * ============================================================
       */
      async function startQuery(asins, opts = {}) {
        if (!asins.length) { showToast("请输入至少 1 个 ASIN"); return; }
        if (state.running) manager.cancel();
        state.running = true;
        state.products = {};
        asins.forEach((asin) => { state.products[asin] = { asin, loading: true }; });
        render(asins);
        document.getElementById("progressWrap").hidden = false;
        document.getElementById("progressFill").style.width = "0%";
        document.getElementById("progressText").textContent = "正在查询 0/" + asins.length + "...";
        document.getElementById("statusAsins").textContent = "已加载：" + asins.length + " 个 ASIN（" + asins.join("、") + "）";
        updateSourceStatus("查询中...");

        await manager.queryBatch(asins, {
          onColumn: (res) => {
            const p = state.products[res.asin] || {};
            state.products[res.asin] = Object.assign({}, p, res, { loading: false, done: true, error: !!res.error, cancelled: false });
            render(asins);
          },
          onProgress: (info) => {
            document.getElementById("progressFill").style.width = Math.round((info.done / info.total) * 100) + "%";
            document.getElementById("progressText").textContent = "正在查询 " + info.done + "/" + info.total + "...";
          },
          onDone: (info) => {
            state.running = false;
            document.getElementById("progressFill").style.width = "100%";
            document.getElementById("progressText").textContent = "查询完成，耗时" + info.elapsed.toFixed(1) + "秒，成功" + info.success + "个，失败" + info.failed + "个";
            document.getElementById("statusAsins").textContent = "查询完成：" + info.success + " 成功 / " + info.failed + " 失败";
            setTimeout(() => { if (!state.running) document.getElementById("progressWrap").hidden = true; }, 4000);
            updateSourceStatus("查询完成");
            if (opts.onDone) opts.onDone(info);
          },
          onCancel: (info) => {
            state.running = false;
            document.getElementById("progressText").textContent = "已取消查询（完成 " + info.done + "/" + info.total + "）";
            document.getElementById("progressWrap").hidden = false;
            document.getElementById("statusAsins").textContent = "查询已取消";
            updateSourceStatus("查询已取消");
          },
        });
      }

      async function retryAsin(asin) {
        const cfg = manager.config.general || {};
        state.products[asin] = { asin, loading: true };
        render(state.asins);
        try {
          const res = await manager.fetchOne(asin, cfg.site || "US");
          state.products[asin] = Object.assign({}, res, { loading: false, done: true, error: false, cancelled: false });
        } catch (err) {
          state.products[asin] = { asin, loading: false, error: true, done: false, data: {}, source: null };
        }
        render(state.asins);
        showToast("已重试 " + asin);
      }

      function doQuery() { startQuery(currentAsins()); }
      function doReset() {
        document.getElementById("asinInput").value = DEFAULT_ASINS.join(",");
        startQuery(DEFAULT_ASINS);
      }

      let toastTimer = null;
      function showToast(msg) {
        const el = document.getElementById("toast");
        el.textContent = msg;
        el.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
      }
      async function copyText(text, msg) {
        try { await navigator.clipboard.writeText(text); }
        catch (err) {
          const ta = document.createElement("textarea");
          ta.value = text;
          ta.style.position = "fixed"; ta.style.opacity = "0";
          document.body.appendChild(ta); ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        }
        showToast(msg || "已复制");
      }

      function buildReport() {
        const asins = currentAsins();
        const lines = [];
        lines.push("亚马逊竞品自动化分析系统 - 横向对比报告");
        lines.push("数据来源：" + (manager.listProviders().find((p) => p.id === manager.activeMain)?.name || manager.activeMain) + "（" + (manager.config.general?.mode === "mixed" ? "混合模式" : "单一数据源") + "）");
        lines.push("");
        asins.forEach((asin, idx) => {
          const p = state.products[asin] || {};
          const c = buildCompetitor(p);
          lines.push("【竞品 " + (idx + 1) + "】" + (c.matched ? (c.brand || "") + " / " : "") + asin);
          if (!c.matched) { lines.push("  暂无该商品数据"); lines.push(""); return; }
          if (c.title) lines.push("  标题：" + c.title);
          if (c.price !== null && c.price !== undefined) lines.push("  售价：$" + c.price + (c.originalPrice ? "（原价 $" + c.originalPrice + "）" : ""));
          if (c.launchDate) lines.push("  上线时间：" + c.launchDate + (c.daysOnSale ? "（" + c.daysOnSale + "天）" : ""));
          if (c.rankCategory || c.rankSubcategory) lines.push("  排名：" + (c.rankCategory || "--") + " / " + (c.rankSubcategory || "--"));
          if (c.rating !== null && c.rating !== undefined) lines.push("  评分：" + c.rating);
          if (c.reviewCount !== null && c.reviewCount !== undefined) lines.push("  评论数：" + c.reviewCount);
          if (c.productParams) lines.push("  产品参数信息：" + c.productParams);
          if (c.packageInfo) lines.push("  包装尺寸及重量：" + c.packageInfo);
          const anaFields = [
            ["产品卖点", c.sellingPoints], ["好评点", c.positiveReviews], ["差评点", c.negativeReviews],
            ["待改善点", c.improvementPoints], ["使用人群", c.targetAudience], ["使用场景", c.useScenarios],
            ["优化方向", typeof c.optimizationDirection === "string" ? c.optimizationDirection : null],
          ];
          anaFields.forEach(([label, val]) => { if (val) lines.push("  " + label + "：\n" + val); });
          lines.push("");
        });
        return lines.join("\n");
      }

      /*
       * ============================================================
       * 11. 配置面板
       * ============================================================
       */
      function updateSourceStatus(text) {
        const meta = manager.listProviders().find((p) => p.id === manager.activeMain);
        const base = text || (meta ? meta.name : manager.activeMain);
        document.getElementById("sourceStatus").textContent = base + " · 当前使用模拟数据，后续可接入MCP获取真实亚马逊数据";
      }
      function initSourceSelect() {
        const sel = document.getElementById("sourceSelect");
        sel.innerHTML = manager.listProviders().map((p) =>
          '<option value="' + esc(p.id) + '"' + (p.id === manager.activeMain ? " selected" : "") + ">" + esc(p.name) + "</option>"
        ).join("");
      }
      function applyConfigToForm() {
        const cfg = manager.config;
        document.getElementById("siteSelect").value = cfg.general.site || "US";
        document.getElementById("timeoutInput").value = cfg.general.timeout;
        document.getElementById("retriesInput").value = cfg.general.retries;
        document.getElementById("concurrencyInput").value = cfg.general.concurrency;
        document.getElementById("intervalInput").value = cfg.general.requestIntervalMs;
        document.getElementById("modeSelect").value = cfg.general.mode;
        document.getElementById("mcpUrl").value = cfg.sellersprite.mcpServerUrl || "";
        document.getElementById("mcpKey").value = cfg.sellersprite.apiKey || "";
        document.getElementById("paAccess").value = cfg.pa.accessKey || "";
        document.getElementById("paSecret").value = cfg.pa.secretKey || "";
        document.getElementById("paTag").value = cfg.pa.partnerTag || "";
        document.getElementById("paType").value = cfg.pa.partnerType || "Associates";
        document.getElementById("keepaKey").value = cfg.keepa.keepaApiKey || "";
        document.getElementById("keepaDomain").value = cfg.keepa.domainId || 1;
        document.getElementById("keepaQuota").textContent = loadKeepaQuota() ?? "--";
        updateConnectionLights();
      }
      function collectConfigFromForm() {
        const cfg = manager.config;
        cfg.mainProvider = manager.activeMain;
        cfg.general.site = document.getElementById("siteSelect").value;
        cfg.general.timeout = Math.max(1, Number(document.getElementById("timeoutInput").value) || 10);
        cfg.general.retries = Math.max(0, Number(document.getElementById("retriesInput").value) || 0);
        cfg.general.concurrency = Math.max(1, Math.min(6, Number(document.getElementById("concurrencyInput").value) || 3));
        cfg.general.requestIntervalMs = Math.max(0, Number(document.getElementById("intervalInput").value) || 0);
        cfg.general.mode = document.getElementById("modeSelect").value;
        cfg.sellersprite.mcpServerUrl = document.getElementById("mcpUrl").value.trim();
        cfg.sellersprite.apiKey = document.getElementById("mcpKey").value.trim();
        cfg.pa.accessKey = document.getElementById("paAccess").value.trim();
        cfg.pa.secretKey = document.getElementById("paSecret").value.trim();
        cfg.pa.partnerTag = document.getElementById("paTag").value.trim();
        cfg.pa.partnerType = document.getElementById("paType").value;
        cfg.keepa.keepaApiKey = document.getElementById("keepaKey").value.trim();
        cfg.keepa.domainId = Number(document.getElementById("keepaDomain").value) || 1;
        return cfg;
      }
      function updateConnectionLights() {
        const cfg = manager.config;
        setLight("mcp", cfg.sellersprite.apiKey && cfg.sellersprite.mcpServerUrl ? "未测试" : "未配置");
        setLight("pa", cfg.pa.accessKey && cfg.pa.secretKey && cfg.pa.partnerTag ? "未测试" : "未配置");
        setLight("keepa", cfg.keepa.keepaApiKey ? "未测试" : "未配置");
      }
      function setLight(name, text, color) {
        const light = document.getElementById(name + "Light");
        const span = document.getElementById(name + "StatusText");
        if (!light || !span) return;
        light.className = "light " + (color || "gray");
        span.textContent = text;
      }
      function openConfig() {
        applyConfigToForm();
        document.getElementById("configModal").hidden = false;
      }
      function closeConfig() { document.getElementById("configModal").hidden = true; }

      function initConfigModal() {
        document.getElementById("configBtn").addEventListener("click", openConfig);
        document.getElementById("configClose").addEventListener("click", closeConfig);
        document.getElementById("configCancel").addEventListener("click", closeConfig);
        document.querySelectorAll(".tab").forEach((btn) => {
          btn.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
          });
        });
        document.getElementById("mcpKeyToggle").addEventListener("click", () => {
          const input = document.getElementById("mcpKey");
          const show = input.type === "password";
          input.type = show ? "text" : "password";
          document.getElementById("mcpKeyToggle").textContent = show ? "隐藏" : "显示";
        });
        document.getElementById("testMcpBtn").addEventListener("click", async () => {
          collectConfigFromForm();
          const provider = new SellerspriteMCPProvider(manager.config.sellersprite);
          const res = await provider.testConnection();
          setLight("mcp", res.status === "connected" ? "已连接" : res.message, res.status === "connected" ? "green" : (res.status === "failed" ? "red" : "gray"));
        });
        document.getElementById("testPaBtn").addEventListener("click", async () => {
          collectConfigFromForm();
          const provider = new AmazonPaApiProvider(manager.config.pa);
          const res = await provider.testConnection();
          setLight("pa", res.status === "connected" ? "已连接" : res.message, res.status === "connected" ? "green" : (res.status === "failed" ? "red" : "gray"));
        });
        document.getElementById("testKeepaBtn").addEventListener("click", async () => {
          collectConfigFromForm();
          const provider = new KeepaApiProvider(manager.config.keepa);
          const res = await provider.testConnection();
          setLight("keepa", res.status === "connected" ? "已连接" : res.message, res.status === "connected" ? "green" : (res.status === "failed" ? "red" : "gray"));
          document.getElementById("keepaQuota").textContent = loadKeepaQuota() ?? "--";
        });
        document.getElementById("configSave").addEventListener("click", () => {
          collectConfigFromForm();
          saveConfig(manager.config);
          closeConfig();
          showToast("配置已保存");
          startQuery(currentAsins());
        });
        window.addEventListener("keepa-quota-update", (e) => {
          document.getElementById("keepaQuota").textContent = e.detail ?? "--";
        });
      }

      /*
       * ============================================================
       * 12. 事件绑定与初始化
       * ============================================================
       */
      function initEvents() {
        document.getElementById("compareTable").addEventListener("mouseover", (e) => {
          const cell = e.target.closest("[data-col]");
          if (!cell) { clearColumnHighlight(); return; }
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
            tip.style.left = Math.min(rect.left, window.innerWidth - 480) + "px";
            tip.style.top = Math.min(rect.bottom + 8, window.innerHeight - 80) + "px";
          } else { tip.classList.remove("show"); }
        });
        document.addEventListener("click", (e) => {
          const copyBtn = e.target.closest("[data-asin]");
          if (copyBtn) copyText(copyBtn.dataset.asin, "已复制：" + copyBtn.dataset.asin);
          const retryBtn = e.target.closest("[data-retry]");
          if (retryBtn) retryAsin(retryBtn.dataset.retry);
        });
        document.getElementById("queryBtn").addEventListener("click", doQuery);
        document.getElementById("resetBtn").addEventListener("click", doReset);
        document.getElementById("cancelBtn").addEventListener("click", () => {
          manager.cancel();
          state.running = false;
          Object.values(state.products).forEach((p) => {
            if (p.loading) p.cancelled = true;
            p.loading = false;
          });
          render(state.asins);
        });
        document.getElementById("copyBtn").addEventListener("click", () => copyText(buildReport(), "报告已复制"));
        document.getElementById("asinInput").addEventListener("keydown", (e) => { if (e.key === "Enter") doQuery(); });
        document.getElementById("sourceSelect").addEventListener("change", (e) => {
          manager.activeMain = e.target.value;
          manager.config.mainProvider = manager.activeMain;
          saveConfig(manager.config);
          showToast("已切换数据源：" + (manager.listProviders().find((p) => p.id === manager.activeMain)?.name || manager.activeMain));
          startQuery(currentAsins());
        });
        document.getElementById("configModal").addEventListener("click", (e) => {
          if (e.target.id === "configModal") closeConfig();
        });
      }

      let currentCol = null;
      function clearColumnHighlight() {
        if (currentCol === null) return;
        document.querySelectorAll('[data-col="' + currentCol + '"]').forEach((el) => el.classList.remove("col-hot"));
        currentCol = null;
      }

      /* 兼容旧版 MCP 注入入口 */
      window.mcpCompetitorAdapter = {
        setRawData: (list) => { window.mcpImport && window.mcpImport({ raw: list }); },
        setAnalysis: (list) => { window.mcpImport && window.mcpImport({ analysis: list }); },
        render: () => render(state.asins),
      };
      window.mcpImport = (payload) => {
        if (!payload) return;
        if (payload.raw) payload.raw.forEach((p) => { if (p && p.asin && MOCK_CATALOG[p.asin]) Object.assign(MOCK_CATALOG[p.asin].basicInfo, p); });
        if (payload.analysis) payload.analysis.forEach((p) => { if (p && p.asin && MOCK_CATALOG[p.asin]) Object.assign(MOCK_CATALOG[p.asin].reviewsData, p); });
        startQuery(currentAsins());
      };

      function init() {
        initSourceSelect();
        initConfigModal();
        initEvents();
        document.getElementById("asinInput").value = DEFAULT_ASINS.join(",");
        startQuery(DEFAULT_ASINS);
      }
      init();
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
