#!/usr/bin/env python3
import json
import html
import sys
import re
from datetime import datetime
from pathlib import Path
import uuid

DEFAULT_OUTPUT_DIR = "/tmp"
DEFAULT_OUTPUT_PREFIX = "claude-long-output"
DEFAULT_STAMP = "/tmp/claude-long-output.stamp"
DEFAULT_SIDECAR = "/tmp/claude-last-html-path.txt"


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def block(text: str) -> str:
    if not text:
        return ""
    parts = []
    for para in str(text).split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("<") and para.endswith(">"):
            parts.append(para)
        else:
            parts.append(f"<p>{para}</p>")
    return "\n".join(parts)


def list_items(items):
    if not items:
        return ""
    lis = "\n".join(f"<li>{esc(x)}</li>" for x in items if str(x).strip())
    return f'<ul class="summary-list">{lis}</ul>' if lis else ""


def section_html(section, index):
    title = esc(section.get("title", "未命名栏目"))
    raw_content = section.get("content", "")
    body = block(raw_content)

    eyebrow = f"SECCIÓN {index:02d}"
    word_count = len(re.sub(r'\s+', '', raw_content))
    read_time = max(1, word_count // 300)

    return f"""
    <article class="newspaper-section" id="sec-{index}">
      <div class="section-left">
        <div class="eyebrow">{eyebrow}</div>
        <h2 class="section-title">{title}</h2>
        <div class="section-meta">
          <span class="meta-item">Tiempo: {read_time} min</span>
          <span class="meta-item">Palabras: {word_count}</span>
        </div>
      </div>
      <div class="section-right">
        <div class="article-body">
          {body}
        </div>
      </div>
    </article>
    """


def build_default_output_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return str(Path(DEFAULT_OUTPUT_DIR) / f"{DEFAULT_OUTPUT_PREFIX}-{timestamp}-{suffix}.html")


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("Expected JSON on stdin")
    data = json.loads(raw)

    title = data.get("title", "Claude 长输出")
    subtitle = data.get("subtitle", "")
    summary = data.get("summary", [])
    sections = data.get("sections", [])
    appendix = data.get("appendix", [])
    output = data.get("output") or build_default_output_path()
    stamp = data.get("stamp", DEFAULT_STAMP)
    sidecar = data.get("sidecar", DEFAULT_SIDECAR)
    generated_at = data.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        dt = datetime.strptime(generated_at, "%Y-%m-%d %H:%M")
        display_date = dt.strftime("%B %d, %Y").upper()
    except Exception:
        display_date = generated_at.upper()

    if appendix:
        sections = list(sections) + [{"title": "附录 / 技术细节", "content": "\n\n".join(appendix)}]

    html_doc = f"""<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:wght@400;500;700&display=swap');

    :root[data-theme="light"] {{
      --bg: #f5f1e6;
      --ink: #2c2c2c;
      --ink-soft: #666666;
      --rule-thick: #2c2c2c;
      --rule-thin: #d6ccb6;
      --accent: #b83b3b;
      --code-bg: #e8e2d2;
      --progress: #b83b3b;
    }}

    :root[data-theme="dark"] {{
      --bg: #1c1b19;
      --ink: #d4d4d4;
      --ink-soft: #8a8a8a;
      --rule-thick: #d4d4d4;
      --rule-thin: #3d3b36;
      --accent: #d46c6c;
      --code-bg: #292723;
      --progress: #d46c6c;
    }}

    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; scroll-behavior: smooth; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "DM Sans", sans-serif;
      background-color: var(--bg);
      color: var(--ink);
      padding: 40px 20px 100px;
      transition: background-color 0.4s ease, color 0.4s ease;
    }}

    #reading-progress {{
      position: fixed;
      top: 0; left: 0;
      height: 3px;
      background: var(--progress);
      width: 0%;
      z-index: 1001;
      transition: width 0.15s ease-out;
    }}

    .theme-toggle {{
      position: fixed;
      bottom: 30px; right: 30px;
      width: 44px; height: 44px;
      background: var(--bg);
      border: 1px solid var(--rule-thin);
      border-radius: 50%;
      color: var(--ink-soft);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer;
      z-index: 1000;
      opacity: 0.4;
      transition: all 0.3s ease;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}
    .theme-toggle:hover {{ opacity: 1; border-color: var(--ink); color: var(--ink); }}
    .theme-toggle svg {{ width: 20px; height: 20px; }}
    :root[data-theme="light"] .icon-sun {{ display: none; }}
    :root[data-theme="light"] .icon-moon {{ display: block; }}
    :root[data-theme="dark"] .icon-sun {{ display: block; }}
    :root[data-theme="dark"] .icon-moon {{ display: none; }}

    .broadsheet {{
      max-width: 1100px;
      margin: 0 auto;
    }}

    .masthead {{
      border-bottom: 3px solid var(--rule-thick);
      padding-bottom: 40px;
      margin-bottom: 40px;
    }}
    .masthead-top-bar {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--rule-thick); padding-bottom: 16px; margin-bottom: 24px; }}
    .top-bar-left, .top-bar-right {{ font-family: "DM Sans", sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-soft); max-width: 200px; }}
    .top-bar-left p {{ margin: 0 0 4px; }}
    .top-bar-right {{ text-align: right; }}
    .issue-number {{ font-family: "Cormorant Garamond", serif; font-size: 32px; font-weight: 700; color: var(--accent); line-height: 1; margin-top: 8px; }}

    .masthead h1 {{
      font-family: "Cormorant Garamond", serif;
      font-size: clamp(3.5rem, 7vw, 6.5rem);
      font-weight: 700;
      text-align: center;
      text-transform: uppercase;
      letter-spacing: -0.02em;
      line-height: 0.95;
      margin: 0 0 15px;
      color: var(--ink);
    }}

    .subtitle {{
      text-align: center;
      font-family: "Cormorant Garamond", serif;
      font-style: italic;
      font-size: 1.5rem;
      color: var(--ink-soft);
      max-width: 800px;
      margin: 20px auto 0;
    }}
    .subtitle::before, .subtitle::after {{ content: " · "; }}

    .lead-section {{ padding-bottom: 40px; border-bottom: 1px solid var(--rule-thick); margin-bottom: 50px; }}
    .eyebrow {{ font-family: "DM Sans", sans-serif; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; color: var(--ink-soft); margin-bottom: 16px; border-bottom: 1px solid var(--rule-thin); display: inline-block; padding-bottom: 4px; }}

    .lead-columns {{ column-count: 2; column-gap: 50px; column-rule: 1px solid var(--rule-thin); }}
    .lead-columns ul {{ margin: 0; padding-left: 20px; }}
    .lead-columns li {{
      margin-bottom: 16px;
      font-size: 1.1rem;
      line-height: 1.7;
      color: var(--ink);
      break-inside: avoid;
    }}

    .newspaper-section {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 60px;
      padding-bottom: 60px;
      margin-bottom: 60px;
      border-bottom: 1px solid var(--rule-thin);
    }}
    .newspaper-section:last-child {{ border-bottom: none; margin-bottom: 0; }}

    .section-left {{ position: sticky; top: 40px; align-self: start; }}
    .section-title {{
      font-family: "Cormorant Garamond", serif;
      font-size: 2.6rem;
      font-weight: 700;
      line-height: 1.1;
      margin: 0 0 20px;
      color: var(--ink);
    }}

    .section-meta {{ display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--rule-thin); padding-top: 12px; }}
    .meta-item {{ font-family: "DM Sans", sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); }}

    .article-body {{
      max-width: 660px;
      font-size: 1.12rem;
      line-height: 1.9;
      color: var(--ink);
      font-weight: 400;
    }}

    .article-body p {{
      margin: 0 0 1.8em;
    }}

    .article-body blockquote {{
      margin: 40px 0;
      padding: 0 0 0 24px;
      border-left: 3px solid var(--accent);
      font-family: "Cormorant Garamond", serif;
      font-style: italic;
      font-size: 1.4rem;
      line-height: 1.5;
      color: var(--ink-soft);
    }}

    .article-body ul, .article-body ol {{ padding-left: 1.5em; margin-bottom: 1.8em; }}
    .article-body li {{ margin-bottom: 0.8em; }}

    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; }}
    code {{ background: var(--code-bg); padding: 0.2em 0.4em; border-radius: 4px; }}
    pre {{ background: var(--code-bg); padding: 20px; border-radius: 8px; overflow-x: auto; margin-bottom: 1.8em; }}

    @media (max-width: 900px) {{
      body {{ padding: 20px 15px 80px; }}
      .masthead-top-bar {{ flex-direction: column; gap: 16px; text-align: left; }}
      .top-bar-right {{ text-align: left; }}
      .lead-columns {{ column-count: 1; }}
      .newspaper-section {{ grid-template-columns: 1fr; gap: 20px; }}
      .section-left {{ position: static; }}
      .article-body {{ max-width: 100%; }}
    }}
  </style>
</head>
<body>

  <div id="reading-progress"></div>

  <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle Theme">
    <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
    <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
  </button>

  <main class="broadsheet">
    <header class="masthead">
      <div class="masthead-top-bar">
        <div class="top-bar-left">
          <p>Claude Editorial Engine</p>
          <p>Anti-fatigue Reading Mode</p>
        </div>
        <div class="top-bar-right">
          <p>{display_date}</p>
          <div class="issue-number"># 0001</div>
        </div>
      </div>
      <h1>{esc(title)}</h1>
      <div class="subtitle">{esc(subtitle)}</div>
    </header>

    <section class="lead-section">
      <div class="eyebrow">Resumen / 导读摘要</div>
      <div class="lead-columns">
        {list_items(summary)}
      </div>
    </section>

    <div class="articles-container">
      {''.join(section_html(s, i + 1) for i, s in enumerate(sections))}
    </div>
  </main>

  <script>
    function toggleTheme() {{
      const html = document.documentElement;
      const currentTheme = html.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('claude_newspaper_theme', newTheme);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      const savedTheme = localStorage.getItem('claude_newspaper_theme') || 'light';
      document.documentElement.setAttribute('data-theme', savedTheme);
    }});

    window.addEventListener('scroll', () => {{
      const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
      const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrolled = (height > 0) ? (winScroll / height) * 100 : 0;
      document.getElementById("reading-progress").style.width = scrolled + "%";
    }});

    window.MathJax = {{ tex: {{ inlineMath: [['$','$'], ['\\(','\\)']], displayMath: [['$$','$$'], ['\\[','\\]']] }}, svg: {{ fontCache: 'global' }} }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</body>
</html>
"""

    out = Path(output).expanduser().resolve()
    out.write_text(html_doc, encoding="utf-8")
    Path(stamp).expanduser().write_text(generated_at, encoding="utf-8")
    Path(sidecar).expanduser().write_text(str(out), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
