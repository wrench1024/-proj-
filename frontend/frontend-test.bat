@echo off
echo ========================================
echo RegDoc Frontend 综合测试
echo ========================================
echo.

echo [1] 环境检查...
echo.
node --version
echo.
if exist "node_modules" (
    echo ? node_modules 存在
) else (
    echo ? node_modules 不存在
    echo 请运行: npm install
    goto :end
)

echo.
echo [2] 项目文件检查...
if exist "src\App.vue" (
    echo ? 主组件存在
) else (
    echo ? 主组件缺失
)

if exist "src\main.ts" (
    echo ? 入口文件存在
) else (
    echo ? 入口文件缺失
)

if exist "package.json" (
    echo ? 配置文件存在
) else (
    echo ? 配置文件缺失
)

echo.
echo [3] 依赖检查...
if exist "node_modules\vue" (
    echo ? Vue 3 已安装
) else (
    echo ? Vue 3 未安装
)

if exist "node_modules\element-plus" (
    echo ? Element Plus 已安装
) else (
    echo ? Element Plus 未安装
)

if exist "node_modules\vite" (
    echo ? Vite 已安装
) else (
    echo ? Vite 未安装
)

echo.
echo [4] 构建测试...
echo 正在构建项目...
node node_modules\vite\bin\vite.js build > build_output.log 2>&1

if %errorlevel% equ 0 (
    echo ? 构建成功
    if exist "dist\index.html" (
        echo ? 输出文件生成成功
    ) else (
        echo ? 输出文件生成失败
    )
) else (
    echo ? 构建失败
    echo 查看 build_output.log 了解详情
)

echo.
echo [5] 文件大小统计...
if exist "dist" (
    for %%f in (dist\*.*) do echo   %%~nxf: %%~zf bytes
    for %%f in (dist\assets\*.*) do echo   assets\%%~nxf: %%~zf bytes
)

echo.
echo [6] 浏览器预览...
echo 可以通过以下方式预览应用:
echo 1. 直接打开: file:///%CD%\dist\index.html
echo 2. 使用任何HTTP服务器提供 dist/ 目录
echo.

echo ========================================
echo 测试完成!
echo ========================================
echo.
echo 建议的下一步:
echo 1. 如果构建成功，应用已准备好部署
echo 2. 使用HTTP服务器预览完整功能
echo 3. 配置生产环境的Web服务器
echo.

:end
pause
