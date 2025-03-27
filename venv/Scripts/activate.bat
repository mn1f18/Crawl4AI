@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

set VIRTUAL_ENV=%~dp0..

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT (
    set "PROMPT=%_OLD_VIRTUAL_PROMPT%"
)

if defined _OLD_VIRTUAL_PYTHONHOME (
    set "PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%"
)

rem 移除旧的path设置
if defined _OLD_VIRTUAL_PATH (
    set "PATH=%_OLD_VIRTUAL_PATH%"
) else (
    set "_OLD_VIRTUAL_PATH=%PATH%"
)

rem 将虚拟环境路径添加到PATH最前面
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"

rem 获取虚拟环境目录名作为提示符前缀
for %%d in ("%VIRTUAL_ENV%") do set "ENV_NAME=%%~nxd"
set "VIRTUAL_ENV_PROMPT=(%ENV_NAME%) "

rem 保存旧的设置以便于deactivate
if defined PYTHONHOME (
    set "_OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%"
    set PYTHONHOME=
)
if defined PROMPT (
    set "_OLD_VIRTUAL_PROMPT=%PROMPT%"
    set "PROMPT=%VIRTUAL_ENV_PROMPT%%PROMPT%"
)

rem 恢复旧的代码页设置
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)
