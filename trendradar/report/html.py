# coding=utf-8
"""
HTML 报告渲染模块

提供 HTML 格式的热点新闻报告生成功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape
from trendradar.utils.time import convert_time_for_display
from trendradar.ai.formatter import render_ai_analysis_html_rich


def render_html_content(
    report_data: Dict,
    total_titles: int,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
    display_mode: str = "keyword",
    standalone_data: Optional[Dict] = None,
    ai_analysis: Optional[Any] = None,
    show_new_section: bool = True,
) -> str:
    """渲染HTML内容

    Args:
        report_data: 报告数据字典，包含 stats, new_titles, failed_ids, total_new_count
        total_titles: 新闻总数
        mode: 报告模式 ("daily", "current", "incremental")
        update_info: 更新信息（可选）
        region_order: 区域显示顺序列表
        get_time_func: 获取当前时间的函数（可选，默认使用 datetime.now）
        rss_items: RSS 统计条目列表（可选）
        rss_new_items: RSS 新增条目列表（可选）
        display_mode: 显示模式 ("keyword"=按关键词分组, "platform"=按平台分组)
        standalone_data: 独立展示区数据（可选），包含 platforms 和 rss_feeds
        ai_analysis: AI 分析结果对象（可选），AIAnalysisResult 实例
        show_new_section: 是否显示新增热点区域

    Returns:
        渲染后的 HTML 字符串
    """
    # 默认区域顺序
    default_region_order = ["hotlist", "rss", "new_items", "standalone", "ai_analysis"]
    if region_order is None:
        region_order = default_region_order

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TrendRadar · 国内财经简报</title>
        <meta name="color-scheme" content="light">
        <meta name="format-detection" content="telephone=no">
        <style>
            * { box-sizing: border-box; }

            body {
                margin: 0;
                padding: 0;
                background: #EDEAE2;
                color: #101820;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                    "Noto Sans SC", sans-serif;
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
            }

            .page { padding: 24px 12px; background: #EDEAE2; }

            .container {
                max-width: 600px;
                margin: 0 auto;
                background: #FFFFFF;
                border: 1px solid #E2DCD0;
                border-radius: 6px;
                overflow: hidden;
            }

            .masthead { background: #0F1C2B; }
            .masthead table { width: 100%; border-collapse: collapse; }
            .masthead .brand { padding: 24px 26px 18px; vertical-align: top; }
            .masthead .kicker {
                font-size: 10px;
                letter-spacing: 3px;
                color: #93A4B3;
                font-weight: 600;
            }
            .masthead .title {
                margin-top: 8px;
                font-size: 24px;
                line-height: 1.25;
                font-weight: 700;
                color: #FFFFFF;
                letter-spacing: 1px;
            }
            .masthead .subtitle {
                margin-top: 6px;
                font-size: 12px;
                color: #AEBBC6;
                letter-spacing: 1px;
            }
            .masthead .date {
                padding: 24px 26px 18px;
                text-align: right;
                vertical-align: bottom;
                white-space: nowrap;
            }
            .masthead .date-day { font-size: 11px; color: #93A4B3; }
            .masthead .date-time {
                font-size: 22px;
                line-height: 1.2;
                color: #FFFFFF;
                font-weight: 600;
                margin-top: 2px;
            }

            .accent-bar { height: 3px; background: #9F2D2D; }

            .meta {
                padding: 11px 26px;
                background: #FCFBF7;
                border-bottom: 1px solid #EFEAE0;
                font-size: 12px;
                color: #6B7785;
            }
            .meta .sep { color: #CFC8BA; padding: 0 8px; }
            .meta .strong { color: #101820; font-weight: 600; }

            .content { padding: 26px; }

            .section-divider {
                margin-top: 30px;
                padding-top: 26px;
                border-top: 1px solid #E9E4D9;
            }

            .section-heading {
                margin-bottom: 18px;
                padding-bottom: 12px;
                border-bottom: 2px solid #101820;
            }
            .section-kicker {
                font-size: 10px;
                letter-spacing: 2.5px;
                color: #9F2D2D;
                font-weight: 700;
            }
            .section-title {
                margin-top: 2px;
                font-size: 19px;
                font-weight: 700;
                color: #101820;
                letter-spacing: 0.5px;
            }

            .word-group { margin-bottom: 30px; }
            .word-group:last-child { margin-bottom: 0; }

            .word-header {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 12px;
                padding-bottom: 9px;
                border-bottom: 1px solid #E9E4D9;
            }
            .word-info { display: flex; align-items: baseline; gap: 10px; }
            .word-name {
                font-size: 16px;
                font-weight: 700;
                color: #101820;
                letter-spacing: 0.3px;
            }
            .word-count { font-size: 11px; color: #8A94A0; font-weight: 500; }
            .word-count.hot { color: #9F2D2D; }
            .word-count.warm { color: #B7791F; }
            .word-index {
                font-size: 11px;
                color: #A39B8B;
                font-variant-numeric: tabular-nums;
            }

            .news-item {
                display: flex;
                gap: 12px;
                padding: 12px 0;
                border-bottom: 1px solid #F3EFE7;
            }
            .news-item:last-child { border-bottom: none; padding-bottom: 0; }
            .news-number {
                flex: 0 0 26px;
                width: 26px;
                padding-top: 2px;
                font-size: 11px;
                font-weight: 600;
                color: #B0A896;
                font-variant-numeric: tabular-nums;
            }
            .news-content { flex: 1; min-width: 0; }
            .news-header {
                display: flex;
                align-items: center;
                gap: 7px;
                flex-wrap: wrap;
                margin-bottom: 4px;
            }
            .source-name {
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.4px;
                color: #6B7785;
            }
            .keyword-tag {
                font-size: 11px;
                color: #1F4E79;
                background: #EFF4F8;
                padding: 1px 6px;
                border-radius: 3px;
            }
            .rank-num {
                font-size: 10px;
                font-weight: 700;
                color: #5C6672;
                background: #F1EEE7;
                padding: 1px 6px;
                border-radius: 3px;
                font-variant-numeric: tabular-nums;
            }
            .rank-num.top { background: #9F2D2D; color: #FFFFFF; }
            .rank-num.high { background: #C07A2C; color: #FFFFFF; }
            .time-info {
                font-size: 11px;
                color: #929BA6;
                font-variant-numeric: tabular-nums;
            }
            .count-info { font-size: 11px; color: #2F6B4F; font-weight: 600; }
            .tag-new {
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #9F2D2D;
                border: 1px solid #DDB3AF;
                border-radius: 2px;
                padding: 0 4px;
                line-height: 1.5;
            }
            .news-title {
                margin: 0;
                font-size: 15px;
                line-height: 1.55;
                color: #17212B;
            }
            .news-link,
            .rss-link {
                color: #17212B;
                text-decoration: underline;
                text-decoration-color: #D6CFC1;
                text-underline-offset: 2px;
            }
            .news-link:hover,
            .rss-link:hover {
                color: #9F2D2D;
                text-decoration-color: #9F2D2D;
            }

            .new-section { margin-top: 4px; }
            .new-section-title {
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.5px;
                color: #101820;
                margin: 0 0 16px;
                padding-bottom: 9px;
                border-bottom: 1px solid #E9E4D9;
            }
            .new-source-group { margin-bottom: 20px; }
            .new-source-group:last-child { margin-bottom: 0; }
            .new-source-title {
                font-size: 12px;
                font-weight: 600;
                color: #6B7785;
                margin: 0 0 8px;
            }
            .new-item {
                display: flex;
                align-items: baseline;
                gap: 10px;
                padding: 7px 0;
                border-bottom: 1px solid #F5F2EB;
            }
            .new-item:last-child { border-bottom: none; }
            .new-item-number {
                flex: 0 0 20px;
                font-size: 11px;
                color: #B0A896;
                font-variant-numeric: tabular-nums;
            }
            .new-item-rank {
                flex: 0 0 auto;
                font-size: 10px;
                font-weight: 700;
                color: #5C6672;
                background: #F1EEE7;
                padding: 1px 6px;
                border-radius: 3px;
            }
            .new-item-rank.top { background: #9F2D2D; color: #FFFFFF; }
            .new-item-rank.high { background: #C07A2C; color: #FFFFFF; }
            .new-item-content { flex: 1; min-width: 0; }
            .new-item-title {
                margin: 0;
                font-size: 14px;
                line-height: 1.5;
                color: #17212B;
            }

            .rss-section-header {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 14px;
                padding-bottom: 9px;
                border-bottom: 1px solid #E9E4D9;
            }
            .rss-section-title {
                font-size: 16px;
                font-weight: 700;
                color: #101820;
            }
            .rss-section-count { font-size: 11px; color: #8A94A0; }
            .feed-group { margin-bottom: 22px; }
            .feed-group:last-child { margin-bottom: 0; }
            .feed-header {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 8px;
            }
            .feed-name { font-size: 13px; font-weight: 700; color: #33414F; }
            .feed-count { font-size: 11px; color: #8A94A0; }
            .rss-item {
                padding: 9px 0;
                border-bottom: 1px solid #F5F2EB;
            }
            .rss-item:last-child { border-bottom: none; }
            .rss-meta {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin-bottom: 3px;
            }
            .rss-time {
                font-size: 11px;
                color: #929BA6;
                font-variant-numeric: tabular-nums;
            }
            .rss-author { font-size: 11px; color: #6B7785; font-weight: 500; }
            .rss-title { font-size: 14px; line-height: 1.55; }

            .standalone-section-header {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 18px;
                padding-bottom: 9px;
                border-bottom: 1px solid #E9E4D9;
            }
            .standalone-section-title {
                font-size: 16px;
                font-weight: 700;
                color: #101820;
            }
            .standalone-section-count { font-size: 11px; color: #8A94A0; }
            .standalone-group { margin-bottom: 24px; }
            .standalone-group:last-child { margin-bottom: 0; }
            .standalone-header {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 8px;
            }
            .standalone-name { font-size: 13px; font-weight: 700; color: #33414F; }
            .standalone-count { font-size: 11px; color: #8A94A0; }

            .error-section {
                background: #FDF3F2;
                border: 1px solid #E8C4C0;
                border-radius: 4px;
                padding: 14px 16px;
                margin-bottom: 24px;
            }
            .error-title {
                color: #9F2D2D;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.3px;
                margin: 0 0 6px 0;
            }
            .error-list { list-style: none; padding: 0; margin: 0; }
            .error-item {
                color: #7A2E2A;
                font-size: 12px;
                padding: 2px 0;
                font-family: "SFMono-Regular", Consolas, monospace;
            }

            .footer {
                padding: 20px 26px 24px;
                background: #FBF9F4;
                border-top: 1px solid #EFEAE0;
                text-align: center;
            }
            .footer-content { font-size: 11px; line-height: 1.7; color: #8A94A0; }
            .footer-link {
                color: #5A6B7B;
                text-decoration: none;
                border-bottom: 1px solid #D8D1C3;
            }
            .project-name { color: #33414F; font-weight: 600; }

            @media (max-width: 480px) {
                .page { padding: 0 !important; }
                .container {
                    border-radius: 0 !important;
                    border-left: 0 !important;
                    border-right: 0 !important;
                }
                .masthead .brand,
                .masthead .date { padding: 18px 14px 14px !important; }
                .masthead .kicker {
                    font-size: 9px !important;
                    letter-spacing: 1.6px !important;
                }
                .masthead .title { font-size: 20px !important; }
                .masthead .date-day { display: none !important; }
                .masthead .date-time { font-size: 18px !important; }
                .meta { padding: 10px 14px !important; }
                .content { padding: 20px 16px !important; }
                .footer { padding: 18px !important; }
                .news-item { gap: 8px; }
                .news-number { flex-basis: 22px; width: 22px; }
                .news-title { font-size: 14px; }
            }
        </style>
    </head>
    """

    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    weekday_cn = "\u5468" + "\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u65e5"[now.weekday()]
    mode_label = {"current": "\u5f53\u524d\u699c\u5355", "incremental": "\u589e\u91cf\u5206\u6790"}.get(
        mode, "\u5168\u5929\u6c47\u603b"
    )
    date_text = now.strftime("%Y\u5e74%m\u6708%d\u65e5")
    time_text = now.strftime("%H:%M")
    hot_news_count = sum(len(stat["titles"]) for stat in report_data["stats"])

    html += f"""
    <body style="margin:0;padding:0;background:#EDEAE2;">
        <div class="page" style="padding:24px 12px;background:#EDEAE2;">
        <div class="container" style="max-width:600px;margin:0 auto;background:#FFFFFF;border:1px solid #E2DCD0;border-radius:6px;overflow:hidden;">
            <div class="masthead" style="background:#0F1C2B;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                    <tr>
                        <td class="brand" style="padding:24px 26px 18px;vertical-align:top;">
                            <div class="kicker" style="font-size:10px;letter-spacing:3px;color:#93A4B3;font-weight:600;">TRENDRADAR \u00b7 BRIEFING</div>
                            <div class="title" style="margin-top:8px;font-size:24px;line-height:1.25;font-weight:700;color:#FFFFFF;letter-spacing:1px;">\u56fd\u5185\u8d22\u7ecf\u7b80\u62a5</div>
                            <div class="subtitle" style="margin-top:6px;font-size:12px;color:#AEBBC6;letter-spacing:1px;">\u653f\u7b56 \u00b7 \u5e02\u573a \u00b7 \u4f20\u5bfc \u00b7 \u89c2\u5bdf</div>
                        </td>
                        <td class="date" align="right" style="padding:24px 26px 18px;vertical-align:bottom;white-space:nowrap;">
                            <div class="date-day" style="font-size:11px;color:#93A4B3;">{date_text} \u00b7 {weekday_cn}</div>
                            <div class="date-time" style="font-size:22px;line-height:1.2;color:#FFFFFF;font-weight:600;margin-top:2px;">{time_text}</div>
                        </td>
                    </tr>
                </table>
            </div>
            <div style="height:3px;background:#9F2D2D;"></div>
            <div class="meta" style="padding:11px 26px;background:#FCFBF7;border-bottom:1px solid #EFEAE0;font-size:12px;color:#6B7785;">
                <span style="color:#101820;font-weight:600;">{mode_label}</span>
                <span style="color:#CFC8BA;padding:0 8px;">/</span>\u65b0\u95fb {total_titles} \u6761
                <span style="color:#CFC8BA;padding:0 8px;">/</span>\u70ed\u70b9 {hot_news_count} \u6761
                <span style="color:#CFC8BA;padding:0 8px;">/</span>{time_text} \u751f\u6210
            </div>

            <div class="content" style="padding:26px;">"""

    # 处理失败ID错误信息
    if report_data["failed_ids"]:
        html += """
                <div class="error-section">
                    <div class="error-title">请求失败的平台</div>
                    <ul class="error-list">"""
        for id_value in report_data["failed_ids"]:
            html += f'<li class="error-item">{html_escape(id_value)}</li>'
        html += """
                    </ul>
                </div>"""

    # 生成热点词汇统计部分的HTML
    stats_html = ""
    if report_data["stats"]:
        total_count = len(report_data["stats"])

        for i, stat in enumerate(report_data["stats"], 1):
            count = stat["count"]

            # 确定热度等级
            if count >= 10:
                count_class = "hot"
            elif count >= 5:
                count_class = "warm"
            else:
                count_class = ""

            escaped_word = html_escape(stat["word"])

            stats_html += f"""
                <div class="word-group">
                    <div class="word-header">
                        <div class="word-info">
                            <div class="word-name">{escaped_word}</div>
                            <div class="word-count {count_class}">{count} 条</div>
                        </div>
                        <div class="word-index">{i}/{total_count}</div>
                    </div>"""

            # 处理每个词组下的新闻标题，给每条新闻标上序号
            for j, title_data in enumerate(stat["titles"], 1):
                is_new = title_data.get("is_new", False)
                new_class = "new" if is_new else ""

                stats_html += f"""
                    <div class="news-item {new_class}">
                        <div class="news-number">{j}</div>
                        <div class="news-content">
                            <div class="news-header">"""

                if is_new:
                    stats_html += '<span class="tag-new">NEW</span>'

                # 根据 display_mode 决定显示来源还是关键词
                if display_mode == "keyword":
                    # keyword 模式：显示来源
                    stats_html += f'<span class="source-name">{html_escape(title_data["source_name"])}</span>'
                else:
                    # platform 模式：显示关键词
                    matched_keyword = title_data.get("matched_keyword", "")
                    if matched_keyword:
                        stats_html += f'<span class="keyword-tag">[{html_escape(matched_keyword)}]</span>'

                # 处理排名显示
                ranks = title_data.get("ranks", [])
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    rank_threshold = title_data.get("rank_threshold", 10)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= rank_threshold:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    stats_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'

                # 处理时间显示
                time_display = title_data.get("time_display", "")
                if time_display:
                    # 简化时间显示格式，将波浪线替换为~
                    simplified_time = (
                        time_display.replace(" ~ ", "~")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    stats_html += (
                        f'<span class="time-info">{html_escape(simplified_time)}</span>'
                    )

                # 处理出现次数
                count_info = title_data.get("count", 1)
                if count_info > 1:
                    stats_html += f'<span class="count-info">{count_info}次</span>'

                stats_html += """
                            </div>
                            <div class="news-title">"""

                # 处理标题和链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    stats_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    stats_html += escaped_title

                stats_html += """
                            </div>
                        </div>
                    </div>"""

            stats_html += """
                </div>"""

    # 给热榜统计添加外层包装
    if stats_html:
        heading_title = "平台热点" if display_mode == "platform" else "关键词热点"
        stats_html = f"""
                <div class="hotlist-section">
                    <div class="section-heading">
                        <div class="section-kicker">HOT TOPICS</div>
                        <div class="section-title">{heading_title}</div>
                    </div>{stats_html}
                </div>"""

    # 生成新增新闻区域的HTML
    new_titles_html = ""
    if show_new_section and report_data["new_titles"]:
        new_titles_html += f"""
                <div class="new-section">
                    <div class="new-section-title">本次新增热点 (共 {report_data['total_new_count']} 条)</div>"""

        for source_data in report_data["new_titles"]:
            escaped_source = html_escape(source_data["source_name"])
            titles_count = len(source_data["titles"])

            new_titles_html += f"""
                    <div class="new-source-group">
                        <div class="new-source-title">{escaped_source} · {titles_count}条</div>"""

            # 为新增新闻也添加序号
            for idx, title_data in enumerate(source_data["titles"], 1):
                ranks = title_data.get("ranks", [])

                # 处理新增新闻的排名显示
                rank_class = ""
                if ranks:
                    min_rank = min(ranks)
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= title_data.get("rank_threshold", 10):
                        rank_class = "high"

                    if len(ranks) == 1:
                        rank_text = str(ranks[0])
                    else:
                        rank_text = f"{min(ranks)}-{max(ranks)}"
                else:
                    rank_text = "?"

                new_titles_html += f"""
                        <div class="new-item">
                            <div class="new-item-number">{idx}</div>
                            <div class="new-item-rank {rank_class}">{rank_text}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">"""

                # 处理新增新闻的链接
                escaped_title = html_escape(title_data["title"])
                link_url = title_data.get("mobile_url") or title_data.get("url", "")

                if link_url:
                    escaped_url = html_escape(link_url)
                    new_titles_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    new_titles_html += escaped_title

                new_titles_html += """
                                </div>
                            </div>
                        </div>"""

            new_titles_html += """
                    </div>"""

        new_titles_html += """
                </div>"""

    # 生成 RSS 统计内容
    def render_rss_stats_html(stats: List[Dict], title: str = "RSS 订阅更新") -> str:
        """渲染 RSS 统计区块 HTML

        Args:
            stats: RSS 分组统计列表，格式与热榜一致：
                [
                    {
                        "word": "关键词",
                        "count": 5,
                        "titles": [
                            {
                                "title": "标题",
                                "source_name": "Feed 名称",
                                "time_display": "12-29 08:20",
                                "url": "...",
                                "is_new": True/False
                            }
                        ]
                    }
                ]
            title: 区块标题

        Returns:
            渲染后的 HTML 字符串
        """
        if not stats:
            return ""

        # 计算总条目数
        total_count = sum(stat.get("count", 0) for stat in stats)
        if total_count == 0:
            return ""

        rss_html = f"""
                <div class="rss-section">
                    <div class="rss-section-header">
                        <div>
                            <div class="section-kicker">RSS FEEDS</div>
                            <div class="rss-section-title">{title}</div>
                        </div>
                        <div class="rss-section-count">{total_count} 条</div>
                    </div>"""

        # 按关键词分组渲染（与热榜格式一致）
        for stat in stats:
            keyword = stat.get("word", "")
            titles = stat.get("titles", [])
            if not titles:
                continue

            keyword_count = len(titles)

            rss_html += f"""
                    <div class="feed-group">
                        <div class="feed-header">
                            <div class="feed-name">{html_escape(keyword)}</div>
                            <div class="feed-count">{keyword_count} 条</div>
                        </div>"""

            for title_data in titles:
                item_title = title_data.get("title", "")
                url = title_data.get("url", "")
                time_display = title_data.get("time_display", "")
                source_name = title_data.get("source_name", "")
                is_new = title_data.get("is_new", False)

                rss_html += """
                        <div class="rss-item">
                            <div class="rss-meta">"""

                if time_display:
                    rss_html += f'<span class="rss-time">{html_escape(time_display)}</span>'

                if source_name:
                    rss_html += f'<span class="rss-author">{html_escape(source_name)}</span>'

                if is_new:
                    rss_html += '<span class="tag-new">NEW</span>'

                rss_html += """
                            </div>
                            <div class="rss-title">"""

                escaped_title = html_escape(item_title)
                if url:
                    escaped_url = html_escape(url)
                    rss_html += f'<a href="{escaped_url}" target="_blank" class="rss-link">{escaped_title}</a>'
                else:
                    rss_html += escaped_title

                rss_html += """
                            </div>
                        </div>"""

            rss_html += """
                    </div>"""

        rss_html += """
                </div>"""
        return rss_html

    # 生成独立展示区内容
    def render_standalone_html(data: Optional[Dict]) -> str:
        """渲染独立展示区 HTML（复用热点词汇统计区样式）

        Args:
            data: 独立展示数据，格式：
                {
                    "platforms": [
                        {
                            "id": "zhihu",
                            "name": "知乎热榜",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "rank": 1,
                                    "ranks": [1, 2, 1],
                                    "first_time": "08:00",
                                    "last_time": "12:30",
                                    "count": 3,
                                }
                            ]
                        }
                    ],
                    "rss_feeds": [
                        {
                            "id": "hacker-news",
                            "name": "Hacker News",
                            "items": [
                                {
                                    "title": "标题",
                                    "url": "链接",
                                    "published_at": "2025-01-07T08:00:00",
                                    "author": "作者",
                                }
                            ]
                        }
                    ]
                }

        Returns:
            渲染后的 HTML 字符串
        """
        if not data:
            return ""

        platforms = data.get("platforms", [])
        rss_feeds = data.get("rss_feeds", [])

        if not platforms and not rss_feeds:
            return ""

        # 计算总条目数
        total_platform_items = sum(len(p.get("items", [])) for p in platforms)
        total_rss_items = sum(len(f.get("items", [])) for f in rss_feeds)
        total_count = total_platform_items + total_rss_items

        if total_count == 0:
            return ""

        standalone_html = f"""
                <div class="standalone-section">
                    <div class="standalone-section-header">
                        <div>
                            <div class="section-kicker">CURATED</div>
                            <div class="standalone-section-title">独立展示区</div>
                        </div>
                        <div class="standalone-section-count">{total_count} 条</div>
                    </div>"""

        # 渲染热榜平台（复用 word-group 结构）
        for platform in platforms:
            platform_name = platform.get("name", platform.get("id", ""))
            items = platform.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group">
                        <div class="standalone-header">
                            <div class="standalone-name">{html_escape(platform_name)}</div>
                            <div class="standalone-count">{len(items)} 条</div>
                        </div>"""

            # 渲染每个条目（复用 news-item 结构）
            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "") or item.get("mobileUrl", "")
                rank = item.get("rank", 0)
                ranks = item.get("ranks", [])
                first_time = item.get("first_time", "")
                last_time = item.get("last_time", "")
                count = item.get("count", 1)

                standalone_html += f"""
                        <div class="news-item">
                            <div class="news-number">{j}</div>
                            <div class="news-content">
                                <div class="news-header">"""

                # 排名显示（复用 rank-num 样式，无 # 前缀）
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)

                    # 确定排名等级
                    if min_rank <= 3:
                        rank_class = "top"
                    elif min_rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""

                    if min_rank == max_rank:
                        rank_text = str(min_rank)
                    else:
                        rank_text = f"{min_rank}-{max_rank}"

                    standalone_html += f'<span class="rank-num {rank_class}">{rank_text}</span>'
                elif rank > 0:
                    if rank <= 3:
                        rank_class = "top"
                    elif rank <= 10:
                        rank_class = "high"
                    else:
                        rank_class = ""
                    standalone_html += f'<span class="rank-num {rank_class}">{rank}</span>'

                # 时间显示（复用 time-info 样式，将 HH-MM 转换为 HH:MM）
                if first_time and last_time and first_time != last_time:
                    first_time_display = convert_time_for_display(first_time)
                    last_time_display = convert_time_for_display(last_time)
                    standalone_html += f'<span class="time-info">{html_escape(first_time_display)}~{html_escape(last_time_display)}</span>'
                elif first_time:
                    first_time_display = convert_time_for_display(first_time)
                    standalone_html += f'<span class="time-info">{html_escape(first_time_display)}</span>'

                # 出现次数（复用 count-info 样式）
                if count > 1:
                    standalone_html += f'<span class="count-info">{count}次</span>'

                standalone_html += """
                                </div>
                                <div class="news-title">"""

                # 标题和链接（复用 news-link 样式）
                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += """
                    </div>"""

        # 渲染 RSS 源（复用相同结构）
        for feed in rss_feeds:
            feed_name = feed.get("name", feed.get("id", ""))
            items = feed.get("items", [])
            if not items:
                continue

            standalone_html += f"""
                    <div class="standalone-group">
                        <div class="standalone-header">
                            <div class="standalone-name">{html_escape(feed_name)}</div>
                            <div class="standalone-count">{len(items)} 条</div>
                        </div>"""

            for j, item in enumerate(items, 1):
                title = item.get("title", "")
                url = item.get("url", "")
                published_at = item.get("published_at", "")
                author = item.get("author", "")

                standalone_html += f"""
                        <div class="news-item">
                            <div class="news-number">{j}</div>
                            <div class="news-content">
                                <div class="news-header">"""

                # 时间显示（格式化 ISO 时间）
                if published_at:
                    try:
                        from datetime import datetime as dt
                        if "T" in published_at:
                            dt_obj = dt.fromisoformat(published_at.replace("Z", "+00:00"))
                            time_display = dt_obj.strftime("%m-%d %H:%M")
                        else:
                            time_display = published_at
                    except:
                        time_display = published_at

                    standalone_html += f'<span class="time-info">{html_escape(time_display)}</span>'

                # 作者显示
                if author:
                    standalone_html += f'<span class="source-name">{html_escape(author)}</span>'

                standalone_html += """
                                </div>
                                <div class="news-title">"""

                escaped_title = html_escape(title)
                if url:
                    escaped_url = html_escape(url)
                    standalone_html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                else:
                    standalone_html += escaped_title

                standalone_html += """
                                </div>
                            </div>
                        </div>"""

            standalone_html += """
                    </div>"""

        standalone_html += """
                </div>"""
        return standalone_html

    # 生成 RSS 统计和新增 HTML
    rss_stats_html = render_rss_stats_html(rss_items, "RSS 订阅更新") if rss_items else ""
    rss_new_html = render_rss_stats_html(rss_new_items, "RSS 新增更新") if rss_new_items else ""

    # 生成独立展示区 HTML
    standalone_html = render_standalone_html(standalone_data)

    # 生成 AI 分析 HTML
    ai_html = render_ai_analysis_html_rich(ai_analysis) if ai_analysis else ""

    # 准备各区域内容映射
    region_contents = {
        "hotlist": stats_html,
        "rss": rss_stats_html,
        "new_items": (new_titles_html, rss_new_html),  # 元组，分别处理
        "standalone": standalone_html,
        "ai_analysis": ai_html,
    }

    def add_section_divider(content: str) -> str:
        """为内容的外层 div 添加 section-divider 类"""
        if not content or 'class="' not in content:
            return content
        first_class_pos = content.find('class="')
        if first_class_pos != -1:
            insert_pos = first_class_pos + len('class="')
            return content[:insert_pos] + "section-divider " + content[insert_pos:]
        return content

    # 按 region_order 顺序组装内容，动态添加分割线
    has_previous_content = False
    for region in region_order:
        content = region_contents.get(region, "")
        if region == "new_items":
            # 特殊处理 new_items 区域（包含热榜新增和 RSS 新增两部分）
            new_html, rss_new = content
            if new_html:
                if has_previous_content:
                    new_html = add_section_divider(new_html)
                html += new_html
                has_previous_content = True
            if rss_new:
                if has_previous_content:
                    rss_new = add_section_divider(rss_new)
                html += rss_new
                has_previous_content = True
        elif content:
            if has_previous_content:
                content = add_section_divider(content)
            html += content
            has_previous_content = True

    html += f"""
            </div>

            <div class="footer" style="padding:20px 26px 24px;background:#FBF9F4;border-top:1px solid #EFEAE0;text-align:center;">
                <div class="footer-content" style="font-size:11px;line-height:1.7;color:#8A94A0;">
                    \u7531 <span class="project-name" style="color:#33414F;font-weight:600;">TrendRadar</span> \u751f\u6210 \u00b7
                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" class="footer-link" style="color:#5A6B7B;text-decoration:none;border-bottom:1px solid #D8D1C3;">
                        GitHub \u5f00\u6e90\u9879\u76ee
                    </a>"""

    if update_info:
        html += f"""
                </div>
                <div style="margin-top:8px;font-size:11px;color:#B7791F;">
                    \u53d1\u73b0\u65b0\u7248\u672c {update_info['remote_version']}\uff0c\u5f53\u524d\u7248\u672c {update_info['current_version']}
                </div>"""
    else:
        html += """
                </div>"""
    html += """
            </div>
        </div>
        </div>
    </body>
    </html>
    """

    return html
