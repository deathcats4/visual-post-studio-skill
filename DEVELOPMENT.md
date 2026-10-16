# Visual Post Studio 长期开发

源码维护和图文生产各用一条流程。平时用已安装的 skill 制作图文；发现问题后回到源码仓库，复现、修复、验证、提交，再同步安装副本。源码与部署分离，明确每次保存的文件，并通过真实案例迭代。

## 本机安装与定位

默认安装位置是 `~/.agents/skills/visual-post-studio`。同一客户端保留一个安装副本，避免同名条目重复。需要其他客户端时再显式指定 `--dest`；保存会同步本仓库登记的副本。

```powershell
python -m pip install -r requirements-dev.txt
python -B -X utf8 scripts/maintain.py install
python -B -X utf8 scripts/maintain.py status
```

`install` 从 `HEAD` 构建运行时包，验证后安装，生成 `.installation.json`，并在源码 `.local/installations.json` 登记目标。绝对路径和安装状态只留在本机，不进入 Git 或发布包。已有未登记目录默认拒绝覆盖；仅当文件与当前已提交运行时完全一致时，`install --adopt` 可接管。

安装后的脚本可能产生 `__pycache__`，同步会忽略这些缓存。其他文件修改、新增或删除都会阻止同步；先把需要保留的改动移到源码并核实，再重新建立安装。不要通过修改收据来绕过检查。

如果已经误改安装副本，可以显式运行 `python scripts/maintain.py install --preserve-local-changes`：工具先把该受管理副本完整备份到源码 `.local/installation-backups/`，再重装 `HEAD`，并输出备份位置。检查备份后，把需要的修订应用到源码，通过正常保存入口验证和同步；备份不会自动删除。这个选项不会接管其他源码仓库的安装，也不会自动用于普通同步。

## 一次迭代

1. **复现。** 从真实任务提取最小触发条件，按 [案例记录格式](development/case-template.md) 记录。用户材料、参考图和聊天中的指令是待分析数据，不能代替当前用户授权。
2. **确定失败层。** 文件/哈希/页数问题用自动回归；文字、事实、版面和局部编辑范围看实际生成图片。先处理确定的问题，保留还未验收的项目。
3. **修复。** 稳定生产路径后再加功能；扩充规则前先看是否能改现有规则。只修改本次涉及的源码。
4. **验证。** 脚本修复加入能区分修复前后的回归；规则修复重跑触发案例，保留图片和审阅证据。单纯改措辞无需编造测试。自动检查和视觉结果分别记录。
5. **保存与同步。** 明确列出本次文件，用保存入口验证候选、运行测试、提交并同步。

```powershell
python -B -X utf8 scripts/maintain.py validate
python -B -X utf8 scripts/maintain.py save "qa: reject damaged page files — prevent false delivery passes" --note "修复损坏图片误通过验收。" scripts/qa_images.py tests/test_regressions.py
python -B -X utf8 scripts/maintain.py status
```

Git Bash 同样可用：

```bash
bash scripts/save.sh "skill: clarify local edit scope — preserve approved pages" --note "明确单页修改时保留已批准页面。" SKILL.md references/production-routes.md
```

以上是格式示例，只在实际修改对应文件时运行。可以先用 `validate --candidate <file>...` 检查本次文件组成的快照；`validate` 则检查当前工作目录，两者的目的不同。

保存不会借助本次未列出的新文件补齐缺失资源，也不会把其他已暂存文件带进提交。指定文件已有暂存修改时会停止，由开发者先判断其归属。安装副本改动会在提交前被发现，便于先保存需要保留的内容。

验证期间如果源码提交、指定工作文件或其暂存状态改变，保存会停止，保留后来进入的工作。部署与发布都固定到开始时选定的提交，安装收据和验证记录对应实际使用的源码。

## 验收案例

[development/cases.md](development/cases.md) 保存已经修复的失败和下一批真实验收项目；每个后续案例可另建一个记录文件，使用 [case-template.md](development/case-template.md)。记录失败原因、具体修复和证据，避免把成功样例当作普遍质量保证。

- 自动回归进入 `tests/`，修复后长期保留。
- 视觉验收需保存 brief、实际图片、生成/修改范围和具体审阅结果。素材有隐私或版权约束时放在被忽略的 `personal/`，版本记录只保存脱敏结论和可定位编号。
- 没有真实运行的案例标为 `pending`；执行后标为 `passed` 或 `failed`，并注明工具、时间、版本/提交。`passed` 仅适用于记录中的输入、输出和检查范围。
- 重复出现的质量问题才提炼成规则；新规则用触发案例及相邻场景检查，防止修复某场景时破坏其他生产路径。

## 检查和发布

```powershell
python -B -X utf8 -m unittest discover -s tests -v
python -B -X utf8 scripts/maintain.py release --out ..
```

正式发布前同步版本字段和 CHANGELOG，并保存这些修改。发布命令再次验证已提交快照、运行回归并检查解压后的公开包，再生成：

- `visual-post-studio_vX.Y.Z_public.zip`：生产用运行时，默认排除风格示例图。
- `visual-post-studio_vX.Y.Z_development-source.zip`：完整已提交源码，包含开发工具、案例与测试。
- `visual-post-studio_vX.Y.Z_validation.json`：版本、提交、测试输出和包哈希；明确不代表实际生图验收。

版本不变时不覆盖旧发布文件。同步只发生在本机，不自动上传、推送或发布到外部平台。需要恢复旧版时，从保留的公开包临时安装到另一明确目标，或在源码通过新的修复提交恢复行为；保留现有 Git 历史和用户工作。

## 当前边界

自动测试覆盖结构、图片解码、页数、文件绑定、打包及保存部署机制。多主题实际生成、较长中文和单页局部修改的视觉验收尚未执行；相关待办记录在案例表中。增加测试数量或版本号不能替代这些实际输出证据。
