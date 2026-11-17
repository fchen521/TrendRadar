# Official RSS source notes and analysis boundaries

The RSS entries in `config/config.yaml` are labeled by institution and intended use:

- `cn_policy_*`: China policy and monetary policy. Public stable RSS availability from Chinese government sites is limited; do not treat secondary discovery sources as official policy text.
- `intl_*`: central banks, international bodies, regulators, and official statistics.
- `impact_cn_*`: international energy or macro context that may help analyze transmission to China. An international release alone is not proof of a domestic impact.

## Configured public feeds

| Config ID | Institution | Feed URL | Purpose |
|---|---|---|---|
| `cn_policy_pbc` | People's Bank of China | `http://www.pbc.gov.cn/en/3688110/index.rss` | Domestic monetary policy and PBOC releases (English) |
| `intl_us_federal_reserve` | Federal Reserve | `https://www.federalreserve.gov/feeds/press_all.xml` | US monetary policy and announcements |
| `intl_eu_ecb` | European Central Bank | `https://www.ecb.europa.eu/rss/press.html` | Euro area policy and announcements |
| `intl_uk_boe` | Bank of England | `https://www.bankofengland.co.uk/rss/news` | UK central-bank news |
| `intl_jp_boj` | Bank of Japan | `https://www.boj.or.jp/en/rss/whatsnew.xml` | BOJ announcements (English) |
| `intl_global_bis` | Bank for International Settlements | `https://www.bis.org/rss.xml` | International finance and regulatory cooperation |
| `intl_global_oecd` | OECD | `https://www.oecd.org/rss/generalrss.xml` | International economic and policy publications |
| `intl_us_sec` | US Securities and Exchange Commission | `https://www.sec.gov/news/pressreleases.rss` | US securities-regulator releases |
| `impact_cn_energy_eia` | US Energy Information Administration | `https://www.eia.gov/rss/todayinenergy.xml` | Energy data and analysis; potential cost-transmission context |
| `intl_us_bls` | US Bureau of Labor Statistics | `https://www.bls.gov/feed/news_release/rss.xml` | US employment and inflation statistics |
| `intl_us_bea` | US Bureau of Economic Analysis | `https://www.bea.gov/rss/news_releases.xml` | US national accounts and international economic statistics |

Feeds can change, rate-limit, or become temporarily unavailable. Check crawler logs after deployment and verify failed endpoints on the institution's official website before changing a URL. Do not label news aggregators, media commentary, or secondary reports as official policy. Do not guess RSS URLs for Chinese departments when a stable public feed has not been confirmed.

The RSS schema in this project has no category field, so the category is currently represented in feed IDs and display names. Policy analysis prompt: `config/ai_policy_analysis_prompt.txt`.

## Stock candidate watchlist

The policy analysis prompt includes a `stock_watchlist` field for a maximum of three **news-linked research candidates**, not buy recommendations. It must not invent securities, tickers, or a company-benefit link; it may return fewer than three or no candidates when the supplied evidence is insufficient. TrendRadar currently does not supply verified stock master data, real-time prices, valuation, or financial statements to this analysis, so those dimensions must be explicitly marked as unevaluated. See `docs/stock-watchlist.md`.
