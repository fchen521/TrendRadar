# TrendRadar RSS 来源说明与边界

`config/config.yaml` 中的 RSS 列表按官方机构和用途标注：

- `cn_policy_*`：国内政策与货币政策。当前配置了中国人民银行公开的英文 RSS；中国官方部门的公开、稳定 RSS 地址较少，因此其余国内新闻平台仅用于发现线索，不能当作政策原文。
- `intl_*`：央行、国际清算银行、OECD、监管机构及官方统计发布。
- `impact_cn_*`：可作为国内传导分析输入的国际能源数据/解读来源。国际源不等于国内影响的直接证据。

## 已配置的官方��开订阅地址

| 配置 ID | 机构 | 地址 | 用途 |
|---|---|---|---|
| `cn_policy_pbc` | 中国人民银行 | `http://www.pbc.gov.cn/en/3688110/index.rss` | 国内货币政策与央行发布（英文页面） |
| `intl_us_federal_reserve` | 美国联邦储备委员会 | `https://www.federalreserve.gov/feeds/press_all.xml` | 美国货币政策与公告 |
| `intl_eu_ecb` | 欧洲中央银行 | `https://www.ecb.europa.eu/rss/press.html` | 欧元区政策与公告 |
| `intl_uk_boe` | 英格兰银行 | `https://www.bankofengland.co.uk/rss/news` | 英国央行新闻 |
| `intl_jp_boj` | 日本银行 | `https://www.boj.or.jp/en/rss/whatsnew.xml` | 日本央行英文公告 |
| `intl_global_bis` | 国际清算银行 | `https://www.bis.org/rss.xml` | 国际金融与监管合作 |
| `intl_global_oecd` | OECD | `https://www.oecd.org/rss/generalrss.xml` | 国际经济与政策发布 |
| `intl_us_sec` | 美国证券交易委员会 | `https://www.sec.gov/news/pressreleases.rss` | 美国证券监管发布 |
| `impact_cn_energy_eia` | 美国能源信息署 | `https://www.eia.gov/rss/todayinenergy.xml` | 能源数据与分析；用于监测潜在成本传导 |
| `intl_us_bls` | 美国劳工统计局 | `https://www.bls.gov/feed/news_release/rss.xml` | 美国就业、通胀等统计发布 |
| `intl_us_bea` | 美国经济分析局 | `https://www.bea.gov/rss/news_releases.xml` | 美国国民经济与国际收支统计 |

## 部署前检查

RSS 服务可能调整地址、限流或暂时不可用；部署后请检查运行日志中的 RSS 抓取结果。对于返回错误的源，先访问官网确认最新地址，再更新配置。不要把搜索聚合源、媒体评论或非官方转载标记为“官方政策”。若需中文国内政策原文，建议从国务院及相关部委官网查找其当前公开订阅/API；未确认稳定 RSS 前不要猜测 URL。

本项目 RSS 条目结构没有分类字段，因此分类目前写在 `id` 和 `name` 中。AI 分析提示词配置在 `config/ai_policy_analysis_prompt.txt`。
