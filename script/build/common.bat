@echo off
REM ============================================================================
# 知识库智能体 - Windows通用函数库
# File    : common.bat
# Purpose : 提供共享的环境变量和通用函数
# Design  : 遵循SOLID原则，单一职责，可复用
# Usage   : call "%~f0" <command> [args...]
# ============================================================================

REM ============================================================================
# 命令分发（Dispatch模式 - 简化版策略模式）
# ============================================================================
if "%~1"=="" goto :init
if /I "%~1"=="init" goto :init
if /I "%~1"=="check_docker" goto :check_docker
if /I "%~1"=="push_image" goto :push_image
if /I "%~1"=="pull_image" goto :pull_image
if /I "%~1"=="print_separator" goto :print_separator
if /I "%~1"=="error_exit" goto :error_exit

echo [ERROR] Unknown command: %~1
exit /b 1

REM ============================================================================
# init - 初始化环境变量
# 返回: 设置全局环境变量
# ============================================================================
:init
REM ============================================================================
# 项目基础配置
# ============================================================================
set "PROJECT_NAME=knowledge-agent"
set "VERSION=1.0.0"

REM ============================================================================
# 镜像仓库配置（阿里云容器镜像服务）
# ============================================================================
set "REGISTRY=registry.cn-shanghai.aliyuncs.com/tianlanhai/test"
set "IMAGE_NAME=knowagent-back"
set "FRONTEND_IMAGE_NAME=knowagent-front"

REM ============================================================================
# 目录配置（通过相对路径计算项目根目录）
# ============================================================================
set "SCRIPT_DIR=%~dp0"
REM SCRIPT_DIR: <PROJECT_ROOT>\script\build\
REM SCRIPT_DIR%..%: <PROJECT_ROOT>\script\
REM SCRIPT_DIR%..\..%: <PROJECT_ROOT>\
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%code"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

REM ============================================================================
# 容器配置
# ============================================================================
set "NETWORK_NAME=knowledge-agent-network"
set "BACKEND_CONTAINER=knowledge-agent-backend"
set "FRONTEND_CONTAINER=knowledge-agent-frontend"
set "BACKEND_PORT=8010"
set "FRONTEND_PORT=8011"

REM ============================================================================
# 数据目录配置（Windows本地构建用）
# ============================================================================
set "DATA_DIR=%PROJECT_ROOT%data"

exit /b 0

REM ============================================================================
# check_docker - 检查Docker是否运行
# 返回: ERRORLEVEL 0=运行中, 1=未运行
# ============================================================================
:check_docker
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未运行，请启动Docker Desktop
    exit /b 1
)
exit /b 0

REM ============================================================================
# push_image - 推送镜像到仓库
# 参数: %2 = 镜像名称
# 返回: ERRORLEVEL 0=成功, 1=失败
# ============================================================================
:push_image
if "%~2"=="" (
    echo [ERROR] 镜像名称不能为空
    exit /b 1
)

echo [PUSH] 推送镜像: %~2

REM 提取仓库地址并检查登录状态
for /f "tokens=1 delims=/" %%a in ("%~2") do set "REGISTRY_HOST=%%a"

REM 检查是否已登录镜像仓库
docker login "%REGISTRY_HOST%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 需要登录镜像仓库...
    docker login "%REGISTRY_HOST%"
    if errorlevel 1 (
        echo [ERROR] 登录失败
        exit /b 1
    )
)

docker push "%~2"
if errorlevel 1 (
    echo [ERROR] 推送失败
    exit /b 1
)
echo [SUCCESS] 镜像推送成功
exit /b 0

REM ============================================================================
# pull_image - 拉取镜像
# 参数: %2 = 镜像名称
# 返回: ERRORLEVEL 0=成功, 1=失败
# ============================================================================
:pull_image
if "%~2"=="" (
    echo [ERROR] 镜像名称不能为空
    exit /b 1
)
echo [PULL] 拉取镜像: %~2
docker pull "%~2"
exit /b %ERRORLEVEL%

REM ============================================================================
# print_separator - 打印分隔线
# 参数: %2 = 标题（可选）
# ============================================================================
:print_separator
echo.
echo ========================================
if not "%~2"=="" echo   %~2
if not "%~2"=="" echo ========================================
exit /b 0

REM ============================================================================
# error_exit - 打印错误信息并退出
# 参数: %2 = 错误消息
# ============================================================================
:error_exit
echo.
echo [ERROR] %~2
echo.
pause
exit /b 1

REM ============================================================================
# End of file
# ============================================================================
