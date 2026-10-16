# Visual Post Studio 3.0.2 · Quickstart

## 安装

解压发布包，保留 `visual-post-studio/SKILL.md` 以及子目录。根据客户端支持的 Agent Skills 安装规则复制到 Skills 目录，不要只拷贝 `SKILL.md`。

使用本地严格图片 QA 时，在该文件夹中运行 `python -m pip install -r requirements-image-qa.txt`，再执行 `python scripts/preflight.py` 确认 `strict_image_qa_ready`。没有 Pillow 时只能做明确标注的文件头检查，严格验收会失败。

## 最快启动

**直接生图**：`使用 visual-post-studio，从零做一组4页的旅行攻略图文，风格和每页排版让你决定，直接逐页生成，不要拼成一张。`

**现有资料改图文**：`使用 visual-post-studio，将我提供的说明文档变成图文，先做内容与视觉分镜，等我确认。`

**找模板**：`使用 visual-post-studio，自主寻找几组适合手工教程的视觉参考，附来源链接，从中提炼原创风格。`

**学风格**：`使用 visual-post-studio，看这三张图，提炼可复用的 Visual DNA，然后用同风格制作新内容，不要复制文字和品牌。`

**改单页**：`使用 visual-post-studio，只编辑第2页的图表标题，其他页保持原样。`

## 权限与工具

- **有生图工具**：真正生成/修改图片；每页独立一图。
- **有联网搜索**：可以找到并注明公开参考来源；区分风格灵感和许可明确的可编辑模板。
- **有 Python / 本地文件工具**：可验证图片尺寸、内容哈希、重复、报告时效；安装 Pillow 后可做完整解码检查。正式交付须确定确切页数；文字与内容仍需实际审阅。
- **无相关工具**：说明限制；不伪称完成。

## 主要文件

`SKILL.md` 是入口，任务发生时按需读取 `references/`；风格配置在 `styles/`；可复制文档在 `templates/`。不要把任何特定主题或账号署名强加给新用户。
