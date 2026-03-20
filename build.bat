@echo off
chcp 65001 >nul
echo === 知乎回答爬虫 打包脚本 ===
echo.

cd /d "%~dp0"

if exist "venv\Scripts\pyinstaller.exe" (
    set PYINSTALLER=venv\Scripts\pyinstaller.exe
) else (
    set PYINSTALLER=pyinstaller
)

echo [1/2] 清理旧构建...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist ZhihuSpider.spec del ZhihuSpider.spec

echo [2/2] 打包中...
%PYINSTALLER% ^
    --onefile ^
    --windowed ^
    --name ZhihuSpider ^
    --icon=icon.ico ^
    --hidden-import DrissionPage ^
    --hidden-import lxml ^
    --hidden-import bs4 ^
    --collect-data DrissionPage ^
    --add-data "icon.ico;." ^
    --add-data "icon.png;." ^
    main.py

echo.
if exist "dist\ZhihuSpider.exe" (
    echo === 打包成功！===
    echo 输出: dist\ZhihuSpider.exe
    for %%A in ("dist\ZhihuSpider.exe") do echo 大小: %%~zA bytes
) else (
    echo === 打包失败，请检查上方错误信息 ===
)
echo.
pause
