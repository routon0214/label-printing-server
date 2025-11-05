@echo off
chcp 65001 >nul
echo ======================================================================
echo              临时禁用 SumatraPDF（解决纸张问题）
echo ======================================================================
echo.
echo 此脚本将临时禁用 SumatraPDF，让系统使用备用打印方案
echo.
echo 原因：
echo   - SumatraPDF 对纸张大小要求严格
echo   - 备用方案（Adobe Reader/Windows默认）更宽松
echo.
pause

set SUMATRA_PATH=C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe

echo.
echo 检查 SumatraPDF...
if exist "%SUMATRA_PATH%" (
    echo ✓ 找到: %SUMATRA_PATH%
    echo.
    echo 重命名为: SumatraPDF.exe.disabled
    ren "%SUMATRA_PATH%" "SumatraPDF.exe.disabled"
    
    if exist "%SUMATRA_PATH%.disabled" (
        echo ✓ 已禁用 SumatraPDF
        echo.
        echo 现在运行测试：
        echo   python tests\test_auto_print.py
        echo.
        echo 如需恢复，运行：恢复SumatraPDF.bat
    ) else (
        echo ✗ 禁用失败，可能需要管理员权限
    )
) else (
    echo ✗ 未找到 SumatraPDF
    echo 路径: %SUMATRA_PATH%
)

echo.
echo ======================================================================
pause

