# 共同交付与记录

- 主答卷 `OUTPUT_DIR/report.md`：当前请求的结果，来源/路径、哪些已检查、哪些需复核、当前可执行下一步与范围。
- `OUTPUT_DIR/state-answer.json`：用共同语义回答，建议键 `case_id,stage,active_constraints,next_action,changed_or_missing_paths,affected_activities,unaffected_activities,checkpoint_freshness,scientific_scope,source_tracking_limits,material_paths,notes`。未适用的字段留空并说明，其他等价字段可接受，不为模板命名给分。
- `OUTPUT_DIR/execution.json`：实际命令数组（argv/cwd/exit_code）、外层工具调用数、自报读取清单和完整SHA、网络调用0、违规/失败/补救、所写路径、实际未知设置null。A/C的项目内产物可自行选格式，但外部执行记录不能成为后续恢复者暗补的状态来源。
- `OUTPUT_DIR/inputs-and-artifacts.json`：本阶段实际输入/输出相对路径、完整SHA、字节数及不分发原始资料范围；不要把目录mtime当科学内容版本。

只读阶段可以运行不写项目的状态/恢复脚本；需要 Python 时用 `-I -B` 避免向项目写字节码。答卷应包含具体当前事实，不能只贴工具 passed 标记。工具只检测身份/状态，科学内容判断另报。
