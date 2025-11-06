# PyInstaller hook for Starlette
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('starlette')
hiddenimports += collect_submodules('starlette')
