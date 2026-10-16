# Visual Post Studio 开发约定

本仓库是 skill 的唯一修改入口。安装副本中的 `.installation.json` 记录源码路径、提交和文件哈希；安装副本只接受源码部署，不直接编辑。

## 每次修改

1. 先看 `git status --short --branch`，保留已有修改。根据问题阅读相关脚本、规则和测试。
2. 从具体失败入手，记录触发输入、实际结果、期望结果和证据。图文质量问题须看实际输出；不能从脚本通过推断中文、事实或审美合格。案例约定见 [DEVELOPMENT.md](DEVELOPMENT.md)，已知案例见 [development/cases.md](development/cases.md)。
3. 小范围修复。生产规则放在 `SKILL.md` / `references/`；开发约定放在本文件和 `DEVELOPMENT.md`，不塞入生产步骤。
4. 修改后必须保存本次明确列出的文件：

```bash
bash scripts/save.sh "<area>: <what changed> — <why>" <file>...
# 有用户可感知的变化时，在文件列表前加 --note "一句变更说明"
```

Windows 可用 `python -B -X utf8 scripts/maintain.py save`，参数相同。不得用 `git add -A` 收集其他工作；已经暂存的指定文件需先明确处理，脚本不会替用户提交它们。

保存脚本验证 `HEAD + 本次文件` 的快照并运行回归测试，通过后只提交这些文件，再同步已登记的安装副本。候选验证失败不改真实 index、CHANGELOG 或安装副本；提交失败还原脚本自己的暂存和自动日志，保留工作文件。同步失败时提交仍保留，解决后运行 `python scripts/maintain.py sync`。

## 版本与发布

- 提交信息用具体的 `<area>: <what changed> — <why>`，如 `qa`、`skill`、`style`、`packaging`、`workflow`；hook 检查格式。
- 用户可感知的行为变化记录到 `CHANGELOG.md` 的 `Unreleased`。正式发布时更新 `SKILL.md` 的 `metadata.version`、README/QUICKSTART 标题和包名示例，并将日志归入该版本及日期。
- `python scripts/maintain.py release --out <仓库外目录>` 从已提交版本生成公开包、开发包和验证记录。已有同名发布文件不覆盖。
- 公开包只含生产资源、明确列出的生产脚本和 UI 元数据；不包含开发工具、案例、测试、安装收据或默认示例图片。
