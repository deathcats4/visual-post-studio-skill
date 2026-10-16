# 已知失败与验收队列

## 已修复的独立审查问题

来源：3.0.0 上传开发包的独立审查。以下问题在 3.0.1 修复，提交 `34f968c`。证据是可复现的脚本行为及对应回归，检查范围不包括图片审美、中文质量或实际生成模型表现。

| ID | 触发与原错误 | 修复后的要求 | 回归位置 | 状态 |
| --- | --- | --- | --- | --- |
| QA-001 | 只有合理 PNG 文件头、CRC 损坏或 JPEG 截断，仍可能通过文件验收 | 严格 QA 必须完整解码；交付复核再次检查当前文件 | `test_regressions.py` 的 `test_strict_qa_rejects_header_only_png`、`test_strict_qa_rejects_bad_png_crc_and_truncated_jpeg`、`test_final_verifier_rechecks_image_decode_even_with_matching_hash` | passed：自动回归 |
| QA-002 | 正式任务缺少明确页数，最终检查无法发现缺页 | 严格验收或 complete 状态要求确切正整数页数；草稿允许未定页数 | `test_strict_qa_requires_exact_positive_integer_page_count`、`test_draft_may_keep_page_count_unresolved` | passed：自动回归 |
| PKG-001 | 公开打包只去掉一层 examples，嵌套或其他风格目录图片仍泄露 | 递归去掉风格内常见图片，清理相应引用；显式带图包保留 | `test_public_package_excludes_nested_and_non_example_style_images`、`test_reference_image_package_keeps_nested_assets_and_metadata` | passed：自动回归 |
| INPUT-001 | 无效 pixels 或后续 reference 路径报错后留下半成品目录，修正后无法重试 | 输出目录创建前验证全部输入，失败后可直接重试 | `test_invalid_pixels_leave_no_project_and_corrected_retry_succeeds`、`test_invalid_second_reference_leaves_no_style_and_retry_succeeds` | passed：自动回归 |

测试文件见 [tests/test_regressions.py](../tests/test_regressions.py)。

## 保存和安装机制

3.0.2 的回归见 [tests/test_maintenance.py](../tests/test_maintenance.py)：待提交快照不能依赖未列出的文件；其他暂存/未跟踪工作不被提交；验证或提交失败不改用户工作；部署只使用已提交内容；安装改动阻止覆盖；开发文件不进入运行时；旧发布文件不覆盖。

### PKG-002：测试缓存混入开发包

- 来源：本轮 3.0.2 发布后的逐文件核对，初始提交 `ca59970`。运行 48 项回归均通过，但开发 ZIP 比 Git 提交多出 `scripts/__pycache__/qa_images.cpython-311.pyc`；其他源码字节一致。
- 原因：发布前在快照中执行测试，测试启动的子进程产生缓存；随后遍历整个快照打包，把新文件一并收录。仅给测试主进程加 `-B` 没有约束子进程。
- 要求：开发包内容必须逐文件对应记录的 Git 提交；运行时包也不能包含测试生成或改写的内容。
- 修复：开发 ZIP 直接取自固定提交的 `git archive`；运行时从新的同一提交快照构建；测试环境设置 `PYTHONDONTWRITEBYTECODE=1` 并传给子进程。
- 回归：`test_release_uses_committed_source_and_preserves_old_artifacts` 刻意创建缓存、临时文件和改写 README，然后核对两个包及完整 Git 文件内容。该案例只验证发布边界，不评价生成图片质量。
- 本轮错误包保存在本机 `.local/rejected-releases/initial-v3.0.2/`，用于追溯；不进入正式发布或源码提交。

## 下一批实际图文验收

这些是待运行案例，不是已完成的效果证明。运行后单独建记录，写入实际图片及审阅证据。

| ID | 输入与任务 | 验收重点 | 状态 |
| --- | --- | --- | --- |
| VIS-001 | 同一主题的 5–6 页中文教程，包含短标题及较长说明 | 独立页文件、文字正确、可读性、段落密度、跨页视觉一致性 | pending |
| VIS-002 | 分别完成生活教程、软件操作和科学知识图文；软件截图与科学事实使用实际来源 | 跨主题适应、证据忠实、版式变化与真实 UI，不复制模板中的账号和内容 | pending |
| VIS-003 | 在已批准的一套图中只修改第 4 页标题区域 | 未指定页文件哈希不变；第 4 页非目标区域实际审阅；修改后重新 QA | pending |
| VIS-004 | 对同一 brief 只要分镜，随后明确授权直接生成 | 规划阶段不擅自生图；授权后完成真正的独立图片输出；不重复要求已给授权 | pending |
| VIS-005 | 基于用户指定的 Pyzotero 官方文档与视频字幕制作操作图文 | 先覆盖完整来源流程；封面聚焦实际主题；每页由图像模型直接生成含字成品；真实 UI 有来源 | pending：规则已修订，尚未用新图组复验 |
