# coding=utf-8
"""
AI 分析结果格式化模块

为通知渠道提供精简简报；邮件版采用内联样式，兼容常见客户端。
"""

import html as html_lib
import re
from .analyzer import AIAnalysisResult


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符。"""
    return html_lib.escape(text) if text else ""


def _format_list_content(text: str) -> str:
    """规范化 AI 列表文本。"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'(\d+\.)\s*【([^】]+)】([:：]?)', r'\1 \2：', text)
    result = re.sub(r'(\d+)\.([^ \d])', r'\1. \2', text)
    result = re.sub(r'(?<=[^\n])\s+(\d+\.)', r'\n\1', result)
    result = re.sub(r'(?<=[^\n])(\d+\.\*\*)', r'\n\1', result)
    result = re.sub(r'([：:;,。；，])\s*(\d+\.)', r'\1\n\2', result)
    result = re.sub(r'([。！？；，、])\s*([a-zA-Z0-9\u4e00-\u9fa5]+(方面|领域)[:：])', r'\1\n\2', result)
    text = re.sub(r'(?<=\S)\n*(【[^】]+】)', r'\n\n\1', result)
    text = re.sub(r'(【[^】]+】)\n+([:：])', r'\1\2', text)
    text = re.sub(r'(【[^】]+】[:：]?)[ \t]*(?=[^\s:：])', r'\1\n', text)
    return re.sub(r'(?<![:：】])\n(\d+\.)', r'\n\n\1', text)


def _format_standalone_summaries(summaries: dict) -> str:
    """格式化独立来源简述。"""
    if not summaries:
        return ""
    return "\n\n".join(
        f"[{name}]:\n{summary}"
        for name, summary in summaries.items()
        if summary
    )


def _sections(result: AIAnalysisResult):
    """仅包含可展示的结论字段，不输出内部来源逐条分析。"""
    return [
        ("今日结论", result.core_trends),
        ("国内影响", result.signals),
        ("后续观察", result.outlook_strategy),
        ("候选观察", result.stock_watchlist),
    ]


def _render_markdown(result: AIAnalysisResult, heading: str = "**") -> str:
    if not result.success:
        return f"⚠️ AI 简报生成失败：{result.error}"
    lines = ["**国内财经简报**", ""]
    for title, text in _sections(result):
        if text:
            prefix = f"#### {title}" if heading == "#### " else f"**{title}**"
            lines.extend([prefix, _format_list_content(text), ""])
    return "\n".join(lines).strip()


def render_ai_analysis_markdown(result: AIAnalysisResult) -> str:
    """渲染为通用 Markdown 格式。"""
    return _render_markdown(result)


def render_ai_analysis_feishu(result: AIAnalysisResult) -> str:
    """渲染为飞书 Markdown 格式。"""
    return _render_markdown(result)


def render_ai_analysis_dingtalk(result: AIAnalysisResult) -> str:
    """渲染为钉钉 Markdown 格式。"""
    return _render_markdown(result, "#### ")


def _html_card(title: str, text: str, highlight: bool = False) -> str:
    """生成邮件客户端友好的紧凑内联样式卡片。"""
    if not text:
        return ""
    background, border, title_color = (
        ("#fffaf0", "#e7c98b", "#805719")
        if highlight else ("#ffffff", "#e2e8f0", "#334155")
    )
    content = _escape_html(_format_list_content(text)).replace("\n", "<br>")
    return (
        '<div style="margin:0 0 8px;padding:10px 12px;'
        f'background:{background};border:1px solid {border};border-radius:7px;">'
        f'<div style="margin:0 0 4px;color:{title_color};font-size:13px;font-weight:700;">'
        f'{_escape_html(title)}</div>'
        f'<div style="color:#334155;font-size:13px;line-height:1.45;">{content}</div>'
        '</div>'
    )


def render_ai_analysis_html(result: AIAnalysisResult) -> str:
    """渲染简洁 HTML 邮件简报。"""
    return render_ai_analysis_html_rich(result)


def render_ai_analysis_plain(result: AIAnalysisResult) -> str:
    """渲染为纯文本简报。"""
    if not result.success:
        return f"AI 简报生成失败：{result.error}"
    lines = ["【国内财经简报】", ""]
    for title, text in _sections(result):
        if text:
            lines.extend([f"[{title}]", _format_list_content(text), ""])
    return "\n".join(lines).strip()


def get_ai_analysis_renderer(channel: str):
    """按通知渠道选择对应格式。"""
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
    """邮件用紧凑财经简报卡片。"""
    if not result:
        return ""
    if not result.success:
        return (
            '<div style="margin:0 0 8px;padding:10px;border:1px solid #fecaca;'
            'background:#fef2f2;border-radius:7px;color:#991b1b;font-size:13px;">'
            f'简报生成失败：{_escape_html(result.error or "未知错误")}</div>'
        )

    html = (
        '<div style="margin:0 0 12px;padding:12px;background:#f8fafc;'
        'border:1px solid #dbe3ec;border-radius:9px;">'
        '<div style="margin:0 0 9px;color:#172b4d;font-size:16px;font-weight:700;">'
        '国内财经简报</div>'
    )
    for title, text in _sections(result):
        html += _html_card(title, text, highlight=title in ("今日结论", "候选观察"))
    html += "</div>"
    return html

# End of file
