# 🚀 GitHub Workflows

本项目使用现代化的 GitHub Actions 工作流，支持 Python 3.12 和 3.13，包含完整的 CI/CD 流程。

## 📋 工作流概览

### 🧪 CI Tests (`.github/workflows/ci.yml`)
- **触发条件**: `main` 和 `develop` 分支的推送/PR
- **测试矩阵**: Python 3.12 & 3.13 × Ubuntu/Windows/macOS
- **功能**:
  - 🎨 代码格式检查 (Black)
  - 📚 导入排序检查 (isort)
  - 🔍 代码质量检查 (flake8)
  - 🚀 CLI工具安装测试
  - ✅ 基础功能测试

### 🏗️ Build Executables (`.github/workflows/build.yml`)
- **触发条件**: 版本标签推送 (`v*`) 或手动触发
- **构建目标**: Windows/Linux/macOS 可执行文件
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
  - 🏗️ 构建 Python 包
  - 🧪 测试包安装
  - 📤 发布到 PyPI

### 🔐 Code Quality & Security (`.github/workflows/code-quality.yml`)
- **触发条件**: 每周日定时 + PR + 手动触发
- **功能**:
  - 🛡️ 安全扫描 (safety)
  - 🔍 静态安全分析 (bandit)
  - 📋 依赖审查

## 🛠️ 开发环境设置

### 安装开发依赖
```bash
# 使用 pip
pip install -e .[dev]

# 或使用 requirements-dev.txt
pip install -r requirements-dev.txt
```

### 代码质量检查
```bash
# 格式化代码
black src/

# 排序导入
isort src/

# 代码检查
flake8 src/

# 安全扫描
safety check
bandit -r src/
```

### 本地构建可执行文件
```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建主工具
pyinstaller --onefile --name steam-manifest --console src/steam_manifest/cli/main.py

# 构建辅助工具
pyinstaller --onefile --name steam-extract --console src/steam_manifest/tools/extractor.py
pyinstaller --onefile --name steam-clean --console src/steam_manifest/tools/cleaner.py
```

## 🎯 发布流程

1. **创建版本标签**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **自动执行**:
   - 🏗️ 构建多平台可执行文件
   - 📦 创建 GitHub Release
   - 🚀 发布到 PyPI

3. **产出物**:
   - GitHub Release 包含所有平台的可执行文件
   - PyPI 包可通过 `pip install steam-manifest-tool` 安装

## 📊 支持的平台

- **Python 版本**: 3.12, 3.13
- **操作系统**: Ubuntu, Windows, macOS
- **架构**: AMD64 (x86_64)

## 🎨 特色功能

- ✨ 使用 emoji 美化工作流输出
- 🔄 多平台并行构建和测试
- 📦 自动化包装和发布
- 🛡️ 全面的安全和质量检查
- 🚀 现代化的 CI/CD 最佳实践