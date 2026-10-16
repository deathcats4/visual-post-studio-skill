# Style Packs — 插拔式视觉风格库

风格包**可选**，一个任务完全可以 `style=auto` 不用预设。页面布局类型由内容决定；使用风格包不代表所有页按同一模板排版。

## 标准布局

```text
styles/my-style/
├── style.md        # 给Agent读取的设计规则，含 invariants/variants
├── style.json      # 可选机器可读配色、网格/画幅偏好
├── examples/       # 可选的授权视觉参考图
└── attribution.md  # 可选版权/来源说明
```

从参考图片提炼：给 Agent 看图并按 `templates/style-card.md` 写 `style.md`，再把有使用权限的图片放入 `examples/`。开发源码附带 `editorial-tech` 的过去作品示例，以及无图片的 `minimal-editorial` 和 `study-notes` 风格说明。公开运行时包默认递归排除 `styles/` 内的图片素材；确需带图时显式使用 `package_skill.py --include-example-images` 并核查授权。可根据需要随时新增风格包、替换颜色或取消。

**注意**：从示例中学习的是视觉规律，不是例图文字、实际软件内容、产品名称、用户名或品牌。禁止将别人的特定构图直接复制到新主题。公开分发前核查 `attribution.md`。

## 样式管理约定

- `styles/` 中的预设可分享，但新增社区或私人图片先核权利。
- 用户当前任务的 style card 可以保存在当前项目下，并不要求改动全局 styles。
- `personal/` 适合私有账号视觉与授权不明图片，默认不打包公开。
- 任何人的作品都不应被强制署上示例作者名字。
