# long-output-html

把 Claude 的长回答直接渲染成本地 HTML 页面阅读，而不是先把长正文铺满终端。

这个仓库包含三部分：

- `skills/long-output-html/SKILL.md`：skill 定义
- `scripts/render_long_output_html.py`：把结构化 JSON 渲染成 HTML，并写入 sidecar/stamp
- `scripts/open_long_output_if_fresh.sh`：供 Claude Code `Stop` hook 调用，在回答结束后自动打开刚生成的 HTML

当前默认方案按你本地 Claude 目录安装，目标是尽量复用现有闭环，不引入额外依赖或额外服务。

## 效果

- 当回答预计超过三段时，优先走 HTML 阅读
- 终端只保留一句结论、3–7 条摘要和 HTML 路径
- HTML 写到本地临时文件
- 若配置了 `Stop` hook，Claude 回复结束后会自动打开最新 HTML

## 当前边界

- 自动打开脚本当前使用 macOS 的 `open` 命令，因此默认只验证过 macOS
- Linux / Windows 用户如果需要自动打开，请自行替换 `open_long_output_if_fresh.sh` 里的打开命令
- 如果你只想要 HTML 渲染，不需要自动打开，可以只安装 skill 和 render 脚本，不配置 `Stop` hook

## 安装

### 1. 复制 skill

将仓库里的 skill 目录复制到 Claude 目录：

```bash
mkdir -p ~/.claude/skills
cp -R skills/long-output-html ~/.claude/skills/
```

### 2. 复制脚本

```bash
mkdir -p ~/.claude/scripts
cp scripts/render_long_output_html.py ~/.claude/scripts/
cp scripts/open_long_output_if_fresh.sh ~/.claude/scripts/
chmod +x ~/.claude/scripts/render_long_output_html.py
chmod +x ~/.claude/scripts/open_long_output_if_fresh.sh
```

### 3. 配置 `Stop` hook

把 `settings/settings.example.json` 里的 `hooks.Stop` 示例合并到你的 `~/.claude/settings.json`。

最小示例：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/.claude/scripts/open_long_output_if_fresh.sh\" \"/tmp/claude-last-html-path.txt\" \"/tmp/claude-long-output.stamp\""
          }
        ]
      }
    ]
  }
}
```

如果你已有其他 `Stop` hooks，请合并，不要直接覆盖整个 `settings.json`。

## 使用方式

### 方式 1：作为 skill 使用

当你需要详细、结构化、明显超过三段的回答时，使用 `/long-output-html`。

该 skill 的约束是：

- 必须在正文输出前决定走不走 HTML
- 不先在终端铺长正文，再事后改成 HTML
- 终端只输出简短结论、摘要和 HTML 路径

### 方式 2：直接调用渲染脚本

你也可以直接传入 JSON：

```bash
python3 $HOME/.claude/scripts/render_long_output_html.py <<'EOF'
{
  "title": "示例长回答",
  "subtitle": "最小渲染测试",
  "summary": [
    "这是第一条摘要",
    "这是第二条摘要",
    "这是第三条摘要"
  ],
  "sections": [
    {
      "title": "正文示例",
      "content": "第一段内容。\n\n第二段内容。"
    }
  ]
}
EOF
```

脚本会：

- 生成一个本地 HTML 文件
- 写入 `/tmp/claude-last-html-path.txt`
- 写入 `/tmp/claude-long-output.stamp`
- 在 stdout 输出最终 HTML 路径

## 验证

建议按下面顺序验收：

### A. 渲染链路

执行上面的最小 JSON 示例，确认：

- 返回了一个 `.html` 路径
- 该 HTML 文件确实存在
- `/tmp/claude-last-html-path.txt` 已写入最新 HTML 路径
- `/tmp/claude-long-output.stamp` 已生成

### B. 自动打开链路

手动运行：

```bash
bash $HOME/.claude/scripts/open_long_output_if_fresh.sh \
  /tmp/claude-last-html-path.txt \
  /tmp/claude-long-output.stamp
```

确认：

- 浏览器或系统默认 HTML 查看器被打开
- `/tmp/claude-long-output.stamp` 被消费删除

### C. 真实 skill 链路

在 Claude Code 里触发一次 `/long-output-html`，确认：

- 终端只保留简短摘要，不重复全文
- 输出了 HTML 路径
- 回答结束后自动打开 HTML（若已配置 `Stop` hook）

## 仓库结构

```text
.
├── README.md
├── LICENSE
├── skills/
│   └── long-output-html/
│       └── SKILL.md
├── scripts/
│   ├── render_long_output_html.py
│   └── open_long_output_if_fresh.sh
└── settings/
    └── settings.example.json
```

## 设计说明

这个仓库刻意保持最小化：

- 不公开个人 `settings.local.json`
- 不携带无关 permission allowlist
- 不打包其他 hooks 或个人脚本
- 不扩展未验证的新交互能力

发布版只保留当前已验证可用的最小闭环。

## License

MIT
