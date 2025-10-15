@echo off
REM 设置UTF-8编码
chcp 65001 >nul 2>&1

echo ====================================
echo 程序诊断和修复工具
echo ====================================
echo.

echo [1/5] 检查Python版本...
python --version
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)
echo.

echo [2/5] 检查项目文件...
if not exist "app.py" (
    echo [错误] 未找到app.py，请在项目根目录运行此脚本
    pause
    exit /b 1
)
echo [OK] 项目文件完整
echo.

echo [3/5] 检查并创建必要目录...
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "failed_labels" mkdir failed_labels
echo [OK] 目录结构完整
echo.

echo [4/5] 检查依赖包...
python tests\test_error_scenarios.py
echo.

echo [5/5] 诊断完成
echo.
echo ====================================
echo 下一步操作：
echo ====================================
echo.
echo 如果测试全部通过：
echo   python app.py
echo.
echo 如果有依赖包缺失：
echo   pip install -r requirements.txt
echo.
echo 如果有其他问题：
echo   查看上方的错误信息
echo.

pause

