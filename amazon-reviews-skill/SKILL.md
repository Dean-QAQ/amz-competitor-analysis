---
name: amazon-reviews
description: >-
  拉取亚马逊商品评论（登录态 + Show 10 more，目标 300 条/ASIN，任务队列可融入系统）。
  Use when 用户要爬/拉 Amazon reviews、ASIN 评论、See more reviews、评论软封 unusual activity、
  enqueue/worker 任务队列、或运行 amazon-reviews-skill。
---

# Amazon Reviews Skill

## 何时使用

- 按 ASIN 拉商品评论（目标 300，不足则有多少拿多少）
- 需要登录态 / 账号池 / 多站点（`com` 等）
- 排查评论软封（unusual activity）
- 把采集能力接入宿主系统（入队 + Worker）

## 项目路径

工作区：`amazon-reviews-skill/`

## 标准流程（人工 CLI）

1. 确认 `accounts/pool.json`；测试只用一个 `enabled` 账号。
2. 登录：
   ```powershell
   python -m amazon_reviews.cli login --account test-us-2 --site com --channel chrome
   ```
3. 拉取：
   ```powershell
   $env:PYTHONUNBUFFERED = "1"
   python -m amazon_reviews.cli fetch --asin <ASIN> --site com --account test-us-2 --target 300 --resume --strategy show_more --pace cautious --max-pace normal
   ```

## 系统接入（推荐）

```powershell
python -m amazon_reviews.cli enqueue --asin <ASIN> --account test-us-2 --target 300
python -m amazon_reviews.cli worker
python -m amazon_reviews.cli task --id <task_id>
```

```python
from amazon_reviews import ReviewsService
svc = ReviewsService.from_package_root()
task = svc.enqueue("B0...", account_id="test-us-2")
outcome = svc.run_next()  # exit_code 0/1/2
```

状态机：`queued` → `running` → `done` | `needs_login` | `softbanned` | `captcha` | `failed`  
产物：`data/reviews_{ASIN}_{site}.json`；任务：`tasks/{id}.json`

## 实现约定

- 主路径：Chrome CDP + **Show 10 more**（禁止依赖 `pageNumber`）
- 默认 `--max-pace normal`
- 条数 = 去重 `review_id`（`unique_review_ids`）
- 融入系统用 Windows 有头 Worker，登录失效走人工 `login` 后自动重新入队

## 验收

- login → fetch PoC
- enqueue → worker → `done` + JSON
- softban/needs_login → 退出码 2 + 任务状态对应
