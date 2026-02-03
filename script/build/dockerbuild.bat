@echo off
REM ============================================================================
# 知识库智能体 - Windows Docker镜像构建脚本
# File    : dockerbuild.bat
# Purpose : 在Windows系统上构建Docker镜像，支持4个版本
#           版本说明：
#             v1: 云LLM + 本地向量（约3.5GB，需要torch）
#             v2: 云LLM + 云端向量（约800MB，轻量版）
#             v3: 本地LLM + 本地向量（约3.5GB，需要torch）
#             v4: 本地LLM + 云端向量（约800MB，轻量版）
# Usage   : dockerbuild.bat [version] [options]
# Example : dockerbuild.bat v1
#           dockerbuild.bat v2 --no-cache --push
# ============================================================================

setlocal enabledelayedexpansion

REM ============================================================================
# 1. 初始化：加载通用函数库
# ============================================================================
call "%~dp0common.bat" init
if errorlevel 1 (
    echo [ERROR] 无法加载通用函数库
    pause
    exit /b 1
)

REM ============================================================================
# 2. 参数解析（支持交互式选择）
# ============================================================================
set "VERSION=%~1"
set "NO_CACHE="
set "PUSH_IMAGE="
set "LLM_PROVIDER=zhipuai"

REM 如果没有参数，显示交互式菜单
if "%VERSION%"=="" goto :interactive_menu

REM 解析命令行选项
:parse_args
shift
if "%~1"=="" goto :parse_done
if /I "%~1"=="--no-cache" set "NO_CACHE=--no-cache"
if /I "%~1"=="--push" set "PUSH_IMAGE=true"
if /I "%~1"=="--help" goto :show_usage
shift
goto :parse_args

:parse_done
goto :validate_version

REM ============================================================================
# 3. 交互式菜单（用户友好特性）
# ============================================================================
:interactive_menu
cls
echo ========================================
echo   知识库智能体 - 镜像构建
echo ========================================
echo.
echo 请选择要构建的版本:
echo.
echo   [1] v1 - 云LLM + 本地向量 (约3.5GB)
echo   [2] v2 - 云LLM + 云端向量 (约800MB)
echo   [3] v3 - 本地LLM + 本地向量 (约3.5GB)
echo   [4] v4 - 本地LLM + 云端向量 (约800MB)
echo.
set /p CHOICE="请输入选项 (1-4): "

if "%CHOICE%"=="1" set "VERSION=v1"
if "%CHOICE%"=="2" set "VERSION=v2"
if "%CHOICE%"=="3" set "VERSION=v3"
if "%CHOICE%"=="4" set "VERSION=v4"

if "%VERSION%"=="" (
    echo [ERROR] 无效的选项
    pause
    exit /b 1
)

echo.
set /p CONFIRM="确认构建版本 %VERSION%? (Y/N): "
if /I not "%CONFIRM%"=="Y" exit /b 0

echo.
set /p PUSH_CHOICE="构建后是否推送到镜像仓库? (Y/N): "
if /I "%PUSH_CHOICE%"=="Y" set "PUSH_IMAGE=true"

echo.
set /p CACHE_CHOICE="是否使用构建缓存? (Y=使用/N=不使用): "
if /I "%CACHE_CHOICE%"=="N" set "NO_CACHE=--no-cache"

REM ============================================================================
# 4. 版本验证（Guard Clauses）
# ============================================================================
:validate_version
call "%~dp0lib\version.bat" validate "%VERSION%"
if errorlevel 1 (
    echo [ERROR] 无效的版本: %VERSION%
    echo [INFO] 支持的版本: v1, v2, v3, v4
    call "%~dp0lib\version.bat" list
    pause
    exit /b 1
)

REM ============================================================================
# 5. 获取版本配置信息
# ============================================================================
call "%~dp0lib\version.bat" get_config "%VERSION%"

REM ============================================================================
# 6. 显示构建配置摘要
# ============================================================================
call "%~dp0common.bat" print_separator "构建配置摘要"
echo   版本        : %VERSION% - %VERSION_DESC%
echo   镜像标签    : %IMAGE_TAG%
echo   本地向量    : %INSTALL_LOCAL_EMB%
echo   默认LLM     : %LLM_PROVIDER%
echo   使用缓存    : %NO_CACHE%
echo   推送镜像    : %PUSH_IMAGE%
call "%~dp0common.bat" print_separator
echo.

REM ============================================================================
# 7. 环境检查
# ============================================================================
echo [CHECK] 检查Docker环境...
call "%~dp0common.bat" check_docker
if errorlevel 1 (
    echo [ERROR] Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)

echo [OK] Docker环境正常
echo.

REM ============================================================================
# 8. 执行构建
# ============================================================================
echo [BUILD] 开始构建Docker镜像...
echo.

cd /d "%BACKEND_DIR%"

REM 构建镜像
docker build %NO_CACHE% ^
    --build-arg "IMAGE_VERSION=%VERSION%" ^
    --build-arg "INSTALL_LOCAL_EMB=%INSTALL_LOCAL_EMB%" ^
    -t "%IMAGE_TAG%" ^
    .

if errorlevel 1 (
    call "%~dp0lib\logger.bat" error "镜像构建失败"
    pause
    exit /b 1
)

REM ============================================================================
# 9. 显示构建结果
# ============================================================================
echo.
call "%~dp0lib\logger.bat" success "镜像构建成功"

REM 获取并显示镜像大小
for /f "tokens=*" %%i in ('docker images "%IMAGE_TAG%" --format "{{.Size}}"') do set "IMAGE_SIZE=%%i"
echo [INFO] 镜像大小: %IMAGE_SIZE%
echo.

REM ============================================================================
# 10. 推送镜像（可选）
# ============================================================================
if "%PUSH_IMAGE%"=="true" (
    call "%~dp0common.bat" push_image "%IMAGE_TAG%"
    if errorlevel 1 (
        pause
        exit /b 1
    )
    echo.
)

REM ============================================================================
# 11. 显示后续步骤
# ============================================================================
call "%~dp0common.bat" print_separator "构建完成"
echo.
echo 后续步骤:
echo   1. 将镜像推送到仓库（如未推送）
echo   2. SSH登录到Linux服务器
echo   3. 运行部署脚本: ./deploy.sh %VERSION%
echo.
echo 管理命令:
echo   查看镜像: docker images ^| findstr knowagent-back
echo   删除镜像: docker rmi %IMAGE_TAG%
echo.
call "%~dp0common.bat" print_separator

pause
exit /b 0

REM ============================================================================
# 12. 帮助信息
# ============================================================================
:show_usage
echo 用法: dockerbuild.bat [version] [options]
echo.
echo 版本说明:
echo   v1  云LLM + 本地向量（约3.5GB）
echo   v2  云LLM + 云端向量（约800MB）
echo   v3  本地LLM + 本地向量（约3.5GB）
echo   v4  本地LLM + 云端向量（约800MB）
echo.
echo 选项:
echo   --no-cache   不使用构建缓存
echo   --push       构建后推送到镜像仓库
echo   --help       显示此帮助信息
echo.
echo 示例:
echo   dockerbuild.bat v1              # 交互式选择
echo   dockerbuild.bat v2 --no-cache   # 不使用缓存构建v2
echo   dockerbuild.bat v1 --push       # 构建v1并推送
echo.
pause
exit /b 0

REM ============================================================================
# End of file
# ============================================================================
