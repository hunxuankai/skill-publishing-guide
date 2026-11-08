# 维护、安装与本地版本

修改 `skills/skill-publishing-guide/`，同步 `metadata.version`、README 和包内维护页。资料只有实际复核后才更新核验日期。纯仓库维护工具/记录变化不要求升级本体；已发行版本、标签和包不覆盖。

## 工具来源与依赖

校验器和安装器复用 `software-testing-router` 仓库 `43f4653` 所含的已验证实现，仅将固定技能名/默认路径适配为 `skill-publishing-guide`。各仓库工具独立存在，不依赖兄弟目录；后续修复需检查相应副本。

`requirements-dev.txt` 固定校验所需依赖，`requirements-test.lock` 记录本次完整测试环境。运行包没有这些依赖，也不执行自动上传。结构检查不能替代对平台事实和真实使用的判断。

## 每次修改

1. 检查工作区，阅读相关平台一手资料并保留证据等级。
2. 修改源码及版本记录，运行包校验、受影响的工具测试和必要的独立使用评估。涉及介绍机制时，复核正文来源、实际入口和版本/包/简介/概述的分别验收，不以只读观察冒充保存或发布实测。
3. 检查完整 diff 与 `git diff --check`，确认没有个人配置、凭据、真实回执或越界引用进入包。
4. 提交并合并主分支；需要更新本机副本时先 DryRun，再安装并比较文件哈希。

## 更新与回滚

安装脚本默认目标为 `~/.agents/skills/skill-publishing-guide/`，`-SkillsRoot` 接收父目录。预览不写目标/备份；相同内容不改写。更新会把完整旧包保存在本机应用数据目录 `SkillBackups/skill-publishing-guide/<time-guid>/skill-publishing-guide/`。

回滚时读取实际备份路径并校验该完整包。先保存当前安装副本到技能发现目录之外，再恢复所选旧包，核对完整文件清单和哈希。移动前确认解析后的源/目标都在明确指定的安装/备份范围内，并拒绝链接、路径重叠及未知现存目标。不要删除用户文件解决冲突；异常时保留两份可恢复内容并报告。

## 从已验证提交打包

在干净主分支上执行。以下为 PowerShell 7 本地发行示例，不推送或公开发布：

```powershell
$ErrorActionPreference = 'Stop'
$pending = git status --porcelain
if ($LASTEXITCODE -ne 0 -or $pending) { throw 'A clean checkout is required' }
& .venv/Scripts/python.exe tools/check_skill.py
if ($LASTEXITCODE -ne 0) { throw 'Package validation failed' }
$releaseVersion = '1.2.3'
$releaseTag = 'v' + $releaseVersion
$existingTag = git tag --list $releaseTag
if ($LASTEXITCODE -ne 0 -or $existingTag) { throw 'Tag already exists or lookup failed' }
$releaseCommit = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve release commit' }
$base = 'skill-publishing-guide-' + $releaseVersion
$zipPath = Join-Path 'dist' ($base + '.zip')
$shaPath = Join-Path 'dist' ($base + '.sha256')
$commitPath = Join-Path 'dist' ($base + '.commit.txt')
foreach ($path in @($zipPath, $shaPath, $commitPath)) {
    if (Test-Path -LiteralPath $path) { throw 'Release artifact already exists' }
}
New-Item -ItemType Directory -Path 'dist' -Force | Out-Null
git -c core.autocrlf=false archive --format=zip --prefix=skill-publishing-guide/ --output=$zipPath "${releaseCommit}:skills/skill-publishing-guide"
if ($LASTEXITCODE -ne 0) { throw 'Archive failed' }
$candidate = Join-Path 'dist' ('candidate-' + [Guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath $zipPath -DestinationPath $candidate -ErrorAction Stop
$candidateSkill = Join-Path $candidate 'skill-publishing-guide'
$manifest = & .venv/Scripts/python.exe tools/check_skill.py $candidateSkill --json
if ($LASTEXITCODE -ne 0) { throw 'Candidate validation failed' }
if (($manifest | ConvertFrom-Json).version -cne $releaseVersion) { throw 'Version mismatch' }
$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
($hash + '  ' + [IO.Path]::GetFileName($zipPath)) | Set-Content -LiteralPath $shaPath -Encoding ascii
$releaseCommit | Set-Content -LiteralPath $commitPath -Encoding ascii
git tag -a $releaseTag $releaseCommit -m "skill-publishing-guide $releaseVersion"
if ($LASTEXITCODE -ne 0) { throw 'Tag creation failed' }
```

另核对 ZIP 内只有预期单个技能目录、文件字节与来源提交一致，标签解析到该提交。保留 `.sha256`、`.commit.txt` 与检查结果。真实外部发布属于另一个明确的发布任务，不因生成本地包自动执行。

## GitHub 公开快照与本地历史

首次原历史推送遭 GH007 邮箱隐私保护拒绝。当前公开仓库采用使用 noreply 邮箱的独立 Git 快照，文件 tree 与已验证本地提交相同，原历史和本地发行标签保留；来源映射见发布附件及 [本轮结果](publications/2026-11-08-v1.2.3-results.md)。

后续在唯一维护源码修改并提交 main，再在受控、干净的公开 Git 副本更新完整跟踪文件并比较 tree，提交/推送其 main。不要推送原私有历史或强行覆盖已公开标签。当前本机公开 Git 副本在 `.artifacts/publication-20261108-mp4htbtt/public-source/`；需要重建时从已验证公共仓库克隆到新的隔离目录，校对账号、默认分支与来源后再同步。原维护仓库初始没有远程；本轮临时加入的、与本地历史不一致的 origin 在公开同步验证后移除，公开 Git 副本保留正式远程。
