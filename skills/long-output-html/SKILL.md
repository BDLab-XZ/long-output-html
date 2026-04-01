---
name: long-output-html
description: Use when the answer will likely exceed three terminal paragraphs or the user asks for a detailed/structured explanation. Decide before writing正文, render the full answer to local HTML first, then reply in the terminal with only a brief conclusion, 3-7 bullet summaries, and the HTML path.
---

# long-output-html

将长回答直接渲染到本地 HTML 页面，而不是先在终端输出长正文再二次改写。

## 何时必须使用

满足任一条件时，直接走本 skill：

- 预计回答不能在三段内讲清
- 用户要求“详细介绍 / 详细分析 / 系统讲讲 / 展开说说 / 全面对比”
- 预计需要明显的章节结构，终端直接展开会降低可读性
- 不确定会不会超长时，默认走 HTML

## 核心规则

1. **先分诊，后输出**：必须在正文输出前决定是否走 HTML。
2. **禁止事后补救**：不要先在终端铺长正文，再改成 HTML。
3. **终端只留摘要**：生成 HTML 后，终端只输出一句话结论、3-7 条摘要、HTML 路径、可选一句阅读建议。
4. **统一走现有脚本**：只调用 `$HOME/.claude/scripts/render_long_output_html.py`。
5. **只描述当前能力**：不要假设折叠、标签展示或其他未实现交互。

## 最小输入结构

在调用本 skill 前，先把内容组织成 JSON：

```json
{
  "title": "页面标题",
  "subtitle": "副标题，可选",
  "summary": ["3-7 条摘要"],
  "sections": [
    {
      "title": "一级栏目标题",
      "content": "栏目正文，支持多段"
    }
  ],
  "appendix": ["附录内容，可选"],
  "output": "/tmp/claude-long-output-<timestamp>.html"
}
```

字段约束：
- `title`：必填
- `summary`：必填，3-7 条
- `sections`：必填，正文主体
- `subtitle` / `appendix` / `output`：可选
- 若不传 `output`，脚本会自动生成唯一 HTML 文件名

## 执行步骤

1. 先完成长度分诊，确认走 HTML。
2. 将内容组织为上述 JSON。
3. 使用 Bash 调用：

```bash
python3 "$HOME/.claude/scripts/render_long_output_html.py" <<'EOF'
<JSON>
EOF
```

4. 记录脚本返回的真实 HTML 路径。
5. 在终端只输出：
   - 一句话结论
   - 3-7 条核心摘要
   - HTML 路径
   - 可选一句阅读建议

## 与 hook 的关系

- 渲染脚本会写出 HTML 文件，并更新 sidecar 与 stamp
- Stop hook 会在回答结束后尝试自动打开刚生成的 HTML
- 是否走长输出，必须由回答前的长度分诊决定，不依赖 hook 判断

## 输出约束

终端不要重复 HTML 正文，只输出类似：

```text
一句话结论：这是一个适合 HTML 阅读的长回答。

核心摘要：
- ...
- ...
- ...

HTML 路径：
- /tmp/claude-long-output-20260401-153000.html
```

## 失败处理

如果 HTML 渲染脚本失败：

1. 简短告知用户“HTML 渲染失败”
2. 说明失败点（例如 JSON 格式问题 / 脚本调用失败）
3. 优先修正渲染问题后重新生成
4. 不要退回到直接在终端铺完整长正文，除非用户明确要求
