# coding=utf-8
"""
AI 分析器：将热点与 RSS 输入交给 LiteLLM，并解析结构化简报。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from trendradar.ai.client import AIClient


@dataclass
class AIAnalysisResult:
    """AI 分析结果；文本板块均使用简体中文。"""
    core_trends: str = ""
    sentiment_controversy: str = ""
    signals: str = ""
    rss_insights: str = ""
    outlook_strategy: str = ""
    stock_watchlist: str = ""
    standalone_summaries: Dict[str, str] = field(default_factory=dict)
    raw_response: str = ""
    success: bool = False
    error: str = ""
    total_news: int = 0
    analyzed_news: int = 0
    max_news_limit: int = 0
    hotlist_count: int = 0
    rss_count: int = 0
    ai_mode: str = ""


class AIAnalyzer:
    """使用 AI 对新闻热点及其国内影响进行分析。"""

    TEXT_FIELDS = (
        "core_trends",
        "sentiment_controversy",
        "signals",
        "rss_insights",
        "outlook_strategy",
        "stock_watchlist",
    )

    def __init__(
        self,
        ai_config: Dict[str, Any],
        analysis_config: Dict[str, Any],
        get_time_func: Callable,
        debug: bool = False,
    ):
        self.ai_config = ai_config
        self.analysis_config = analysis_config
        self.get_time_func = get_time_func
        self.debug = debug
        self.client = AIClient(ai_config)

        valid, error = self.client.validate_config()
        if not valid:
            print(f"[AI] 配置警告: {error}")

        self.max_news = analysis_config.get("MAX_NEWS_FOR_ANALYSIS", 50)
        self.include_rss = analysis_config.get("INCLUDE_RSS", True)
        self.include_rank_timeline = analysis_config.get("INCLUDE_RANK_TIMELINE", False)
        self.include_standalone = analysis_config.get("INCLUDE_STANDALONE", False)
        self.language = analysis_config.get("LANGUAGE", "Chinese")
        self.system_prompt, self.user_prompt_template = self._load_prompt_template(
            analysis_config.get("PROMPT_FILE", "ai_analysis_prompt.txt")
        )

    def _load_prompt_template(self, prompt_file: str) -> tuple:
        """加载并拆分 [system] / [user] 提示词。"""
        prompt_path = Path(__file__).parent.parent.parent / "config" / prompt_file
        if not prompt_path.exists():
            message = f"[AI] 提示词文件不存在: {prompt_path}"
            print(message)
            return "", ""

        content = prompt_path.read_text(encoding="utf-8")
        if "[system]" in content and "[user]" in content:
            before_user, user_part = content.split("[user]", 1)
            system_prompt = before_user.split("[system]", 1)[1].strip()
            return system_prompt, user_part.strip()
        return "", content

    def analyze(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
        report_mode: str = "daily",
        report_type: str = "当日汇总",
        platforms: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        standalone_data: Optional[Dict] = None,
    ) -> AIAnalysisResult:
        """执行分析并返回各字段完整的结构化结果。"""
        model = self.ai_config.get("MODEL", "unknown")
        api_key = self.client.api_key or ""
        api_base = self.ai_config.get("API_BASE", "")
        masked_key = f"{api_key[:5]}******" if len(api_key) >= 5 else "******"
        print(f"[AI] 模型: {model.replace('/', '/\\u200b') if model else 'unknown'}")
        print(f"[AI] Key : {masked_key}")
        if api_base:
            print("[AI] 接口: 存在自定义 API 端点")
        print(
            f"[AI] 参数: timeout={self.ai_config.get('TIMEOUT', 120)}, "
            f"max_tokens={self.ai_config.get('MAX_TOKENS', 5000)}"
        )

        if not self.client.api_key:
            return AIAnalysisResult(
                success=False,
                error="未配置 AI API Key，请在 config.yaml 或环境变量 AI_API_KEY 中设置",
            )

        news_content, rss_content, hotlist_total, rss_total, analyzed_count = (
            self._prepare_news_content(stats, rss_stats)
        )
        if not news_content and not rss_content:
            return AIAnalysisResult(
                success=False,
                error="没有可分析的新闻内容",
                total_news=hotlist_total + rss_total,
                hotlist_count=hotlist_total,
                rss_count=rss_total,
                analyzed_news=0,
                max_news_limit=self.max_news,
            )

        keywords = keywords or [s.get("word", "") for s in (stats or []) if s.get("word")]
        current_time = self.get_time_func().strftime("%Y-%m-%d %H:%M:%S")
        replacements = {
            "{report_mode}": report_mode,
            "{report_type}": report_type,
            "{current_time}": current_time,
            "{news_count}": str(hotlist_total),
            "{rss_count}": str(rss_total),
            "{platforms}": ", ".join(platforms) if platforms else "多平台",
            "{keywords}": ", ".join(keywords[:20]) if keywords else "无",
            "{news_content}": news_content,
            "{rss_content}": rss_content,
            "{language}": self.language,
            "{standalone_content}": (
                self._prepare_standalone_content(standalone_data)
                if self.include_standalone and standalone_data else ""
            ),
        }
        user_prompt = self.user_prompt_template
        for placeholder, value in replacements.items():
            user_prompt = user_prompt.replace(placeholder, value)

        if self.debug:
            print("\n" + "=" * 80)
            print("[AI 调试] 发送给 AI 的完整提示词")
            print("=" * 80)
            if self.system_prompt:
                print("\n--- System Prompt ---\n" + self.system_prompt)
            print("\n--- User Prompt ---\n" + user_prompt)
            print("=" * 80 + "\n")

        try:
            result = self._parse_response(self._call_ai(user_prompt))
            if not self.include_rss:
                result.rss_insights = ""
            if not self.include_standalone:
                result.standalone_summaries = {}
            result.total_news = hotlist_total + rss_total
            result.hotlist_count = hotlist_total
            result.rss_count = rss_total
            result.analyzed_news = analyzed_count
            result.max_news_limit = self.max_news
            return result
        except Exception as exc:
            message = str(exc)
            if len(message) > 200:
                message = message[:200] + "..."
            return AIAnalysisResult(
                success=False,
                error=f"AI 分析失败 ({type(exc).__name__}): {message}",
            )

    def _prepare_news_content(
        self, stats: List[Dict], rss_stats: Optional[List[Dict]] = None
    ) -> tuple:
        """准备热榜和 RSS 文本，遵守 MAX_NEWS_FOR_ANALYSIS 上限。"""
        news_lines: List[str] = []
        rss_lines: List[str] = []
        news_count = 0
        rss_count = 0
        stats = stats or []
        rss_stats = rss_stats or []
        hotlist_total = sum(len(s.get("titles", [])) for s in stats)
        rss_total = sum(len(s.get("titles", [])) for s in rss_stats)

        for stat in stats:
            if news_count >= self.max_news:
                break
            word = stat.get("word", "")
            titles = stat.get("titles", [])
            if word and titles:
                news_lines.append(f"\n**{word}** ({len(titles)}条)")
            for item in titles:
                if news_count >= self.max_news:
                    break
                if not isinstance(item, dict) or not item.get("title"):
                    continue
                source = item.get("source_name", item.get("source", ""))
                line = f"- [{source}] {item['title']}" if source else f"- {item['title']}"
                ranks = item.get("ranks") or []
                rank_text = "-"
                if ranks:
                    low, high = min(ranks), max(ranks)
                    rank_text = str(low) if low == high else f"{low}-{high}"
                time_text = self._format_time_range(
                    item.get("first_time", ""), item.get("last_time", "")
                )
                line += f" | 排名:{rank_text} | 时间:{time_text} | 出现:{item.get('count', 1)}次"
                if self.include_rank_timeline:
                    line += f" | 轨迹:{self._format_rank_timeline(item.get('rank_timeline', []))}"
                news_lines.append(line)
                news_count += 1

        remaining = max(0, self.max_news - news_count)
        if self.include_rss and remaining:
            for stat in rss_stats:
                if rss_count >= remaining:
                    break
                word = stat.get("word", "")
                titles = stat.get("titles", [])
                if word and titles:
                    rss_lines.append(f"\n**{word}** ({len(titles)}条)")
                for item in titles:
                    if rss_count >= remaining:
                        break
                    if not isinstance(item, dict) or not item.get("title"):
                        continue
                    source = item.get("source_name", item.get("feed_name", ""))
                    line = f"- [{source}] {item['title']}" if source else f"- {item['title']}"
                    if item.get("time_display"):
                        line += f" | {item['time_display']}"
                    rss_lines.append(line)
                    rss_count += 1

        return (
            "\n".join(news_lines),
            "\n".join(rss_lines),
            hotlist_total,
            rss_total,
            news_count + rss_count,
        )

    def _call_ai(self, user_prompt: str) -> str:
        """调用 AI API（使用 LiteLLM）。"""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return self.client.chat(messages)

    def _format_time_range(self, first_time: str, last_time: str) -> str:
        """格式化时间范围（仅保留时分）。"""
        def extract_time(value: str) -> str:
            if not value:
                return "-"
            if " " in value:
                parts = value.split(" ")
                if len(parts) >= 2 and ":" in parts[1]:
                    return parts[1][:5]
            if ":" in value:
                return value[:5]
            result = value[:5] if len(value) >= 5 else value
            return result.replace("-", ":") if len(result) == 5 and result[2] == "-" else result

        first, last = extract_time(first_time), extract_time(last_time)
        return first if first == last or last == "-" else f"{first}~{last}"

    def _format_rank_timeline(self, rank_timeline: List[Dict]) -> str:
        """格式化排名时间线。"""
        if not rank_timeline:
            return "-"
        parts = []
        for item in rank_timeline:
            time_str = item.get("time", "")
            if len(time_str) == 5 and time_str[2] == "-":
                time_str = time_str.replace("-", ":")
            rank = item.get("rank")
            parts.append(f"{rank if rank is not None else 0}({time_str})")
        return "→".join(parts)

    def _prepare_standalone_content(self, standalone_data: Dict) -> str:
        """将独立展示区数据转为提示词文本。"""
        lines = []
        for platform in standalone_data.get("platforms", []):
            name = platform.get("name", platform.get("id", ""))
            items = platform.get("items", [])
            if not items:
                continue
            lines.append(f"### [{name}]")
            for item in items:
                title = item.get("title", "")
                if not title:
                    continue
                line = f"- {title}"
                ranks = item.get("ranks") or []
                if ranks:
                    low, high = min(ranks), max(ranks)
                    line += f" | 排名:{low if low == high else f'{low}-{high}'}"
                if item.get("first_time"):
                    line += " | 时间:" + self._format_time_range(
                        item.get("first_time", ""), item.get("last_time", "")
                    )
                if item.get("count", 1) > 1:
                    line += f" | 出现:{item['count']}次"
                if self.include_rank_timeline and item.get("rank_timeline"):
                    line += " | 轨迹:" + self._format_rank_timeline(item["rank_timeline"])
                lines.append(line)
            lines.append("")

        for feed in standalone_data.get("rss_feeds", []):
            name = feed.get("name", feed.get("id", ""))
            items = feed.get("items", [])
            if not items:
                continue
            lines.append(f"### [{name}]")
            for item in items:
                title = item.get("title", "")
                if title:
                    line = f"- {title}"
                    if item.get("published_at"):
                        line += f" | {item['published_at']}"
                    lines.append(line)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _extract_json_object(response: str) -> str:
        """提取完整 JSON 对象，兼容 Markdown code fence 和前后说明文字。"""
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("响应中没有完整 JSON 对象；可能被模型截断")
        return text[start:end + 1]

    def _parse_response(self, response: str) -> AIAnalysisResult:
        """严格解析 AI JSON；畸形或截断响应标记失败，不伪装成完整简报。"""
        result = AIAnalysisResult(raw_response=response or "")
        if not response or not response.strip():
            result.error = "AI 返回空响应"
            return result

        try:
            data = json.loads(self._extract_json_object(response))
            if not isinstance(data, dict):
                raise ValueError("AI JSON 顶层必须是对象")

            defaults = {
                "core_trends": "暂无显著国内政策或热点主线。",
                "sentiment_controversy": "暂无显著争议或分歧。",
                "signals": "暂无足够证据判断弱信号。",
                "rss_insights": "暂无显著 RSS 增量。",
                "outlook_strategy": "暂无足够证据形成可靠情景推演。",
                "stock_watchlist": "暂无足够证据形成股票候选。非投资建议；未评估实时行情、估值及财务数据。",
            }
            for field_name, default in defaults.items():
                value = data.get(field_name, default)
                if value is None or value == "":
                    value = default
                if not isinstance(value, str):
                    raise ValueError(f"AI 字段 {field_name} 必须是字符串")
                setattr(result, field_name, value.strip())

            summaries = data.get("standalone_summaries", {})
            if summaries is None:
                summaries = {}
            if not isinstance(summaries, dict):
                raise ValueError("AI 字段 standalone_summaries 必须是对象")
            result.standalone_summaries = {
                str(key): str(value) for key, value in summaries.items()
                if value is not None and str(value).strip()
            }
            result.success = True
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            result.success = False
            result.error = f"AI 响应不完整或格式无效: {exc}"
            print(f"[AI] {result.error}")

        return result

# End of file
