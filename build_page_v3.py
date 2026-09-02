# -*- coding: utf-8 -*-
"""Generate index.html: six independent competitor columns, keeping original UI/styles."""
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

      /*
       * ============================================================
       * V3 新增样式：6 列独立竞品卡片网格（追加在末尾，不删除旧样式）
       * ============================================================
       */
      .columns-page { max-width: 1920px; }
      .competitor-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 14px;
        align-items: start;
      }
      .competitor-col {
        min-width: 0;
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        display: flex;
        flex-direction: column;
      }
      .competitor-col-head {
        padding: 10px 12px;
        background: #f8fafc;
        border-bottom: 1px solid var(--line);
      }
      .competitor-col-title {
        font-size: 13px;
        font-weight: 700;
        color: #334155;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }
      .competitor-col-title .num {
        width: 22px; height: 22px;
        border-radius: 50%;
        background: #dbe7f5;
        color: #2563eb;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
      }
      .competitor-col .col-query {
        display: flex;
        flex-direction: column;
        gap: 7px;
      }
      .competitor-col .col-query input {
        width: 100%;
        height: 34px;
        padding: 0 10px;
        border: 1px solid #cfd8e3;
        border-radius: 6px;
        font-size: 12px;
        color: var(--text);
        background: #fbfcfe;
        outline: none;
        font-family: Consolas, "Courier New", monospace;
      }
      .competitor-col .col-query input:focus { border-color: #6fa8dc; box-shadow: 0 0 0 3px rgba(111, 168, 220, 0.15); }
      .competitor-col .col-actions { display: flex; gap: 6px; }
      .competitor-col .col-actions .btn {
        flex: 1;
        height: 30px;
        padding: 0 8px;
        font-size: 12px;
        border-radius: 6px;
      }
      .competitor-card {
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-width: 0;
      }
      .competitor-card .cell { width: auto; min-width: 0; padding: 0; border: 0; background: transparent; }
      .competitor-card .card-section {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
      }
      .competitor-card .card-section-head {
        padding: 7px 10px;
        font-size: 12px;
        font-weight: 700;
        border-bottom: 1px solid var(--line);
      }
      .competitor-card .card-section-head.blue { background: var(--blue); color: #1d4ed8; }
      .competitor-card .card-section-head.gray { background: var(--gray); color: #475569; }
      .competitor-card .card-section-head.red { background: var(--red); color: #b91c1c; }
      .competitor-card .card-section-head.orange { background: var(--orange); color: #b45309; }
      .competitor-card .card-section-head.green { background: var(--green); color: #047857; }
      .competitor-card .card-section-body { padding: 9px 10px; }
      .competitor-card .kv-row {
        display: flex;
        gap: 8px;
        padding: 5px 0;
        border-bottom: 1px dashed #edf1f5;
        font-size: 12px;
        line-height: 1.6;
      }
      .competitor-card .kv-row:last-child { border-bottom: 0; }
      .competitor-card .kv-label {
        flex: 0 0 86px;
        color: var(--muted);
        font-weight: 600;
      }
      .competitor-card .kv-value {
        flex: 1;
        min-width: 0;
        word-break: break-word;
        white-space: pre-wrap;
        color: #374151;
      }
      .competitor-card .kv-value.asin-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 700;
        word-break: break-all;
      }
      .competitor-card .kv-value.asin-link:hover { text-decoration: underline; }
      .competitor-card .mini-image {
        width: 88px;
        height: 88px;
        border: 1px dashed #b9c6d4;
        border-radius: 6px;
        background: #f6f8fb;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #64748b;
        font-size: 11px;
        text-align: center;
        overflow: hidden;
      }
      .competitor-card .mini-image img { max-width: 100%; max-height: 100%; object-fit: contain; }
      .competitor-card .keepa-placeholder {
        border: 1px dashed #b9c6d4;
        border-radius: 6px;
        background: #fbfcfe;
        min-height: 90px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #64748b;
        font-size: 12px;
        text-align: center;
        padding: 8px;
      }
      .competitor-card .fold-text {
        position: relative;
        max-height: 150px;
        overflow: hidden;
        transition: max-height 0.25s ease;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 12px;
        line-height: 1.65;
      }
      .competitor-card .fold-text.expanded { max-height: none; }
      .competitor-card .fold-btn {
        border: 0;
        background: none;
        color: #2563eb;
        font-size: 12px;
        cursor: pointer;
        padding: 3px 0 0;
        align-self: flex-start;
      }
      .competitor-card .fold-btn:hover { text-decoration: underline; }
      .competitor-card .placeholder-note { color: var(--muted); font-size: 11px; margin-top: 5px; }
      .competitor-card .state-note { color: #6b7280; font-size: 11px; margin-top: 6px; }
      .competitor-col .skeleton { margin: 12px; }
      .competitor-card .card-status {
        font-size: 11px;
        color: #047857;
        background: #dcf5e8;
        border-radius: 999px;
        padding: 2px 8px;
        align-self: flex-start;
      }

      @media (max-width: 1500px) {
        .competitor-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }
      @media (max-width: 900px) {
        .competitor-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 560px) {
        .competitor-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <!-- ????????????????????????? -->
    <header class="page top-card">
      <div class="top-head">
        <div>
          <h1>????????????</h1>
          <p class="sub">6 ???????? ? ??????/??/????????????????</p>
        </div>
        <div class="top-tools">
          <label class="source-picker">
            <span>???</span>
            <select id="sourceSelect"></select>
          </label>
          <button class="icon-btn" id="configBtn" type="button">?? ?????</button>
        </div>
      </div>
      <div class="status-line">
        <span><span class="dot"></span><span id="statusAsins">6 ??????? ? ??????? ASIN</span></span>
        <span id="sourceStatus" class="source">??????????????MCP?????????</span>
      </div>
    </header>

    <!-- ????6?????????????? -->
    <main class="page columns-page">
      <div class="grid-6-col competitor-grid" id="competitorGrid"></div>
      <p class="foot-note">?????????????????????????? ASIN ???????????</p>
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
            <p class="hint">混合模式映射：基础信息 = PA-API，销量 = 卖家精灵，趋势 = Keepa，评论/参数 = 模拟数据。未配置的数据源会自动降级到主数据源或模拟数据。</p>
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

      /* ============================================================
       * 基础工具与统一数据格式
       * ============================================================ */
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

      /* ============================================================
       * 配置与缓存（localStorage）
       * ============================================================ */
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
        } catch (err) { return defaultConfig(); }
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
          const readback = localStorage.getItem(CACHE_KEY);
          if (readback === null) console.warn("localStorage 不可用，缓存仅保留在内存");
        } catch (err) { console.warn("缓存保存失败", err); }
      }
      function loadKeepaQuota() {
        try { return Number(localStorage.getItem(QUOTA_KEY)) || null; } catch (err) { return null; }
      }
      function saveKeepaQuota(n) {
        try { localStorage.setItem(QUOTA_KEY, String(n)); } catch (err) {}
      }

      /* ============================================================
       * Provider 基类与统一接口
       * ============================================================ */
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

      /* ============================================================
       * 适配器 A：模拟数据（MockDataProvider）—— 默认数据源
       * ============================================================ */
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

      /* ============================================================
       * 适配器 B：卖家精灵 MCP（SellerspriteMCPProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
       * 已预留 MCP 方法：
       *   get_product_info(asin, marketplace)         → 基础信息
       *   get_product_sales(asin, marketplace, period) → 销量
       *   get_asins_sales_rank(asin, marketplace)      → BSR 排名
       *   get_product_reviews(asin, marketplace)       → 评论关键词与摘要
       */
      class SellerspriteMCPProvider extends ProductDataProvider {
        get id() { return "sellersprite-mcp"; }
        get label() { return "卖家精灵MCP"; }
        isConfigured() { return !!(this.config.apiKey && this.config.mcpServerUrl); }
        async _callMcp(method, params) {
          if (!this.isConfigured()) throw new ProviderNotConfiguredError("卖家精灵MCP未配置");
          /* 此处填入真实请求逻辑 */
          throw new ProviderRequestError("卖家精灵 MCP 尚未接入：请在 SellerspriteMCPProvider._callMcp 中填入真实请求逻辑");
        }
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

      /* ============================================================
       * 适配器 C：亚马逊 PA-API 5.0（AmazonPaApiProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
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
          /* 此处填入真实请求逻辑：AWS SigV4 签名后 POST /paapi5/{endpoint} */
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
            Resources: ["Images.Primary.Large", "ItemInfo.Title", "ItemInfo.ByLineInfo", "ItemInfo.Classifications", "ItemInfo.ExternalIds", "Offers.Listings.Price", "CustomerReviews.Count", "CustomerReviews.StarRating", "BrowseNodeInfo.BrowseNodes"],
          };
          const raw = await this._paApiRequest("getitems", payload, marketplace);
          const item = raw?.ItemsResult?.Items?.[0];
          if (!item) throw new ProviderRequestError("PA-API 未返回商品：" + asin);
          return this._toBasic(asin, marketplace, item);
        }
        async getSalesData(asin, marketplace) {
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
          const out = empty("reviewsData", asin, marketplace);
          out.found = false;
          return out;
        }
        async getProductSpecs(asin, marketplace) {
          const payload = { ItemIds: [asin], Resources: ["ItemInfo.Features", "ItemInfo.ProductInfo", "ItemInfo.ManufactureInfo", "Offers.Listings.Price"] };
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
            await this._paApiRequest("getitems", { ItemIds: ["B0B441L1K6"], Resources: ["ItemInfo.Title"] }, "US");
            return { ok: true, status: "connected", message: "PA-API 连接成功" };
          } catch (err) {
            return { ok: false, status: "failed", message: "连接失败：" + err.message };
          }
        }
      }

      /* ============================================================
       * 适配器 D：Keepa API（KeepaApiProvider）
       * ============================================================
       * 接入步骤：1. 填 Key 2. 切换数据源 3. 重新查询
       * Domain ID：1=US, 2=UK, 3=DE, 4=FR, 5=JP, 6=CA, 12=AU
       */
      class KeepaApiProvider extends ProductDataProvider {
        get id() { return "keepa-api"; }
        get label() { return "Keepa API"; }
        isConfigured() { return !!this.config.keepaApiKey; }
        async _callProduct(asin, marketplace, light = false) {
          if (!this.isConfigured()) throw new ProviderNotConfiguredError("Keepa API未配置");
          const domain = this.config.domainId || KEEPA_DOMAINS[marketplace] || 1;
          /* 此处填入真实请求逻辑：GET https://api.keepa.com/product?key=...&asin=...&domain=... */
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

      /* ============================================================
       * Provider 注册表 + DataProviderManager
       * ============================================================ */
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
       * V3 页面主体：6 列独立竞品查询（每列独立输入/查询/重置/渲染）
       * ============================================================
       */
      const manager = new DataProviderManager();
      const COL_COUNT = 6;
      const COLUMN_KEYS = ["A", "B", "C", "D", "E", "F"];
      const columns = [];

      /* 竞品字段模型：与后续 MCP/API 返回的单条竞品对象一致 */
      const FIELD_KEYS = [
        "品牌", "图片", "ASIN", "链接", "标题", "售价", "上线时间", "排名", "评分", "评论数",
        "变体", "产品参数信息", "包装尺寸及重量", "30天销量(畅销变体)", "历史月销", "Keepa趋势",
        "AI评论分析", "产品卖点", "好评点", "差评点", "待改善点", "使用人群", "使用场景", "优化方向",
      ];

      function emptyProduct(asin) {
        const obj = {};
        FIELD_KEYS.forEach((k) => { obj[k] = ""; });
        if (asin) obj["ASIN"] = asin;
        return obj;
      }

      function buildProductFromResult(p) {
        const obj = emptyProduct(p.asin);
        const b = p.data.basicInfo || {};
        const s = p.data.salesData || {};
        const k = p.data.keepaData || {};
        const r = p.data.reviewsData || {};
        const sp = p.data.specs || {};
        obj["品牌"] = b.brand || "";
        obj["图片"] = b.imageUrl || "";
        obj["ASIN"] = p.asin;
        obj["链接"] = b.url || ("https://www.amazon.com/dp/" + p.asin);
        obj["标题"] = b.title || "";
        obj["售价"] = b.price !== null && b.price !== undefined
          ? "$" + b.price + (b.originalPrice ? "（原价 $" + b.originalPrice + "）" : "") + (b.discount ? "，-" + b.discount + "%" : "")
          : "";
        const launch = b.launchDate ? String(b.launchDate) : "";
        obj["上线时间"] = launch + (b.daysOnSale ? "（" + b.daysOnSale + "天）" : "");
        obj["排名"] = [b.category || s.bsrCategory, b.subcategory || s.bsrSubcategory].filter(Boolean).join("\n");
        obj["评分"] = b.rating !== null && b.rating !== undefined ? String(b.rating) : "";
        obj["评论数"] = b.reviewCount !== null && b.reviewCount !== undefined ? fmt(b.reviewCount) : "";
        obj["变体"] = sp.variants ? (Array.isArray(sp.variants) ? sp.variants.join("；") : String(sp.variants)) : "";
        obj["产品参数信息"] = sp.productParams || "";
        obj["包装尺寸及重量"] = sp.packageInfo || "";
        obj["30天销量(畅销变体)"] = s.sales30d !== null && s.sales30d !== undefined ? String(s.sales30d) : "";
        obj["历史月销"] = s.monthlySales && s.monthlySales.length ? s.monthlySales.join(", ") : "";
        obj["Keepa趋势"] = k.priceTrend && k.priceTrend.length ? "价格/BSR 趋势数据" : "";
        obj["AI评论分析"] = r.summary || "";
        obj["产品卖点"] = r.sellingPoints || "";
        obj["好评点"] = r.positiveReviews || "";
        obj["差评点"] = r.negativeReviews || "";
        obj["待改善点"] = r.improvementPoints || "";
        obj["使用人群"] = r.targetAudience || "";
        obj["使用场景"] = r.useScenarios || "";
        obj["优化方向"] = typeof r.optimizationDirection === "string"
          ? r.optimizationDirection
          : (r.optimizationDirection ? [r.optimizationDirection.a, r.optimizationDirection.b, r.optimizationDirection.c].filter(Boolean).join("\n") : "");
        return obj;
      }

      function foldTextHtml(text, uid) {
        if (!text) return '<span class="empty">--</span>';
        const safe = esc(text);
        return '<div class="fold-text" id="fold-' + uid + '" data-tip="' + safe + '">' + safe + "</div>" +
          '<button class="fold-btn" type="button" data-fold="' + uid + '">展开</button>';
      }

      function renderColumn(column) {
        const el = document.getElementById("col-card-" + column.index);
        if (!el) return;
        const p = column.product;
        if (!p || !p.done) {
          el.innerHTML =
            '<div class="card-section"><div class="card-section-head blue">基础商品信息</div><div class="card-section-body">' +
            '<div class="skeleton"><span class="sk img"></span><span class="sk w60"></span><span class="sk w80"></span></div>' +
            '</div></div>' +
            '<div class="card-section"><div class="card-section-head gray">销量趋势数据</div><div class="card-section-body">' +
            '<div class="skeleton"><span class="sk w80"></span><span class="sk w60"></span></div>' +
            '</div></div>' +
            '<div class="card-section"><div class="card-section-head red">AI文本分析</div><div class="card-section-body">' +
            '<div class="skeleton"><span class="sk w40"></span><span class="sk w80"></span><span class="sk w60"></span></div>' +
            '</div></div>';
          return;
        }

        if (p.error) {
          el.innerHTML =
            '<div class="cell-error"><span>数据加载失败，点击重试</span>' +
            '<button class="btn btn-secondary btn-small" type="button" data-col-retry="' + column.index + '">重试</button></div>';
          return;
        }

        const obj = buildProductFromResult(p);
        const uid = "c" + column.index;
        const baseRows = [
          ["品牌", obj["品牌"]],
          ["图片", obj["图片"]],
          ["ASIN", obj["ASIN"]],
          ["链接", obj["链接"]],
          ["标题", obj["标题"]],
          ["售价", obj["售价"]],
          ["上线时间", obj["上线时间"]],
          ["排名", obj["排名"]],
          ["评分", obj["评分"]],
          ["评论数", obj["评论数"]],
          ["变体", obj["变体"]],
          ["产品参数信息", obj["产品参数信息"]],
          ["包装尺寸及重量", obj["包装尺寸及重量"]],
        ];
        const salesRows = [
          ["30天销量(畅销变体)", obj["30天销量(畅销变体)"]],
          ["历史月销", obj["历史月销"]],
          ["Keepa趋势", obj["Keepa趋势"]],
        ];
        const aiRows = [
          ["AI评论分析", obj["AI评论分析"]],
          ["产品卖点", obj["产品卖点"]],
          ["好评点", obj["好评点"]],
          ["差评点", obj["差评点"]],
          ["待改善点", obj["待改善点"]],
          ["使用人群", obj["使用人群"]],
          ["使用场景", obj["使用场景"]],
          ["优化方向", obj["优化方向"]],
        ];

        const rowHtml = (label, value, opts = {}) => {
          const { image = false, link = false, fold = false } = opts;
          let valueHtml = "";
          if (image) {
            valueHtml = value
              ? '<div class="mini-image"><img src="' + esc(value) + '" alt="' + esc(label) + '" /></div>'
              : '<div class="mini-image">商品图片占位</div>';
          } else if (link) {
            valueHtml = value
              ? '<a class="kv-value asin-link" href="' + esc(value) + '" target="_blank" rel="noopener">' + esc(value) + "</a>"
              : '<span class="empty">--</span>';
          } else if (fold) {
            valueHtml = foldTextHtml(value, uid + "-" + label);
          } else {
            valueHtml = value ? '<div class="kv-value" data-tip="' + esc(value) + '">' + esc(value) + "</div>" : '<span class="empty">--</span>';
          }
          return '<div class="kv-row"><span class="kv-label">' + esc(label) + "</span>" + valueHtml + "</div>";
        };

        let html = "";
        html += '<div class="card-section"><div class="card-section-head blue">基础商品信息</div><div class="card-section-body">';
        html += rowHtml("品牌", obj["品牌"]);
        html += rowHtml("图片", obj["图片"], { image: true });
        html += rowHtml("ASIN", "https://www.amazon.com/dp/" + obj["ASIN"], { link: true });
        html += rowHtml("链接", obj["链接"], { link: true });
        html += rowHtml("标题", obj["标题"], { fold: true });
        html += rowHtml("售价", obj["售价"]);
        html += rowHtml("上线时间", obj["上线时间"]);
        html += rowHtml("排名", obj["排名"]);
        html += rowHtml("评分", obj["评分"]);
        html += rowHtml("评论数", obj["评论数"]);
        html += rowHtml("变体", obj["变体"]);
        html += rowHtml("产品参数信息", obj["产品参数信息"], { fold: true });
        html += rowHtml("包装尺寸及重量", obj["包装尺寸及重量"], { fold: true });
        html += '</div></div>';

        html += '<div class="card-section"><div class="card-section-head gray">销量趋势数据</div><div class="card-section-body">';
        html += rowHtml("30天销量(畅销变体)", obj["30天销量(畅销变体)"]);
        html += rowHtml("历史月销", obj["历史月销"], { fold: true });
        html += '<div class="kv-row"><span class="kv-label">Keepa趋势</span><div class="kv-value">' +
          '<div class="keepa-placeholder">Keepa 趋势截图占位<br><span class="placeholder-note">后续放置价格 / BSR 走势图</span></div></div></div>';
        html += '</div></div>';

        html += '<div class="card-section"><div class="card-section-head red">AI文本分析</div><div class="card-section-body">';
        aiRows.forEach(([label, value]) => {
          html += rowHtml(label, value, { fold: true });
        });
        html += '</div></div>';

        html += '<div class="card-status">' + esc(p.source || "模拟数据") + (p.degraded ? " · 已降级" : "") + (p.cached ? " · 缓存" : "") + "</div>";
        el.innerHTML = html;
        el.querySelectorAll("[data-fold]").forEach((btn) => {
          btn.addEventListener("click", () => {
            const target = document.getElementById("fold-" + btn.dataset.fold);
            if (!target) return;
            const expanded = target.classList.toggle("expanded");
            btn.textContent = expanded ? "收起" : "展开";
          });
        });
      }

      function renderAllColumns() {
        columns.forEach(renderColumn);
      }

      function buildColumnShell(index) {
        const asin = DEFAULT_ASINS[index] || "";
        const column = {
          index,
          asin,
          product: null,
          loading: false,
        };
        columns.push(column);
        const grid = document.getElementById("competitorGrid");
        const shell = document.createElement("div");
        shell.className = "competitor-col";
        shell.id = "col-" + index;
        shell.innerHTML =
          '<div class="competitor-col-head">' +
          '<div class="competitor-col-title"><span class="num">' + COLUMN_KEYS[index] + "</span><span>竞品 " + (index + 1) + "</span></div>" +
          '<div class="col-query">' +
          '<input id="col-input-' + index + '" type="text" placeholder="输入 ASIN，如 B0B441L1K6" autocomplete="off" value="' + esc(asin) + '" />' +
          '<div class="col-actions">' +
          '<button class="btn btn-primary" type="button" data-col-query="' + index + '">查询</button>' +
          '<button class="btn btn-secondary" type="button" data-col-reset="' + index + '">重置</button>' +
          '</div></div></div>' +
          '<div class="competitor-card" id="col-card-' + index + '"></div>';
        grid.appendChild(shell);
        return column;
      }

      async function queryColumn(index) {
        const column = columns[index];
        const input = document.getElementById("col-input-" + index);
        const asin = (input.value || "").trim().toUpperCase();
        if (!asin) {
          showToast("请先输入 ASIN");
          return;
        }
        column.asin = asin;
        column.product = { asin, loading: true };
        column.loading = true;
        renderColumn(column);
        updateStatusText("正在查询 " + COLUMN_KEYS[index] + " 列：" + asin);
        try {
          const res = await manager.fetchOne(asin, manager.config.general.site || "US");
          column.product = Object.assign({}, res, { loading: false, done: true, error: false });
          column.loading = false;
          renderColumn(column);
          updateStatusText("竞品 " + COLUMN_KEYS[index] + " 查询完成");
        } catch (err) {
          column.product = { asin, loading: false, error: true, data: {}, source: null };
          column.loading = false;
          renderColumn(column);
          updateStatusText("竞品 " + COLUMN_KEYS[index] + " 查询失败");
        }
      }

      function resetColumn(index) {
        const column = columns[index];
        column.asin = DEFAULT_ASINS[index] || "";
        column.product = null;
        column.loading = false;
        const input = document.getElementById("col-input-" + index);
        if (input) input.value = column.asin;
        renderColumn(column);
        updateStatusText("已重置竞品 " + COLUMN_KEYS[index] + " 列");
      }

      function updateStatusText(text) {
        document.getElementById("statusAsins").textContent = text;
      }

      /* 事件委托：6 列独立查询/重置/折叠 */
      document.getElementById("competitorGrid").addEventListener("click", (e) => {
        const q = e.target.closest("[data-col-query]");
        if (q) { queryColumn(Number(q.dataset.colQuery)); return; }
        const r = e.target.closest("[data-col-reset]");
        if (r) { resetColumn(Number(r.dataset.colReset)); return; }
        const retry = e.target.closest("[data-col-retry]");
        if (retry) { queryColumn(Number(retry.dataset.colRetry)); return; }
      });
      document.getElementById("competitorGrid").addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const input = e.target.closest("[id^='col-input-']");
          if (input) {
            const idx = Number(input.id.replace("col-input-", ""));
            queryColumn(idx);
          }
        }
      });

      function initColumns() {
        const grid = document.getElementById("competitorGrid");
        grid.innerHTML = "";
        columns.length = 0;
        for (let i = 0; i < COL_COUNT; i++) buildColumnShell(i);
        /* 预置 6 列模拟样例：本地直接打开即可预览完整并排效果 */
        DEFAULT_ASINS.forEach((asin, i) => {
          const column = columns[i];
          const cached = manager._getCache(asin.toUpperCase() + "|US|" + manager.fingerprint());
          if (cached) {
            column.product = Object.assign({}, cached, { loading: false, done: true });
            renderColumn(column);
          } else {
            queryColumn(i);
          }
        });
      }

      /* 顶部消息与配置保留 */
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
          DEFAULT_ASINS.forEach((asin, i) => queryColumn(i));
        });
        window.addEventListener("keepa-quota-update", (e) => {
          document.getElementById("keepaQuota").textContent = e.detail ?? "--";
        });
      }

      /* 配置面板数据源切换 */
      document.getElementById("sourceSelect").addEventListener("change", (e) => {
        manager.activeMain = e.target.value;
        manager.config.mainProvider = manager.activeMain;
        saveConfig(manager.config);
        showToast("已切换数据源：" + (manager.listProviders().find((p) => p.id === manager.activeMain)?.name || manager.activeMain));
        DEFAULT_ASINS.forEach((asin, i) => queryColumn(i));
      });
      document.getElementById("configModal").addEventListener("click", (e) => {
        if (e.target.id === "configModal") closeConfig();
      });

      /* MCP 兼容入口：外部注入单条竞品数据后渲染对应列 */
      window.mcpImport = (payload) => {
        if (!payload) return;
        const items = Array.isArray(payload) ? payload : (payload.raw || payload.products || []);
        items.forEach((item) => {
          const asin = String(item.asin || item.ASIN || "").toUpperCase();
          const col = columns.find((c) => c.asin.toUpperCase() === asin);
          if (!col) return;
          const product = { asin, matched: true, done: true, loading: false, source: "MCP", data: {} };
          product.data.basicInfo = {
            brand: item["品牌"] || item.brand || "", title: item["标题"] || item.title || "",
            url: item["链接"] || item.url || ("https://www.amazon.com/dp/" + asin),
            price: item["售价"] || item.price || null, imageUrl: item["图片"] || item.imageUrl || "",
            category: null, subcategory: null, rating: item["评分"] || null, reviewCount: item["评论数"] || null,
          };
          product.data.salesData = {
            sales30d: item["30天销量(畅销变体)"] || null, monthlySales: item["历史月销"] || null,
            bsrCategory: null, bsrSubcategory: null,
          };
          product.data.keepaData = { priceTrend: item["Keepa趋势"] ? [item["Keepa趋势"]] : null };
          product.data.reviewsData = {
            summary: item["AI评论分析"] || "", sellingPoints: item["产品卖点"] || "",
            positiveReviews: item["好评点"] || "", negativeReviews: item["差评点"] || "",
            improvementPoints: item["待改善点"] || "", targetAudience: item["使用人群"] || "",
            useScenarios: item["使用场景"] || "", optimizationDirection: item["优化方向"] || "",
          };
          product.data.specs = {
            variants: item["变体"] || null, productParams: item["产品参数信息"] || "",
            packageInfo: item["包装尺寸及重量"] || "",
          };
          col.product = product;
          renderColumn(col);
        });
      };
      window.mcpCompetitorAdapter = {
        setRawData: (list) => window.mcpImport(list),
        setAnalysis: (list) => window.mcpImport(list),
        render: renderAllColumns,
      };

      function init() {
        initSourceSelect();
        initConfigModal();
        initColumns();
        updateSourceStatus();
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
