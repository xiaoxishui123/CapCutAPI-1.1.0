@echo off
chcp 65001
echo 🎬 剪映草稿自动整理工具
echo ================================
echo.

REM 设置剪映目录（用户可以修改这个路径）
set JIANYING_DIR=F:\jianying\cgwz\JianyingPro Drafts

REM 设置下载目录
set DOWNLOAD_DIR=%USERPROFILE%\Downloads

echo 📁 剪映目录: %JIANYING_DIR%
echo 📥 下载目录: %DOWNLOAD_DIR%
echo.

REM 检查剪映目录是否存在
if not exist "%JIANYING_DIR%" (
    echo ❌ 剪映目录不存在，正在创建...
    mkdir "%JIANYING_DIR%"
    if errorlevel 1 (
        echo ❌ 无法创建剪映目录，请检查路径或权限
        pause
        exit /b 1
    )
    echo ✅ 已创建剪映目录
)

echo 🔍 正在查找草稿文件...
set FOUND=0

REM 查找并移动草稿ZIP文件
for %%f in ("%DOWNLOAD_DIR%\draft_*_custom.zip") do (
    if exist "%%f" (
        echo 📦 发现草稿文件: %%~nxf
        move "%%f" "%JIANYING_DIR%\" >nul
        if errorlevel 1 (
            echo ❌ 移动失败: %%~nxf
        ) else (
            echo ✅ 已移动: %%~nxf
            set /a FOUND+=1
        )
    )
)

REM 查找普通草稿文件
for %%f in ("%DOWNLOAD_DIR%\dfd_cat_*.zip") do (
    if exist "%%f" (
        echo 📦 发现草稿文件: %%~nxf
        move "%%f" "%JIANYING_DIR%\" >nul
        if errorlevel 1 (
            echo ❌ 移动失败: %%~nxf
        ) else (
            echo ✅ 已移动: %%~nxf
            set /a FOUND+=1
        )
    )
)

echo.
if %FOUND% == 0 (
    echo 😔 没有找到草稿文件
    echo 💡 请确保已下载草稿ZIP文件到Downloads文件夹
) else (
    echo 🎉 成功处理 %FOUND% 个草稿文件！
    echo 📂 文件已移动到剪映目录，请解压后使用
)

echo.
echo 💡 使用提示:
echo 1. 解压ZIP文件到剪映目录
echo 2. 打开剪映应用
echo 3. 草稿会自动出现在草稿列表中
echo.
pause
