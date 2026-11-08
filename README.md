# skill-publishing-guide

版本 **1.2.3**。指导代理按目标平台准备和发布 Agent Skill，区分 GitHub 链接、ZIP、CLI、目录 PR，以及接收、审核和公开结果；发布包、简介和概述分别准备与验收。[本版本记录](docs/releases/v1.2.3.md)；[1.2.2 记录](docs/releases/v1.2.2.md)；[1.2.1 记录](docs/releases/v1.2.1.md)；[1.2.0 记录](docs/releases/v1.2.0.md)；[1.1.1 记录](docs/releases/v1.1.1.md)；[1.1.0 记录](docs/releases/v1.1.0.md)；[首版本地交付记录](docs/releases/v1.0.0.md)。

这是发布指导，没有自动向所有市场上传的运行脚本。代理按用户选择的平台、已有工具和授权执行。

1.2.3 已在 [GitHub Release](https://github.com/hunxuankai/skill-publishing-guide/releases/tag/v1.2.3)、[skills.sh](https://www.skills.sh/hunxuankai/skill-publishing-guide/skill-publishing-guide) 和 [ClawHub](https://clawhub.ai/hunxuankai/skill-publishing-guide) 公开；腾讯 SkillHub、SkillHub.club、Skillstore 和 Agensi 已提交待审。安全评估警告、文件核对和未完成项见 [发布结果](docs/publications/2026-11-08-v1.2.3-results.md)。VoltAgent 的真实社区使用门槛尚未满足。

## 平台、提交方式与核验范围

目前覆盖 8 个渠道。腾讯 skillhub.cn 的概述机制、发布/更新与编辑入口，以及 Agensi、SkillHub.club 的实际网页表单于 **2026-11-08** 核对；其他渠道、腾讯此前文件过滤及既有 CLI 本地运行依据保留 **2026-11-07** 的核验记录。下表区分文档、界面和本地运行，不代表已逐个平台完成真实发布测试。

| 平台 | 提交或收录方式 | 已核对的范围与限制 |
| --- | --- | --- |
| [GitHub](skills/skill-publishing-guide/references/github.md) | 源码仓库、版本标签、Release 附件 | 官方 CLI 文档 |
| [skills.sh](skills/skill-publishing-guide/references/skills-sh.md) | GitHub 来源安装及安装遥测触发收录 | 官方 FAQ/CLI；收录与网页刷新分别核验 |
| [腾讯 SkillHub（skillhub.cn）](skills/skill-publishing-guide/references/skillhub-cn.md) | 本地文件/ZIP，或绑定 GitHub 后导入；简介与自定义概述分别核对 | 官方教程、实际发布/更新和概述编辑器、当前客户端与公开只读响应；未保存、上传或提交，翻译重建/缓存时限仍未确认 |
| [SkillHub（skillhub.club）](skills/skill-publishing-guide/references/skillhub-club.md) | 网页导入 ZIP/Markdown/文本，或官方 CLI 的 `init → push → publish`；已有公开 GitHub 来源的索引单独核对 | 已读取登录后的网页表单及文件选择器属性；CLI 0.1.9 本地运行已实测；实际上传、详情页资源补充和公开未验证 |
| [Skillstore（skillstore.io）](skills/skill-publishing-guide/references/skillstore.md) | 提交 GitHub 仓库或目录 URL | 官方说明与网页；导入范围和审核结果需核对 |
| [ClawHub（clawhub.ai）](skills/skill-publishing-guide/references/clawhub.md) | 官方 CLI 提交本地 skill 文件夹 | 官方 CLI/发布文档；有 MIT-0 分发条件 |
| [VoltAgent](skills/skill-publishing-guide/references/community-directories.md) | 向社区目录提交收录 PR | 官方贡献规则；要求已有真实社区使用 |
| [Agensi](skills/skill-publishing-guide/references/agensi.md) | 正式网页提交 ZIP；代理提交采用另一个受限流程 | 当前已登录发布页、字段和可选区域已实际读取；打包/审核等规则有官方文档依据；实际上传、审核和公开未验证 |

`skillhub.cn` 与 `skillhub.club` 是独立平台，账号、CLI、包格式和审核规则分别核对。受限渠道的确认方法写在对应参考页；[核验说明](skills/skill-publishing-guide/references/verification-and-recovery.md)区分入口恢复、流程核对与目标版本公开。

[介绍内容同步](skills/skill-publishing-guide/references/introduction-content.md) 区分包内正文、SKILL.md description、GitHub README、平台简介、详情概述与翻译/展示副本。发布前备好与新版功能、系统支持、依赖和真实验证范围一致的文案，提交时核对实际接收内容，发布后分别验收版本、下载包、简介和概述。手动处理材料必须包含完整可复制文案和实际概述操作步骤。

## 源码与使用

唯一安装单元是 [skills/skill-publishing-guide](skills/skill-publishing-guide/SKILL.md)。主入口和参考页以中文编写，按所选平台加载；既有授权、语言、许可和发布范围优先。

可下载 Release 的单技能 ZIP；也可用本轮核对的 CLI 版本从公开仓库安装指定技能：

```powershell
npx --yes skills@1.7.6 add hunxuankai/skill-publishing-guide --skill skill-publishing-guide --agent codex --copy
```

此命令读取当前 main；需要不可变的 1.2.3 文件时使用 Release 附件及其来源/哈希记录。

示例请求：

- “使用 skill-publishing-guide，为这个多技能仓库中的一个 skill 准备 skills.sh 和 Skillstore 发布材料。”
- “这份 ZIP 要上传腾讯 SkillHub，帮我核对结构、版本和审核结果。”
- “为这个 skill 准备 skillhub.club 的 CLI 发布材料，检查实际上传清单是否完整。”
- “核对 skillhub.club 网页导入表单，为这个 skill 准备单技能 ZIP，保留未验证的文件限制和公开步骤。”
- “平台返回成功但公开页还是旧版本，判断本次发布到了哪一步。”
- “版本号已公开，但简介或概述仍旧，分别记录状态并准备完整文案和已核实的修改步骤。”

运行包只有 Markdown/YAML，可由支持 Agent Skills 的宿主读取。它不依赖本仓库维护工具、其他已安装 skill 或预配置的个人账号。调用平台 CLI、浏览器或 API 时使用宿主已有工具及用户已授权的会话。

## 本机安装与维护

维护工具需要 Python 3.10+、PowerShell 7、PyYAML、markdown-it-py/mdurl；依赖版本已固定。下面使用独立测试环境，`uv` 可替换为等价的 Python venv/pip 操作：

```powershell
uv venv --python 3.11.13 .venv
uv pip sync --python .venv/Scripts/python.exe requirements-test.lock
& .venv/Scripts/python.exe tools/check_skill.py
pwsh -NoProfile -File tools/install-local.ps1 -Python .venv/Scripts/python.exe -DryRun
pwsh -NoProfile -File tools/install-local.ps1 -Python .venv/Scripts/python.exe
```

每条命令成功后再继续；脚本支持指定解释器和 `-SkillsRoot <技能父目录>`。默认安装到当前用户 `~/.agents/skills/skill-publishing-guide/`。先预检，更新前备份，复制后校验；有未知文件或链接时停止，不删除绕过。

`tools/check_skill.py` 用于维护本指南自身，不能当作所有第三方 skill 的通用文件布局规则。实际发布其他项目时优先采用其已有校验器及目标平台要求。

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
& .venv/Scripts/python.exe -m pytest tests -q
git diff --check
```

目录中 `tools/`、`tests/`、`docs/` 和依赖文件不进入安装包。版本规则、打包和回滚见 [维护说明](docs/maintenance.md)；资料来源见 [来源与维护](skills/skill-publishing-guide/references/sources-and-maintenance.md)，实际验证见 [验证记录](docs/validation.md)。

本项目按 [MIT 许可](LICENSE) 分发。1.2.3 的实际提交、审核和公开状态见 [发布记录](docs/publications/2026-11-08-v1.2.3.md)，简介与完整概述分别准备和核验。
