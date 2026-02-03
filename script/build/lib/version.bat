@echo off
REM ============================================================================
# 知识库智能体 - 版本配置函数库
# File    : lib/version.bat
# Purpose : 提供版本相关的配置和验证函数
# Usage   : call "%~f0" <command> [args...]
# ============================================================================

REM ============================================================================
# 版本配置映射表（内部变量）
# 说明：
#   v1: 云LLM + 本地向量（需要torch，约3.5GB）
#   v2: 云LLM + 云端向量（轻量版，约800MB）
#   v3: 本地LLM + 本地向量（需要torch，约3.5GB）
#   v4: 本地LLM + 云端向量（轻量版，约800MB）
# ============================================================================

REM ============================================================================
# 命令分发
# ============================================================================
if /I "%~1"=="validate" goto :validate
if /I "%~1"=="get_config" goto :get_config
if /I "%~1"=="list" goto :list_versions
if /I "%~1"=="description" goto :get_description

echo [ERROR] Unknown command: %~1
exit /b 1

REM ============================================================================
# validate - 验证版本号是否有效
# 参数: %2 = 版本号 (v1/v2/v3/v4)
# 返回: ERRORLEVEL 0=有效, 1=无效
# ============================================================================
:validate
set "VER=%~2"
if "%VER%"=="v1" exit /b 0
if "%VER%"=="v2" exit /b 0
if "%VER%"=="v3" exit /b 0
if "%VER%"=="v4" exit /b 0
exit /b 1

REM ============================================================================
# get_config - 获取版本配置信息
# 参数: %2 = 版本号
# 返回: 设置环境变量 VERSION_DESC, INSTALL_LOCAL_EMB, IMAGE_TAG
# ============================================================================
:get_config
set "VER=%~2"
set "REGISTRY=%REGISTRY:-registry.cn-shanghai.aliyuncs.com/tianlanhai/test%"
set "IMAGE_NAME=%IMAGE_NAME:-knowagent-back%"

if "%VER%"=="v1" (
    set "VERSION_DESC=云LLM + 本地向量"
    set "INSTALL_LOCAL_EMB=true"
    set "IMAGE_TAG=%REGISTRY%:%IMAGE_NAME%-v1"
    goto :config_done
)
if "%VER%"=="v2" (
    set "VERSION_DESC=云LLM + 云端向量"
    set "INSTALL_LOCAL_EMB=false"
    set "IMAGE_TAG=%REGISTRY%:%IMAGE_NAME%-v2"
    goto :config_done
)
if "%VER%"=="v3" (
    set "VERSION_DESC=本地LLM + 本地向量"
    set "INSTALL_LOCAL_EMB=true"
    set "IMAGE_TAG=%REGISTRY%:%IMAGE_NAME%-v3"
    goto :config_done
)
if "%VER%"=="v4" (
    set "VERSION_DESC=本地LLM + 云端向量"
    set "INSTALL_LOCAL_EMB=false"
    set "IMAGE_TAG=%REGISTRY%:%IMAGE_NAME%-v4"
    goto :config_done
)
exit /b 1

:config_done
exit /b 0

REM ============================================================================
# get_description - 获取版本描述
# 参数: %2 = 版本号
# 返回: 输出版本描述
# ============================================================================
:get_description
set "VER=%~2"
if "%VER%"=="v1" echo 云LLM + 本地向量（约3.5GB，需要torch）
if "%VER%"=="v2" echo 云LLM + 云端向量（约800MB，轻量版）
if "%VER%"=="v3" echo 本地LLM + 本地向量（约3.5GB，需要torch）
if "%VER%"=="v4" echo 本地LLM + 云端向量（约800MB，轻量版）
exit /b 0

REM ============================================================================
# list_versions - 列出所有可用版本
# ============================================================================
:list_versions
echo 可用版本列表:
echo   v1 - 云LLM + 本地向量（约3.5GB，需要torch）
echo   v2 - 云LLM + 云端向量（约800MB，轻量版）
echo   v3 - 本地LLM + 本地向量（约3.5GB，需要torch）
echo   v4 - 本地LLM + 云端向量（约800MB，轻量版）
exit /b 0

REM ============================================================================
# End of file
# ============================================================================
