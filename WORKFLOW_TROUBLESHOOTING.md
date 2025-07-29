# GitHub Actions 工作流问题排查指南

## 🚨 常见问题及解决方案

### 1. 工作流语法错误

#### 问题症状
- 工作流无法启动
- GitHub Actions 标签页显示语法错误
- YAML 解析失败

#### 解决方案
```bash
# 本地验证 YAML 语法
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml', 'r'))"

# 使用在线 YAML 验证器
# https://yamlchecker.com/
```

### 2. 工作流调用 (uses) 问题

#### 问题症状
- `uses: ./.github/workflows/xxx.yml` 失败
- 工作流间调用出错

#### 解决方案
- 移除复杂的工作流调用，改为直接执行
- 确保被调用的工作流支持 `workflow_call` 触发器

### 3. 依赖安装失败

#### 问题症状
- `pip install` 命令失败
- 模块导入错误

#### 解决方案
```yaml
- name: 📦 Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt || pip install --break-system-packages -r requirements.txt
```

### 4. 文件路径问题

#### 问题症状
- `main.ico` 文件未找到
- 路径引用错误

#### 解决方案
- 移除不存在的文件引用
- 使用相对路径而非绝对路径

### 5. 权限问题

#### 问题症状
- 无法写入文件
- 无法创建 Release

#### 解决方案
```yaml
permissions:
  contents: write
  packages: write
```

## 🔧 快速修复步骤

### 步骤 1: 使用简化的工作流
使用 `simple-ci.yml` 进行初始测试：

```bash
git add .github/workflows/simple-ci.yml
git commit -m "Add simple CI workflow for testing"
git push
```

### 步骤 2: 检查基础功能
确保以下命令在本地工作：

```bash
# 测试包导入
python -c "from src.steam_manifest import SteamManifestClient, Config"

# 测试 CLI
python main.py --help
python main.py --version

# 测试构建
pip install pyinstaller
pyinstaller --onefile main.py
```

### 步骤 3: 逐步启用功能
在简化工作流正常后，逐步添加功能：

1. 代码质量检查 (Black, isort, Flake8)
2. 多平台构建
3. 安全扫描
4. 自动发布

## 🐛 具体错误修复

### 错误 1: workflow_call 不支持
**错误信息**: `uses: ./.github/workflows/ci.yml` 失败

**修复方案**: 
```yaml
# 移除这种调用方式
# uses: ./.github/workflows/ci.yml

# 改为直接执行
runs-on: ubuntu-latest
steps:
  - name: Run CI steps
    run: |
      # 直接执行 CI 步骤
```

### 错误 2: 图标文件缺失
**错误信息**: `main.ico` 文件未找到

**修复方案**: 
```yaml
# 移除图标参数
pyinstaller --onefile --name app-name main.py
# 不使用: pyinstaller --onefile -i main.ico main.py
```

### 错误 3: 工具安装失败
**错误信息**: `pip install bandit safety` 失败

**修复方案**: 
```yaml
- name: Install tools (with fallback)
  run: |
    pip install flake8 black isort || true
    pip install bandit safety || echo "Security tools installation failed"
  continue-on-error: true
```

## 📋 调试检查清单

- [ ] YAML 语法正确
- [ ] 所有引用的文件存在
- [ ] 依赖项可以正常安装
- [ ] 本地测试通过
- [ ] 权限设置正确
- [ ] 环境变量配置正确
- [ ] 工作流触发条件正确

## 🚀 推荐的渐进式启用策略

### 阶段 1: 基础验证
启用 `simple-ci.yml`，确保基本功能正常。

### 阶段 2: 代码质量
添加基础的代码质量检查（Black, Flake8）。

### 阶段 3: 构建测试
添加 PyInstaller 构建和测试。

### 阶段 4: 多平台支持
扩展到 Windows 和 macOS 构建。

### 阶段 5: 高级功能
添加安全扫描、自动发布等高级功能。

## 📞 获取帮助

如果问题持续存在：

1. 检查 GitHub Actions 日志的详细错误信息
2. 在本地复现问题
3. 搜索 GitHub Actions 官方文档
4. 查看类似项目的工作流配置

## 🔗 有用资源

- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [YAML 在线验证器](https://yamlchecker.com/)
- [PyInstaller 文档](https://pyinstaller.readthedocs.io/)
- [GitHub Actions 市场](https://github.com/marketplace?type=actions)