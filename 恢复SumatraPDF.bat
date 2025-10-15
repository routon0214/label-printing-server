@echo off
chcp 65001 >nul
echo ======================================================================
echo                    恢复 SumatraPDF
echo ======================================================================
echo.

set SUMATRA_PATH=C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe

if exist "%SUMATRA_PATH%.disabled" (
    echo ✓ 找到: %SUMATRA_PATH%.disabled
    echo.
    echo 恢复为: SumatraPDF.exe
    ren "%SUMATRA_PATH%.disabled" "SumatraPDF.exe"
    
    if exist "%SUMATRA_PATH%" (
        echo ✓ 已恢复 SumatraPDF
    ) else (
        echo ✗ 恢复失败
    )
) else (
    echo ✗ 未找到 SumatraPDF.exe.disabled
)

echo.
echo ======================================================================
pause

