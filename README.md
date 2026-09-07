# 亚马逊竞品自动化分析系统

纯前端单文件应用，支持六竞品并排对比，可接入多个数据源（西柚 MCP、Sorftime MCP、Sif MCP、LingXing MCP、VOC、本地 Excel/评论数据）。

## 本地运行

```bash
# 方式1：Node 代理（支持真实 MCP 数据源）
node server/local-server.js
# 浏览器打开 http://127.0.0.1:3000

# 方式2：局域网访问
node server/lan-server.js
# 浏览器打开 http://<你的局域网IP>:3002

# 方式3：纯静态预览（不接 MCP）
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
| **amazon-reviews-skill** | 全量评论抓取（Show more，目标 300） | 同级目录产物，经 `/api/local/reviews` 自动合并 |

## 评论数据怎么进页面

系统里消费评论的主路径是 **`LocalProvider.getReviewsData`** → `GET /api/local/reviews?asin=`，响应形状：

```json
{ "reviews": [ { "asin", "title", "content", "rating", "date", "review_id", "author" } ], "matchedFiles": [] }
```

前端再经 `normalizeReviewRows` / `analyzeReviewsToFields` 填到列上的 `reviewsData`（好评/差评/卖点/`rawReviews`）。

同级目录 `../amazon-reviews-skill/data/reviews_{ASIN}_{site}.json` 会被 Node 桥 **优先合并**进上述接口（字段已映射，无需改前端）。

配置面板新增 **「评论抓取(Skill)」**：可开关自动入队、账号、目标条数。新 ASIN 无本地 JSON 时，查询评论会 `POST /api/reviews/enqueue` 并后台拉起 Chrome Worker（需先 login）；完成后再次查询即可。

```powershell
# 1) 账号登录（首次）
cd ..\amazon-reviews-skill
python -m amazon_reviews.cli login --account test-us-2 --site com --channel chrome

# 2) 开竞品分析（完整后端）
cd ..\amz-competitor-analysis
node .local_static_server.js
# http://127.0.0.1:3000 → 数据源配置 → 评论抓取(Skill)
```

## 部署

纯静态部分可直接上传到 Netlify、Vercel、GitHub Pages、demogo.cn 等静态托管。部署说明见 `部署说明.md`。

注意：`api/mcp/*` 代理路由只有本地 Node 服务提供，静态托管环境无法使用；接入真实数据源需自行部署 Node 代理。
