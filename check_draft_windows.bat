@echo off
chcp 65001 >nul
echo ============================================================
echo 剪映草稿结构检查工具 (Windows版)
echo ============================================================
echo.

set DRAFT_PATH=%1

if "%DRAFT_PATH%"=="" (
    echo 请拖拽草稿文件夹到此批处理文件上，或者：
    echo 用法: check_draft_windows.bat "草稿文件夹路径"
    echo.
    echo 示例: check_draft_windows.bat "F:\jianyin\cgwz\JianyingPro Drafts\dfd_cat_xxx"
    pause
    exit /b
)

echo 检查草稿文件夹: %DRAFT_PATH%
echo.

echo [1/5] 检查必需文件...
if exist "%DRAFT_PATH%\draft_info.json" (
    echo   ✓ draft_info.json 存在
) else (
    echo   ✗ draft_info.json 缺失！
)

if exist "%DRAFT_PATH%\draft_meta_info.json" (
    echo   ✓ draft_meta_info.json 存在
) else (
    echo   ✗ draft_meta_info.json 缺失！
)

if exist "%DRAFT_PATH%\draft_content.json" (
    echo   ! draft_content.json 存在 ^(不常见^)
)

echo.
echo [2/5] 检查assets文件夹...
if exist "%DRAFT_PATH%\assets\" (
    echo   ✓ assets\ 存在
    
    if exist "%DRAFT_PATH%\assets\audio\" (
        echo     ✓ assets\audio\ 存在
        
        rem 计数音频文件
        set count=0
        for %%f in ("%DRAFT_PATH%\assets\audio\*.mp3") do set /a count+=1
        if %count% gtr 0 (
            echo       ✓ 找到 %count% 个音频文件
            echo.
            echo       音频文件列表:
            dir /b "%DRAFT_PATH%\assets\audio\*.mp3" | findstr /n "^" | findstr /r "^[1-5]:"
        ) else (
            echo       ✗ audio文件夹是空的！
        )
    ) else (
        echo     ✗ assets\audio\ 不存在！
    )
    
    if exist "%DRAFT_PATH%\assets\video\" (
        echo     ✓ assets\video\ 存在
    ) else (
        echo     ! assets\video\ 不存在
    )
    
    if exist "%DRAFT_PATH%\assets\image\" (
        echo     ✓ assets\image\ 存在
    ) else (
        echo     ! assets\image\ 不存在
    )
) else (
    echo   ✗ assets\ 不存在！
)

echo.
echo [3/5] 检查draft_info.json中的路径...
if exist "%DRAFT_PATH%\draft_info.json" (
    findstr /C:"\"path\"" "%DRAFT_PATH%\draft_info.json" | findstr /n "^" | findstr /r "^[1-3]:" 
    echo.
    echo   检查路径格式:
    findstr /C:"assets\\\\audio" "%DRAFT_PATH%\draft_info.json" >nul
    if errorlevel 1 (
        findstr /C:"assets/audio" "%DRAFT_PATH%\draft_info.json" >nul
        if errorlevel 1 (
            echo     ? 未找到assets路径引用
        ) else (
            echo     ! 使用了正斜杠 '/' ^(应该用反斜杠 '\\'^)
        )
    ) else (
        echo     ✓ 使用了正确的反斜杠 '\\'
    )
)

echo.
echo [4/5] 检查draft_meta_info.json...
if exist "%DRAFT_PATH%\draft_meta_info.json" (
    findstr /C:"\"draft_fold_path\"" "%DRAFT_PATH%\draft_meta_info.json"
    findstr /C:"\"draft_root_path\"" "%DRAFT_PATH%\draft_meta_info.json"
)

echo.
echo [5/5] 检查文件权限和属性...
attrib "%DRAFT_PATH%\draft_info.json" 2>nul
if exist "%DRAFT_PATH%\.locked" (
    echo   ! 发现.locked文件 ^(草稿可能被锁定^)
)

echo.
echo ============================================================
echo 诊断完成！
echo ============================================================
echo.
echo 如果发现问题，请检查上述标记为 ✗ 或 ! 的项目。
echo.
pause

