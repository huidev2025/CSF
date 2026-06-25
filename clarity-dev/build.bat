@echo off
REM ============================================================
REM  Clarity V3 构建与部署 — 每次发布的唯一入口
REM ============================================================
REM
REM  用法: 在 clarity-dev/ 下双击 build.bat（或终端运行）
REM
REM  流程: 测试(397个) → PyInstaller打包 → 部署到生产环境
REM
REM  输出:
REM    dist\clarity.exe         ← 单文件可执行
REM    ..\csf-lite\clarity.exe  ← 生产环境（直接复制）
REM    logs\build-YYYYMMDD.log  ← 构建日志
REM
REM  体积优化（每次自动执行，无需手动干预）:
REM    1. 排除未用 Qt 模块: Qml/Quick/Sql/PrintSupport/Test
REM    2. 筛除 Qt 翻译文件(~10MB) + QML 引擎(~14MB)
REM    3. 构建数据收集中排除 .exe/.dll（防旧构建污染）
REM
REM  已知: Qt6 本体 ~140MB 是硬下限，CFG 保护使 UPX 不可用
REM        单文件 exe 比单目录 zip 大约 2-3 倍，但分发更简单
REM
REM  修改打包配置 → 编辑 clarity.spec
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ===========================================================
echo   Clarity V3 打包与部署
echo ===========================================================
echo.

REM 0. 路径
set "CLARITY_DIR=%~dp0"
set "CSF_LITE_DIR=%CLARITY_DIR%..\csf-lite"
set "LOG_DIR=%CLARITY_DIR%logs"

REM 1. Python 环境
if exist "%CLARITY_DIR%.venv\Scripts\python.exe" (
    set "PYTHON=%CLARITY_DIR%.venv\Scripts\python.exe"
) else (
    echo [ERROR] 找不到 .venv\Scripts\python.exe，请先配置虚拟环境
    pause
    exit /b 1
)

REM 2. 全量测试（不通过则中止）
echo [1/4] 运行全量测试 ^(期望 314 passed^)...
%PYTHON% -m pytest "%CLARITY_DIR%tests" -q
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 测试未通过，中止构建。请修复后重试。
    pause
    exit /b 1
)
echo       全量测试通过 ✅
echo.

REM 2. 版本号递增（自动 +0.0.1）→ 写 RELEASE.md + 收割 RELEASE_NOTES.txt
echo [2/4] 版本号递增...
pushd "%CLARITY_DIR%"
%PYTHON% bump_version.py
if %ERRORLEVEL% NEQ 0 (
    popd
    echo [ERROR] 版本号递增失败
    pause
    exit /b 1
)
REM 读取新版本号用于后续显示
for /f %%v in ('%PYTHON% bump_version.py --current') do set "NEW_VERSION=%%v"
popd
echo       新版本: v%NEW_VERSION% ✅
echo.

REM 3. PyInstaller 打包（单文件模式，配置在 clarity.spec）
echo [3/4] PyInstaller 打包 ^(单文件模式^)...
pushd "%CLARITY_DIR%"
%PYTHON% -m PyInstaller clarity.spec --noconfirm
if %ERRORLEVEL% NEQ 0 (
    popd
    echo [ERROR] PyInstaller 打包失败
    pause
    exit /b 1
)
popd
echo       打包完成 ✅
echo.

REM 4. 部署：复制单文件 exe 到生产环境
echo [4/4] 部署到生产环境...
if not exist "%CSF_LITE_DIR%" mkdir "%CSF_LITE_DIR%"
copy /Y "%CLARITY_DIR%dist\clarity.exe" "%CSF_LITE_DIR%\clarity.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 复制到生产环境失败
    pause
    exit /b 1
)
echo       生产环境就绪 ✅

REM 5. 构建摘要
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOGFILE=%LOG_DIR%\build-%date:~0,4%%date:~5,2%%date:~8,2%.log"
echo 版本: v%NEW_VERSION% > "%LOGFILE%"
echo 构建时间: %date% %time% >> "%LOGFILE%"
echo 生产环境: %CSF_LITE_DIR%\clarity.exe >> "%LOGFILE%"
for %%F in ("%CSF_LITE_DIR%\clarity.exe") do echo 文件大小: %%~zF 字节 >> "%LOGFILE%"

REM 计算体积
for %%F in ("%CSF_LITE_DIR%\clarity.exe") do set /a EXE_MB=%%~zF / 1048576

echo.
echo ===========================================================
echo   构建成功
echo ===========================================================
echo   版本:      v%NEW_VERSION%
echo   生产环境:  %CSF_LITE_DIR%\clarity.exe
echo   体积:      !EXE_MB! MB
echo   构建日志:  %LOGFILE%
echo   发布记录:  %CLARITY_DIR%RELEASE.md
echo ===========================================================
echo.
