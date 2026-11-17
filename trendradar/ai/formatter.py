# coding=utf-8
"""
AI 分析结果格式化模块

将 AI 分析结果格式化为各推送渠道的样式。
"""

import html as html_lib
import re
from .analyzer import AIAnalysisResult


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符，防止 XSS 攻击。"""
    return html_lib.escape(text) if text else ""


def _format_list_content(text: str) -> str:
    """规范化 AI 列表文本和段落间距。"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'(\d+\.)\s*【([^】]+)】([:：]?)', r'\1 \2：', text)
    result = re.sub(r'(\d+)\.([^ \d])', r'\1. \2', text)
    result = re.sub(r'(?<=[^\n])\s+(\d+\.)', r'\n\1', result)
    result = re.sub(r'(?<=[^\n])(\d+\.\*\*)', r'\n\1', result)
    result = re.sub(r'([：:;,。；，])\s*(\d+\.)', r'\1\n\2', result)
    result = re.sub(r'([。！？；，、])\s*([a-zA-Z0-9\u4e00-\u9fa5]+(方面|领域)[:：])', r'\1\n\2', result)
    result = re.sub(r'(?<=\S)\n*(【[^】]+】)', r'\n\n\1', result)
    result = re.sub(r'(【[^】]+】)\n+([:：])', r'\1\2', result)
    result = re.sub(r'(【[^】]+】[:：]?)[ \t]*(?=[^\s:：])', r'\1\n', result)
    return re.sub(r'(?<![:：】])\n(\d+\.)', r'\n\n\1', result)


def _format_standalone_summaries(summaries: dict) -> str:
    """格式化独立展示区摘要。"""
    if not summaries:
        return ""
    return "\n\n".join(
        f"[{source_name}]:\n{summary}"
        for source_name, summary in summaries.items()
        if summary
    )


def _append_markdown_sections(result: AIAnalysisResult, heading_prefix: str = "**") -> list:
    """生成各通知渠道共用的分析区块。"""
    sections = [
        ("核心判断", result.core_trends),
        ("主要分歧", result.sentiment_controversy),
        ("国内影响信号", result.signals),
        ("新闻来源增量", result.rss_insights),
        ("后续观察", result.outlook_strategy),
        ("股票候选观察", result.stock_watchlist),
    ]
    lines = ["✨ 国内政策与市场影响简报", ""]
    for title, content in sections:
        if content:
            if heading_prefix == "#### ":
                lines.extend([f"#### {title}", _format_list_content(content), ""])
            else:
                lines.extend([f"**{title}**", _format_list_content(content), ""])
    summaries_text = _format_standalone_summaries(result.standalone_summaries)
    if summaries_text:
        lines.extend(["**来源速览**", summaries_text])
    return lines


def render_ai_analysis_markdown(result: AIAnalysisResult) -> str:
    """渲染为通用 Markdown 格式。"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"
    return "\n".join(_append_markdown_sections(result))


def render_ai_analysis_feishu(result: AIAnalysisResult) -> str:
    """渲染为飞书 Markdown 格式。"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"
    return "\n".join(_append_markdown_sections(result))


def render_ai_analysis_dingtalk(result: AIAnalysisResult) -> str:
    """渲染为钉钉 Markdown 格式。"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"
    return "\n".join(_append_markdown_sections(result, "#### "))


def _render_html_block(title: str, text: str, *, highlight: bool = False) -> str:
    """生成内联样式 HTML 卡片，兼容常见邮件客户端。"""
    if not text:
        return ""
    content = _escape_html(_format_list_content(text)).replace("\n", "<br>")
    background = "#fffaf0" if highlight else "#ffffff"
    border = "#e7c98b" if highlight else "#e5e7eb"
    title_color = "#8a5a12" if highlight else "#334155"
    return (
        '<div style="margin:0 0 10px;padding:12px 14px;'
        f'background:{background};border:1px solid {border};border-radius:8px;">'
        f'<div style="margin:0 0 6px;color:{title_color};font-size:14px;'
        f'font-weight:700;">{_escape_html(title)}</div>'
        f'<div style="color:#334155;font-size:13px;line-height:1.55;">{content}</div>'
        '</div>'
    )


def render_ai_analysis_html(result: AIAnalysisResult) -> str:
    """渲染为简洁 HTML 邮件内容。"""
    return render_ai_analysis_html_rich(result)


def render_ai_analysis_plain(result: AIAnalysisResult) -> str:
    """渲染为纯文本格式。"""
    if not result.success:
        return f"AI 分析失败: {result.error}"
    lines = ["【国内政策与市场影响简报】", ""]
    sections = [
        ("今日结论", result.core_trends),
        ("主要分歧", result.sentiment_controversy),
        ("国内影响信号", result.signals),
        ("来源增量", result.rss_insights),
        ("后续观察", result.outlook_strategy),
        ("股票候选观察", result.stock_watchlist),
    ]
    for title, content in sections:
        if content:
            lines.extend([f"[{title}]", _format_list_content(content), ""])
    summaries_text = _format_standalone_summaries(result.standalone_summaries)
    if summaries_text:
        lines.extend(["[来源速览]", summaries_text])
    return "\n".join(lines)


def get_ai_analysis_renderer(channel: str):
    """根据渠道获取对应的渲染函数。"""
    renderers = {
        "feishu": render_ai_analysis_feishu,
        "dingtalk": render_ai_analysis_dingtalk,
        "wework": render_ai_analysis_markdown,
        "telegram": render_ai_analysis_markdown,
        "email": render_ai_analysis_html_rich,
        "ntfy": render_ai_analysis_markdown,
        "bark": render_ai_analysis_plain,
        "slack": render_ai_analysis_markdown,
    }
    return renderers.get(channel, render_ai_analysis_markdown)


def render_ai_analysis_html_rich(result: AIAnalysisResult) -> str:
    """渲染紧凑财经简报卡片 HTML。"""
    if not result:
        return ""
    if not result.success:
        return (
            '<div style="margin:0 0 10px;padding:12px;border:1px solid #fecaca;'
            'background:#fef2f2;border-radius:8px;color:#991b1b;">'
            f'AI 分析失败：{_escape_html(result.error or "未知错误")}</div>'
        )

    ai_html = (
        '<div style="margin:0 0 18px;padding:16px;background:#f8fafc;'
        'border:1px solid #dbe3ec;border-radius:10px;">'
        '<div style="margin:0 0 12px;color:#172b4d;font-size:18px;'
        'font-weight:700;">国内政策与市场影响简报</div>'
    )
    blocks = [
        ("今日结论", result.core_trends, True),
        ("主要分歧", result.sentiment_controversy, False),
        ("国内影响信号", result.signals, False),
        ("来源增量", result.rss_insights, False),
        ("后续观察", result.outlook_strategy, False),
        ("股票候选观察", result.stock_watchlist, True),
    ]
    for title, text, highlight in blocks:
        ai_html += _render_html_block(title, text, highlight=highlight)

    summaries = _format_standalone_summaries(result.standalone_summaries)
    if summaries:
        content = _escape_html(summaries).replace("\n", "<br>")
        ai_html += (
            '<div style="margin-top:8px;color:#64748b;font-size:11px;line-height:1.4;">'
            f'来源速览：{content}</div>'
        )
    ai_html += "</div>"
    return ai_html

# End of file
