# Steam Manifest Tool - Poetry 开发指南

本项目已迁移到使用 [Poetry](https://python-poetry.org/) 进行依赖管理和构建。

## 快速开始

### 1. 安装 Poetry

如果还没有安装 Poetry，请先安装：

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

或者使用 pip 安装：

```bash
pip install poetry
```

### 2. 克隆项目并安装依赖

```bash
git clone https://github.com/steam-manifest/tool.git
cd tool
# 推荐使用Python 3.12
poetry install
```

### 3. 激活虚拟环境

```bash
poetry shell
```

## 开发工作流

### 运行项目

```bash
# 使用 poetry 运行
poetry run steam-manifest --help
poetry run steam-extract --help  
poetry run steam-clean --help

# 或者在激活的环境中直接运行
steam-manifest --help
```

### 添加依赖

```bash
# 添加生产依赖
poetry add package-name

# 添加开发依赖
poetry add --group dev package-name
```

### 代码质量检查

```bash
# 格式化代码
poetry run black src/

# 代码排序
poetry run isort src/

# 代码检查
poetry run flake8 src/

# 安全检查
poetry run safety check
poetry run bandit -r src/
```

### 运行测试

```bash
poetry run pytest
```

## 构建和打包

### 使用提供的构建脚本（推荐）

```bash
python build.py
```

这个脚本会：
- 检查 Poetry 安装
- 安装依赖
- 运行测试（如果存在）
- 构建 Python 包
- 使用 PyInstaller 构建可执行文件（包含图标）

### 手动构建

#### 构建 Python 包

```bash
poetry build
```

生成的包位于 `dist/` 目录：
- `steam_manifest_tool-x.x.x.tar.gz` (源码包)
- `steam_manifest_tool-x.x.x-py3-none-any.whl` (wheel包)

#### 构建可执行文件

```bash
poetry run pyinstaller \
    --onefile \
    --console \
    --icon=src/steam_manifest/assets/main.ico \
    --name=steam-manifest-tool \
    --add-data='src/steam_manifest/assets:steam_manifest/assets' \
    src/steam_manifest/cli/main.py
```

可执行文件位于 `dist/steam-manifest-tool` (Linux/macOS) 或 `dist/steam-manifest-tool.exe` (Windows)

## 项目结构

```
src/steam_manifest/
├── __init__.py
├── assets/
│   └── main.ico          # 应用程序图标
├── cli/                  # 命令行界面
├── core/                 # 核心功能
├── tools/                # 工具模块
└── utils/                # 工具函数
```

## 发布

### 发布到 PyPI

```bash
# 构建
poetry build

# 发布到 TestPyPI（测试）
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi

# 发布到 PyPI（正式）
poetry publish
```

## Python版本支持

- **支持版本**: Python 3.10 - 3.13
- **推荐版本**: Python 3.12
- **最低版本**: Python 3.10
- **最高版本**: Python 3.13 (不包含3.14)

### 发布 GitHub Release

1. 更新版本号：`pyproject.toml` 中的 `version`
2. 运行 `python build.py` 构建所有文件
3. 创建 GitHub Release 并上传 `dist/` 中的文件

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `poetry install` | 安装依赖 |
| `poetry shell` | 激活虚拟环境 |
| `poetry add <package>` | 添加依赖 |
| `poetry remove <package>` | 移除依赖 |
| `poetry show` | 显示依赖列表 |
| `poetry update` | 更新依赖 |
| `poetry build` | 构建包 |
| `poetry publish` | 发布包 |
| `poetry run <command>` | 在虚拟环境中运行命令 |

## 迁移说明

本项目已从传统的 `setuptools` + `requirements.txt` 迁移到 Poetry：

### 已删除的文件
- `setup.py`
- `requirements.txt` 
- `requirements-dev.txt`
- `dev.py`, `main.py`, `clean.py`, `extract.py` (旧入口脚本)
- `src/steam_manifest_tool.egg-info/` 目录

### 新增的文件
- 更新的 `pyproject.toml` (Poetry 格式)  
- `build.py` (构建脚本)
- `src/steam_manifest/assets/main.ico` (移动的图标文件)
- `POETRY_GUIDE.md` (本文档)

所有功能保持不变，只是改用 Poetry 进行管理。