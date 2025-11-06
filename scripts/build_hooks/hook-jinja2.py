# PyInstaller hook for Jinja2
from PyInstaller.utils.hooks import collect_all, collect_submodules

# 收集所有 Jinja2 内容
datas, binaries, hiddenimports = collect_all('jinja2')

# 确保所有子模块都被包含
hiddenimports += collect_submodules('jinja2')
hiddenimports += collect_submodules('markupsafe')

# 显式添加关键模块
hiddenimports += [
    'jinja2',
    'jinja2.ext',
    'jinja2.loaders',
    'jinja2.runtime',
    'jinja2.compiler',
    'jinja2.filters',
    'jinja2.tests',
    'jinja2.nodes',
    'jinja2.parser',
    'jinja2.lexer',
    'jinja2.environment',
    'jinja2.utils',
    'jinja2.debug',
    'jinja2.exceptions',
    'jinja2.bccache',
    'jinja2.optimizer',
    'jinja2.visitor',
    'markupsafe',
    'markupsafe._native',
]
