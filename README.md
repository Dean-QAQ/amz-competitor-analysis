# 亚马逊竞品自动化分析系统

纯前端单文件应用，支持六竞品并排对比，可接入多个数据源（西柚 MCP、Sorftime MCP、Sif MCP、LingXing MCP、VOC、本地 Excel/评论数据）。

## 本地运行

```bash
# 方式1：完整后端（推荐，含评论全量抓取）
node .local_static_server.js
# 浏览器打开 http://127.0.0.1:3000

# 方式2：Node 代理
node server/local-server.js
# 浏览器打开 http://127.0.0.1:3000

# 方式3：局域网访问
node server/lan-server.js
# 浏览器打开 http://<你的局域网IP>:3002

# 方式4：纯静态预览（不接 MCP / 不全量抓评论）
npx serve .
```

## 数据源配置

1. 复制 `.env.example` 为 `.env.local`，填入你的真实 Key。
2. 重启 Node 服务。
3. 页面右上角「⚙️ 数据源配置」可切换数据源顺序、站点、并发数等。

未配置的 Key 会自动跳过对应数据源，不会报错。缺失字段用下一个数据源补全，全部失败才显示「无数据」。

## 数据源清单

| 数据源 | 用途 | Key |
|---|---|---|
| 西柚 MCP | 基础信息、销量、BSR、变体 | `XIYOU_MCP_KEY` |
| Sorftime MCP | 商品详情、趋势 | `SORFTIME_MCP_URL` + `SORFTIME_MCP_AUTH` |
| Sif MCP | 基础信息、销量趋势、规格 | `SIF_MCP_KEY` |
| LingXing MCP | 预留入口 | `LINGXING_MCP_KEY` |
| VOC | 评论分析（接口） | 页面配置面板填 |
| 本地 Excel | 市场调研、评论导入 | 页面上传 |
| **amazon-reviews-skill** | 全量评论抓取（Show more，目标 300） | 本仓库内置目录 `amazon-reviews-skill/` |

## 评论全量抓取（内置 Skill）

本仓库已包含 `amazon-reviews-skill/`（登录态 Chrome + Show 10 more，目标约 300 条/ASIN）。

路径解析优先用仓库内目录；若你仍把 Skill 放在同级外部目录，也会自动回退识别。

```powershell
# 1) 安装 Python 依赖（首次）
cd amazon-reviews-skill
python -m pip install -r requirements.txt
python -m playwright install chromium
copy accounts\pool.example.json accounts\pool.json
# 按需编辑 pool.json 账号 id

# 2) 账号登录（首次 / 过期后）
python -m amazon_reviews.cli login --account test-us-1 --site com --channel chrome

# 3) 启动竞品分析
cd ..
node .local_static_server.js
# http://127.0.0.1:3000 → 数据源配置 → 评论抓取(Skill)
```

查询新 ASIN 时，若本地还没有足够评论 JSON，会自动 `POST /api/reviews/enqueue` 并拉起 Chrome Worker；页头「全量评论抓取进度」会轮询条数。抓完后再点一次查询即可刷新 AI 分析。

未安装/依赖缺失时，状态与入队接口会降级提示，系统仍可用本地评论与商品页零星评论，不会整站崩溃。

## 评论数据怎么进页面

系统里消费评论的主路径是 **`LocalProvider.getReviewsData`** → `GET /api/local/reviews?asin=`，响应形状：

```json
{ "reviews": [ { "asin", "title", "content", "rating", "date", "review_id", "author" } ], "matchedFiles": [] }
```

前端再经 `normalizeReviewRows` / `analyzeReviewsToFields` 填到列上的 `reviewsData`（好评/差评/卖点/`rawReviews`）。

`amazon-reviews-skill/data/reviews_{ASIN}_{site}.json` 会被 Node 桥 **优先合并**进上述接口（字段已映射，无需改前端）。

## 部署

纯静态部分可直接上传到 Netlify、Vercel、GitHub Pages、demogo.cn 等静态托管。部署说明见 `部署说明.md`。

注意：`api/mcp/*` 代理路由只有本地 Node 服务提供，静态托管环境无法使用；接入真实数据源需自行部署 Node 代理。全量评论抓取依赖本机 Chrome + Python，不适合纯静态托管。
