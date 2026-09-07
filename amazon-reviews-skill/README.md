# Amazon Reviews Skill

登录态（持久 Chrome / CDP）+ 多过滤器矩阵拉取亚马逊商品评论。目标 **300 条/ASIN**，不足则有多少拿多少；支持多站点与账号池（测试用 1 个号）。

纯 HTTP + cookie 易撞 EdgeX；默认用本机 Chrome 持久配置抓取。

## 架构

```text
持久 Chrome 用户目录 ~/.amazon-reviews-profiles/{account}.{site}/
        ↓
打开 /product-reviews/{ASIN}/（pageNumber 无效，固定第 1 屏）
        ↓
反复点击「Show 10 more reviews」追加 DOM 评论 → review_id 去重
        ↓
不够再换排序/星级各做一轮 Show-more；hybrid 才用关键词切片补
        ↓
每有新增即 checkpoint 写入 JSON（进程被杀也不丢）
```

### 防验证码限速（推荐）

| 档位 | 页间隔（约） | 会话冷却 | 说明 |
|------|--------------|----------|------|
| cautious | 7–14s | 约每 8 页 45–90s | **默认起步** |
| normal | 4–8s | 稍短 | 长干净 streak 后可升到此；`--max-pace` 默认上限 |
| relaxed | 更快 | 更短 | **易触发 captcha**，仅显式 `--max-pace relaxed` |

推荐命令：

```powershell
$env:PYTHONUNBUFFERED = "1"
python -m amazon_reviews.cli fetch --asin B0CQX8B5K9 --site com --account test-us-2 `
  --target 300 --resume --strategy show_more --pace cautious --max-pace normal
```

`--strategy`：`show_more`（默认，点 Show 10 more）| `hybrid`（不够再筛过滤片）| `matrix`（旧路径，不推荐）。  
**不要依赖 URL 的 `pageNumber`**——多数会话下无效，累加过大还会被踢回首页。

## 安装

```powershell
cd amazon-reviews-skill
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy accounts\pool.example.json accounts\pool.json
```

## 使用

### 1. 登录（持久 Chrome 配置）

```powershell
python -m amazon_reviews.cli login --account test-us-2 --site com --channel chrome
```

配置目录在 ASCII 路径 `C:\Users\EDY\.amazon-reviews-profiles\`（中文项目路径会导致 Chrome 忽略 `user-data-dir`）。须看到账号 **Hello**，不能仅靠 cookie。

### 2. 拉评论 / 续跑

```powershell
python -m amazon_reviews.cli fetch --asin B0DB142C6Y --site com --account test-us-2 --target 300 --resume --pace cautious --max-pace normal
```

掉登录时重新 `login`，再 `--resume`（进度不丢）。出现 captcha 时先冷却/在同配置里手动过验证，再 `--resume`。

### 3. 系统接入：入队 + Worker（推荐）

任务状态：`queued` → `running` → `done` | `needs_login` | `softbanned` | `captcha` | `failed`

```powershell
# 业务系统只入队
python -m amazon_reviews.cli enqueue --asin B0CQX8B5K9 --site com --account test-us-2 --target 300

# Windows 抓取机消费队列（一次一个）
python -m amazon_reviews.cli worker

# 查状态
python -m amazon_reviews.cli tasks --status queued
python -m amazon_reviews.cli task --id <task_id>
```

Python API（宿主系统直接 import）：

```python
from amazon_reviews import ReviewsService

svc = ReviewsService.from_package_root()
task = svc.enqueue("B0CQX8B5K9", account_id="test-us-2", target=300)
outcome = svc.run_task(task.id)   # 或 svc.run_next()
# outcome.exit_code: 0=done, 2=needs_login/softbanned/captcha, 1=failed
# outcome.task.status / result JSON: data/reviews_{ASIN}_{site}.json
```

`needs_login` 时：人工 `login` 后任务会自动回到 `queued`，再 `worker`。

### 4. 性能与事件日志

每次 fetch 写入：

- `logs/fetch_{ASIN}_{site}_{run_id}.jsonl` — 逐页/冷却/风控事件
- `logs/fetch_{ASIN}_{site}_{run_id}_summary.json` — 耗时、reviews/hour、avg page ms、等待合计、risk 列表
- `tasks/{task_id}.json` — 队列任务状态机快照

### 5. 其它

```powershell
python -m amazon_reviews.cli sites
python -m amazon_reviews.cli pool
```

## 站点 code

`com` `co.uk` `de` `fr` `it` `es` `ca` `com.au` `co.jp` `in` `com.mx`

每个站点需要各自的登录态（cookie 不互通）。

## 软封 / 登录墙 / 验证码

| 信号 | 行为 |
|------|------|
| unusual activity | 停任务，账号 → `softbanned`，退出码 2 |
| 登录墙 | 停任务，账号 → `needs_login`，`--resume` 前先 login |
| captcha | 长 backoff 后最多再试 1 次；仍失败则停，保持 `--max-pace normal` |

## 与 amz-competitor-analysis 对接

竞品分析页通过 **`GET /api/local/reviews?asin=`** 读评论（`LocalProvider`）。  
将本 skill 与 `amz-competitor-analysis` 放在同级目录后，Node 桥会自动合并：

`amazon-reviews-skill/data/reviews_{ASIN}_{site}.json` → 上述接口的 `{ reviews: [...] }`

无需改前端字段；先 `fetch`/`worker` 出 JSON，再在页面查询该 ASIN。

## 测试

```powershell
pip install pytest
pytest -q
```

## 注意

- 主路径是 **Show 10 more**；`pageNumber` 无效。`hybrid` 才会用筛选切片补量。
- 融入系统请用 **Windows 有头 Chrome Worker**，不要假设 Linux 无头容器能稳定跑。
- 勿把 profile 建在含中文的项目路径下。
- 仅用于你有权访问的账号会话与合规场景。
