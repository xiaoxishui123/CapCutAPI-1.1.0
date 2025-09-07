#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进自定义下载功能的解决方案
解决浏览器无法直接下载到指定路径的问题
"""

import os
import json

def create_download_instructions_page():
    """创建详细的下载指导页面"""
    
    instructions_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自定义下载使用指南</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #667eea;
        }
        .step {
            background: #f8f9fa;
            margin: 15px 0;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        .step-number {
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-weight: bold;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .code {
            background: #f1f3f4;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #5a67d8;
        }
        .icon {
            font-size: 1.2em;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📥 自定义下载使用指南</h1>
            <p>让您的剪映草稿自动识别所有素材！</p>
        </div>

        <div class="warning">
            <strong>🔒 重要说明</strong><br>
            由于浏览器安全限制，无法直接下载到您指定的路径。但我们提供了完美的解决方案！
        </div>

        <h2>🎯 推荐方案一：浏览器设置下载路径</h2>
        
        <div class="step">
            <span class="step-number">1</span>
            <strong>设置浏览器默认下载路径</strong>
            <div class="code">
                <strong>Chrome:</strong> 设置 → 高级 → 下载内容 → 位置<br>
                设置为: <code>F:\\jianying\\cgwz\\JianyingPro Drafts</code>
            </div>
        </div>

        <div class="step">
            <span class="step-number">2</span>
            <strong>下载自定义草稿</strong>
            <p>点击"自定义下载"按钮，文件会直接下载到您设置的剪映目录</p>
        </div>

        <div class="step">
            <span class="step-number">3</span>
            <strong>解压并使用</strong>
            <p>解压ZIP文件，所有路径已自动配置为Windows格式，剪映直接可用！</p>
        </div>

        <h2>🚀 推荐方案二：自动移动脚本</h2>
        
        <div class="step">
            <span class="step-number">1</span>
            <strong>下载自动移动脚本</strong>
            <p>我们为您准备了一个小工具，自动将下载的文件移动到正确位置</p>
            <a href="/download_helper.bat" class="btn">📁 下载Windows脚本</a>
        </div>

        <div class="step">
            <span class="step-number">2</span>
            <strong>运行脚本</strong>
            <p>下载草稿后，双击运行脚本，自动整理到剪映目录</p>
        </div>

        <h2>💡 方案三：手动操作</h2>
        
        <div class="step">
            <span class="step-number">1</span>
            <strong>下载到默认位置</strong>
            <p>点击"自定义下载"，文件下载到Downloads文件夹</p>
        </div>

        <div class="step">
            <span class="step-number">2</span>
            <strong>手动移动文件</strong>
            <p>将ZIP文件剪切/复制到: <code>F:\\jianying\\cgwz\\JianyingPro Drafts</code></p>
        </div>

        <div class="step">
            <span class="step-number">3</span>
            <strong>解压使用</strong>
            <p>右键解压，所有路径已正确配置！</p>
        </div>

        <div class="success">
            <strong>✅ 核心优势</strong><br>
            无论使用哪种方案，下载的草稿都包含正确的Windows路径格式，
            剪映可以自动识别所有素材，无需手动重新链接！
        </div>

        <h2>🔧 技术原理</h2>
        <p>自定义下载功能的核心价值不在于下载位置，而在于：</p>
        <ul>
            <li>🎯 <strong>路径格式转换</strong>：将Linux路径转换为Windows路径</li>
            <li>🔗 <strong>自动素材链接</strong>：所有音频、视频、图片路径自动配置</li>
            <li>⚡ <strong>零配置使用</strong>：解压后剪映直接识别，节省大量时间</li>
        </ul>

        <div style="text-align: center; margin-top: 30px;">
            <a href="javascript:history.back()" class="btn">🔙 返回草稿预览</a>
            <a href="/api/drafts/dashboard" class="btn">📊 草稿管理</a>
        </div>
    </div>

    <script>
        // 检测用户浏览器类型，提供对应的设置指导
        function detectBrowser() {
            const userAgent = navigator.userAgent;
            let browser = "未知浏览器";
            
            if (userAgent.includes("Chrome")) browser = "Chrome";
            else if (userAgent.includes("Firefox")) browser = "Firefox";
            else if (userAgent.includes("Safari")) browser = "Safari";
            else if (userAgent.includes("Edge")) browser = "Edge";
            
            console.log("检测到浏览器:", browser);
        }
        
        detectBrowser();
    </script>
</body>
</html>
"""
    
    # 保存指导页面
    with open('/home/CapCutAPI-1.1.0/templates/download_guide.html', 'w', encoding='utf-8') as f:
        f.write(instructions_html)
    
    print("✅ 创建了详细的下载指导页面")

def create_windows_helper_script():
    """创建Windows自动移动脚本"""
    
    batch_script = """@echo off
chcp 65001
echo 🎬 剪映草稿自动整理工具
echo ================================
echo.

REM 设置剪映目录（用户可以修改这个路径）
set JIANYING_DIR=F:\\jianying\\cgwz\\JianyingPro Drafts

REM 设置下载目录
set DOWNLOAD_DIR=%USERPROFILE%\\Downloads

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
for %%f in ("%DOWNLOAD_DIR%\\draft_*_custom.zip") do (
    if exist "%%f" (
        echo 📦 发现草稿文件: %%~nxf
        move "%%f" "%JIANYING_DIR%\\" >nul
        if errorlevel 1 (
            echo ❌ 移动失败: %%~nxf
        ) else (
            echo ✅ 已移动: %%~nxf
            set /a FOUND+=1
        )
    )
)

REM 查找普通草稿文件
for %%f in ("%DOWNLOAD_DIR%\\dfd_cat_*.zip") do (
    if exist "%%f" (
        echo 📦 发现草稿文件: %%~nxf
        move "%%f" "%JIANYING_DIR%\\" >nul
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
"""
    
    # 保存Windows脚本
    with open('/home/CapCutAPI-1.1.0/static/download_helper.bat', 'w', encoding='utf-8') as f:
        f.write(batch_script)
    
    print("✅ 创建了Windows自动移动脚本")

def update_frontend_with_guide():
    """更新前端，添加使用指导链接"""
    
    # 在自定义下载按钮附近添加指导链接
    guide_button_html = '''
                    <button class="download-btn" onclick="window.open('/download_guide', '_blank')" style="background: #28a745;">
                        📖 下载指南
                    </button>'''
    
    print("✅ 建议在前端添加下载指南按钮")

def main():
    """主函数"""
    print("🔧 改进自定义下载功能...")
    print("=" * 50)
    
    # 确保静态文件目录存在
    os.makedirs('/home/CapCutAPI-1.1.0/static', exist_ok=True)
    os.makedirs('/home/CapCutAPI-1.1.0/templates', exist_ok=True)
    
    # 创建各种解决方案
    create_download_instructions_page()
    create_windows_helper_script()
    update_frontend_with_guide()
    
    print("\n🎉 改进完成！")
    print("\n📋 解决方案总结:")
    print("1. 📖 详细的下载指导页面: /download_guide")
    print("2. 🔧 Windows自动移动脚本: /static/download_helper.bat")
    print("3. 💡 浏览器设置指导")
    print("\n🔗 用户可以通过多种方式实现自定义路径下载")

if __name__ == "__main__":
    main()
