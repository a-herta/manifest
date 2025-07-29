# 🚀 GitHub Workflows

本项目使用现代化的 GitHub Actions 工作流，基于 **Poetry** 依赖管理，支持 Python 3.12 和 3.13，包含完整的 CI/CD 流程。

## 📋 工作流概览

### 🧪 CI Tests (`.github/workflows/ci.yml`)
- **触发条件**: `main` 和 `develop` 分支的推送/PR
- **测试矩阵**: Python 3.12 & 3.13 × Ubuntu/Windows/macOS
- **功能**:
  - 📦 使用 Poetry 管理依赖
  - 🎨 代码格式检查 (Black)
  - 📚 导入排序检查 (isort)
  - 🔍 代码质量检查 (flake8)
  - 🚀 CLI工具安装测试
  - ✅ 基础功能测试

### 🏗️ Build Executables (`.github/workflows/build.yml`)
- **触发条件**: 版本标签推送 (`v*`) 或手动触发
- **构建目标**: Windows/Linux/macOS 可执行文件
- **特色功能**:
  - 🎨 Windows 可执行文件包含应用图标
  - 📦 资源文件自动打包
  - 🔧 基于 Poetry 的依赖管理
- **产出物**:
  - `steam-manifest` - 主CLI工具
  - `steam-extract` - 仓库信息提取器
  - `steam-clean` - 仓库历史清理器
- **打包格式**:
  - Windows: `.zip`
  - Linux/macOS: `.tar.gz`

### 🚀 PyPI Release (`.github/workflows/release.yml`)
- **触发条件**: 版本标签推送 (`v*`)
- **功能**:
  - 📦 使用 Poetry 管理依赖和构建
  - 🏗️ 构建 Python 包 (wheel + sdist)
  - 🧪 测试包安装
  - 📤 使用 Poetry 发布到 PyPI

### 🔐 Code Quality & Security (`.github/workflows/code-quality.yml`)
- **触发条件**: 每周日定时 + PR + 手动触发
- **功能**:
  - 📦 基于 Poetry 的依赖管理
  - 🛡️ 安全扫描 (safety)
  - 🔍 静态安全分析 (bandit)
  - 📋 依赖审查

## 🛠️ 开发环境设置

### 安装 Poetry
```bash
# 使用官方安装脚本
curl -sSL https://install.python-poetry.org | python3 -

# 或使用 pip
pip install poetry
```

### 安装项目依赖
```bash
# 安装生产依赖
poetry install --only main

# 安装所有依赖（包括开发依赖）
poetry install

# 激活虚拟环境
poetry shell
```

### 代码质量检查
```bash
# 格式化代码
poetry run black src/

# 排序导入
poetry run isort src/

# 代码检查
poetry run flake8 src/

# 安全扫描
poetry run safety check
poetry run bandit -r src/
```

### 本地构建

#### 使用构建脚本（推荐）
```bash
python build.py
```

#### 手动构建
```bash
# 构建 Python 包
poetry build

# 构建可执行文件（带图标）
poetry run pyinstaller \
    --onefile \
    --console \
    --icon=src/steam_manifest/assets/main.ico \
    --name=steam-manifest \
    --add-data="src/steam_manifest/assets:steam_manifest/assets" \
    src/steam_manifest/cli/main.py
```

## 🎯 发布流程

1. **更新版本号**:
   ```bash
   # 使用 Poetry 更新版本
   poetry version patch  # 或 minor, major
   ```

2. **创建版本标签**:
   ```bash
   git add pyproject.toml
   git commit -m "🔖 Bump version to $(poetry version -s)"
   git tag v$(poetry version -s)
   git push origin main
   git push origin v$(poetry version -s)
   ```

3. **自动执行**:
   - 🏗️ 构建多平台可执行文件（包含图标和资源）
   - 📦 创建 GitHub Release
   - 🚀 发布到 PyPI

4. **产出物**:
   - GitHub Release 包含所有平台的可执行文件
   - PyPI 包可通过 `pip install steam-manifest-tool` 安装

## 📦 依赖管理

### 添加依赖
```bash
# 添加生产依赖
poetry add package-name

# 添加开发依赖
poetry add --group dev package-name

# 添加可选依赖
poetry add --optional package-name
```

### 更新依赖
```bash
# 更新所有依赖
poetry update

# 更新特定依赖
poetry update package-name
```

### 查看依赖
```bash
# 查看依赖树
poetry show --tree

# 查看过时的依赖
poetry show --outdated
```

## 📊 支持的平台

- **Python 版本**: 3.12, 3.13
- **操作系统**: Ubuntu, Windows, macOS
- **架构**: AMD64 (x86_64)
- **依赖管理**: Poetry 1.8+

## 🎨 特色功能

- ✨ 使用 emoji 美化工作流输出
- 📦 基于 Poetry 的现代依赖管理
- 🎨 Windows 可执行文件包含应用图标
- 🔄 多平台并行构建和测试
- 📦 自动化包装和发布
- 🛡️ 全面的安全和质量检查
- 🚀 现代化的 CI/CD 最佳实践

## 📚 相关文档

- [Poetry 开发指南](POETRY_GUIDE.md) - 详细的 Poetry 使用指南
- [项目结构说明](STRUCTURE.md) - 项目架构和组织