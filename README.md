# Visual Post Studio 3.0.2

一个**不限主题、不限定页数、不绑定平台或作者**的图文创作 Agent Skill：从零选题，或改编现有文档/字幕/照片；学习用户的参考图，或经授权自行找视觉案例；根据内容规划不同页面构图，逐页调用生图工具并校验交付结果。

**这是 Agent Skill，不是自带生图模型的独立 App。** 图像生成、网页搜索、文件读取等依赖安装它的 Agent 所具备的工具。无对应工具时必须说明限制，不能声称已经生成或搜索。

## 3.0 主要升级

- **Visual DNA：** 视觉系统独立于具体页布局，支持参考图分析、既有页批准和公开设计样例提炼。
- **页面家族 / 变体：** 先判定每页传播任务、资产类型和文字密度，再决定版式，不固定7页、不要求每种类型都先建立一堆变体。
- **生产路径：** 规划-only、直接生图、试样、按已批准样板扩展、单页局部修改，按用户表达自动选择；不重复索取已给的授权。
- **正式 QA：** 检查 PNG/JPEG 文件能否完整解码、确切页数、大小、比例、重复图、页面编号、SHA-256 与旧报告是否失效。另设人工审阅记录，不把脚本冒充成画质/文字/事实验证。
- **发布包分离：** 开发库中的测试和 `examples/` 示例任务不进入运行时包；公开版默认递归去掉 `styles/` 内的图片素材，带图版需自行审查分发权。

## 典型用法

```text
使用 visual-post-studio，帮我从零设计一篇有关家庭收纳的6页图文。自己决定风格并逐页生成完整独立图片，先不要给我一张拼图。
```

```text
使用 visual-post-studio，把我上传的长文章拆成适合微信公众号的4页横向知识图。先给分镜，不要生图。
```

```text
分析我上传的3张版式参考图，提炼视觉DNA。然后用同样的视觉语言做一篇新的咖啡教程，不要复制原图内容和品牌。
```

```text
你自己去找3组旅行图文的视觉参考，列出真实出处。选定后直接生成5张独立的3:4竖图，不要自动复刻他人画面。
```

```text
第4页标题太拥挤，保持其他页面和所有未选中内容不变，只修改第4页顶部的标题。
```

## 安装

公开源码：[deathcats4/visual-post-studio-skill](https://github.com/deathcats4/visual-post-studio-skill)。首次安装可直接克隆到客户端的 Skills 目录，例如：

```bash
git clone https://github.com/deathcats4/visual-post-studio-skill.git "$HOME/.agents/skills/visual-post-studio"
```

已有同名安装时先确认其来源；受本机源码管理的安装副本仍通过原源码的维护脚本更新。公开仓库从经过检查的源码快照开始，不包含原私有仓库的 Git 历史、参考图片、本机安装记录或图文生产作品。开发脚本、测试与待验收案例保留，案例状态不代表实际生图已通过验收。

把 `visual-post-studio` 文件夹放入兼容 Agent Skills 的客户端所指定的 Skills 目录，并按客户端需要刷新。见 [QUICKSTART.md](QUICKSTART.md)。根目录必须包含 `SKILL.md`，以及运行时 `references/`、`templates/`、`scripts/`、`styles/`。

Codex 的用户级目录是 `~/.agents/skills/visual-post-studio`。本地源码安装的副本会生成 `.installation.json`，其中 `source_repository` 指向唯一修改入口；更新时回到源码保存并同步。开发包提供 `AGENTS.md`、`DEVELOPMENT.md` 和 `scripts/save.sh`，运行时包只保留图文生产所需内容。

## 生产过程

`任务路由 → 内容/证据 → 逐页规划 → Visual DNA → 页面家族/变体 → 生图/修改 → 单页复核 → 整套QA → 发布材料`

**不要求每次都全部执行。** 只想要标题时不生成图片；只修改某页时不重新做整篇；给出明确“直接生成”命令时不在每个阶段反复等待。

用户提供的内容和技术截图为事实来源，模板和参考图主要是视觉依据。没有来源的运行结果、软件截图、医学/科研数字和真实人物经历不得编造。

## 文件结构

```text
visual-post-studio/
├── SKILL.md                 # 任务入口，渐进式按需加载 references
├── references/              # 路由、Visual DNA、页面家族、生图合同、QA等
├── templates/               # 分镜/生产表/DNA/证据/审查记录模板
├── styles/                  # 可插拔风格包；editorial-tech 是可选示例
├── requirements-image-qa.txt # 严格图片 QA 的 Pillow 依赖
├── scripts/
│   ├── new_project.py
│   ├── new_style_pack.py
│   ├── preflight.py
│   ├── qa_images.py
│   ├── verify_final_qa.py
│   ├── package_skill.py
│   ├── validate_project.py  # v2兼容命令
│   └── validate_skill.py
└── QUICKSTART.md
```

## 本地工具（Python 3.9+）

项目和风格包创建脚本使用标准库；严格图片验收需要 Pillow。`preflight.py` 的 `strict_image_qa_ready` 表明当前环境是否具备严格验收条件，无法据此推断宿主是否有生图工具。

```bash
python -m pip install -r requirements-image-qa.txt
python scripts/validate_skill.py .
python scripts/preflight.py --output preflight.json
python scripts/new_project.py --slug my-post --topic "城市散步" --pages 3 --canvas 3:4 --pixels 1080x1440 --out ./projects
# Agent 根据分镜生成独立图片并保存至 projects/my-post/images/final/01.png ...
# Agent 只有在真实完成生图后才将 manifest.image_generation_status 设为 complete
python scripts/qa_images.py projects/my-post --report projects/my-post/reviews/qa-report.json --strict
python scripts/verify_final_qa.py projects/my-post --report projects/my-post/reviews/qa-report.json
# 实际人工/多模态审阅后填写 page-review.json，可额外要求它:
python scripts/verify_final_qa.py projects/my-post --report projects/my-post/reviews/qa-report.json --require-review
```

草稿可保留 `page_count: null`，正式交付前必须填写确切的正整数页数并完成实际生图。严格验收会校验并加载图片像素；没有 Pillow 时会报错。非严格检查可在无 Pillow 时读取文件头，但报告会标记为 `header_only`，不能作为完整图片验收。

`--require-review` **不是自动审美打分**，而是要求一份由真正执行过检查的人员或代理填写的复核记录，并校验每页对应的哈希。脚本不能辨别图片中的事实错误、乱码、侵权、不当使用真实UI等内容。旧版 `validate_project.py` 只读 PNG 文件头，保留作兼容命令；最终验收使用上面的 `qa_images.py --strict` 和 `verify_final_qa.py`。

## 从开发目录构建发布 ZIP

```bash
python scripts/package_skill.py --output ../visual-post-studio_v3.0.2_public.zip
python scripts/package_skill.py --output ../visual-post-studio_v3.0.2_with-reference-images.zip --include-example-images
python -m unittest discover -s tests -v
```

不要把开发目录中的测试/缓存一股脑发布。公开版递归排除 `styles/` 内的常见图片文件（含嵌套目录、SVG 和非 `examples/` 路径），并清理 `style.json` 中对应的图片引用；其他目录和非图片附件仍需检查后再加入运行时资源。可选带图版中的既有 AI 创作示例可能包含特定账号标识或品牌，公开再次分发前必须确认权利并参考 `styles/editorial-tech/attribution.md`。

上面的打包命令用于检查当前文件。正式源码发布使用 `python scripts/maintain.py release --out ..`，从已提交状态生成公开包、开发包和验证记录，并拒绝覆盖旧版文件；具体保存与版本约定见开发包的 `DEVELOPMENT.md`。

## 兼容性与边界

核心要求 Agent Skills 格式（`SKILL.md`）；输出图片要求宿主有生图/修图工具；联网发现模板要求宿主有实际可用的搜索工具。AI 对参考图的“学习”指生成可重用规范，**不是微调模型权重**。本包可本地做规则和 QA 测试，不等于所有 Agent 的端到端生图能力都已经验收。

## License

Skill 文本和脚本 MIT；第三方图标、模板、参考图片和作品需要依据各自的许可使用。
