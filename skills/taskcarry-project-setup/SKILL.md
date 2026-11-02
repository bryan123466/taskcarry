---
name: taskcarry-project-setup
description: Connect an existing project to TaskCarry, inspect prerequisites, or install and remove project-scoped integration files. Use for explicit project onboarding or tool maintenance.
---

# Project setup / 项目接入

Use the existing local AI host with the TaskCarry engine; no separate model server is required. Establish the exact project directory from the user's task. The current setup generates Codex integration files. Other hosts require their own configuration and instruction-loading verification; CLI/MCP availability alone is not proof of host compatibility.

Start with the fixed installed interpreter: `python -I -X utf8 -m taskcarry --project <directory> setup --json '{"mode":"preview"}'`. Inspect the proposed files and conflicts. Within the user's requested onboarding scope, install with `mode: install`. This creates four project-local skills and `.taskcarry/codex.mcp.toml`; it does not activate the fragment or edit live Codex configuration. Show the fragment for the user's chosen configuration workflow. Preserve existing `AGENTS.md` and configuration.

Use `init` only when creating this project's governance state, then `doctor` to inspect prerequisites. Git is needed only for Git operations. The fixed project used to launch MCP must match the intended governance project. `taskcarry_workspace` registers explicit workspaces; it is not permission to read all local repositories.

Report the actual installed version, project binding and connection checked in the current chat. When onboarding includes starting governance, use `taskcarry-governance-reconcile` for one bounded pass with the same tools a later schedule will use. If there are no deliveries, report readiness or the concrete setup gap; never create sample work to fill a report. Reuse this result when configuring a schedule rather than triggering an extra Automation. Reports remain normal AI/host chat output, not a separate state store or service.

Keep the installed governance runtime separate from its source checkout. For an installed wheel, invoke its fixed interpreter with `-I -X utf8 -m taskcarry`, including when running setup from a source directory. Generated MCP fragments use isolated UTF-8 startup and explicitly pin the package selected by setup; they fail if that package is unavailable. Setup run explicitly against development source pins that source, so it is a development connection, not an installed governance runtime. Review `doctor.runtime` through the actual host for the imported package and managed setup; it describes this process, not proof that another already-running MCP process loaded the same version. Existing fragments remain unchanged until an authorized setup preview/install update; manually activated host configuration needs separate review and reload. Do not recreate project state during a tool upgrade. A pending setup intent may be resumed by repeating the same install with the same candidate; do not delete the intent or overwrite a changed user file. Multiple independent control stores may use explicit distinct `server_name` values; each still has one receiving baseline.

For removal, `setup` with `mode: uninstall` removes only unchanged managed files. Modified files, governance data and manually activated configuration are retained and reported. Do not remove these by force.

中文：接入仅影响用户指定项目。预览后按既有授权安装；MCP 片段需明确配置才会生效，不宣称已自动连接。诊断通过不代表原生 Codex 界面已验收；如实报告实际测试到的层次。
