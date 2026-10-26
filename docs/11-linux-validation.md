# 跨平台复查与实际验收

核心为 Windows、macOS 与 Linux 提供本地项目读写、技能接入、升级和只读恢复。不同系统的文件锁、路径身份、目录发布和文本编码需要实际操作系统验证；实现了兼容分支与该平台已运行通过是两项记录。

macOS/Linux 保留目录文件描述符与 POSIX 写锁。Windows 使用原生目录／文件句柄与非阻塞文件范围锁，在访问期间保持目录身份；拒绝内部重解析点（junction、符号链接和云盘占位符）、设备名及歧义路径。Windows 项目应选普通本地目录，例如 `C:\Research\my-project`；网络盘、云同步占位路径与管理员恶意替换不在本轮完整保证范围。外部程序占用文件时，Windows 可能拒绝改名或替换；遇到错误应先关闭占用该文件的程序再重试，不通过强制覆盖解决。

## 当前结果入口

软件只维护当前一份。[当前核验记录](../evals/current/latest.json)记录本轮真正执行的解释器与平台；最终ZIP的独立验收由 `dist/release-validation.json` 提供。旧发行阶段的平台记录已从包内移除，未在当前记录中列为成功的环境不视为本轮已测。

源输入、已测软件指纹和最终归档身份应分别绑定。测试后若只新增说明或验收元数据，记录其差异；若软件、指导或测试代码变化，需要重新执行相应检查，不能把旧成功结果改名后继续使用。

## 在自己的Linux上复查

维护检查使用源码仓库或 GitHub 的源码归档，进入 `research-workflow-template`，使用 Python 3.11 或更新版本：

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
```

Windows PowerShell 对应命令为：

```powershell
py -3 -X utf8 -B tools/check_core.py --test-timeout 600
py -3 -X utf8 -B tools/release_package.py check
```

最终用户 ZIP 只带运行资源，排除这些开发检查工具和测试。普通使用者按[用户包指南](user-package-guide.md)初始化、接入和运行项目内的 `check`／`resume` 即可。

`--test-timeout`设置完整单元/CLI套件的秒数上限，默认180。超时返回失败JSON和有限的捕获内容，`timed_out=true`、套件退出码为null，命令退出1；部分输出不表示套件完成。非法或非有限时限由参数解析器拒绝。

## 单独记录的边界

本地 Linux ARM64、不同 C 库、GitHub 托管 Ubuntu、macOS 和 Windows 分别记录。CI 配置覆盖三种系统及 Python 3.11／3.14，共六组环境；配置存在不表示本次提交已通过。没有取得相应成功结果之前，当前核验仍须明确记为未执行或待确认。

一次本地测试不代表托管 CI 已执行，也不覆盖网络文件系统、所有发行版、断电恢复或宿主界面技能触发。两套 Python 若使用同一内核或用户态，也应明确说明。

CI 从实际构建并校验的源码 ZIP 解压到临时目录，以独立 HOME／USERPROFILE 和临时目录重新运行完整检查和来源清单检查，另对用户 ZIP 做初始化、技能接入、登记、搬迁与恢复的真实运行；无需个人技能包、账户或额外 Python 依赖。UTF-8 与 Git 提交中的换行字节显式保留，避免把编码或 CRLF 变化误当作内容升级。

需要临时Linux运行器时，运行器、内核、用户态和解释器应保留其来源与校验摘要，放在包外隔离目录中，不随本工具包再分发或套用模板MIT许可。对所用网络、宿主共享和磁盘配置按真实情况记账；测试结束后关闭运行器。
