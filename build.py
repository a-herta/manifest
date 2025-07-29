#!/usr/bin/env python3
"""
Steam Manifest Tool - Build Script
使用Poetry和PyInstaller构建可执行文件的脚本
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """执行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} 完成")
        if result.stdout:
            print(f"   输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"   错误: {e.stderr.strip()}")
        return False


def check_python_version():
    """检查Python版本是否符合要求"""
    import sys
    version = sys.version_info
    if version.major == 3 and 10 <= version.minor <= 13:
        print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本不符合要求: {version.major}.{version.minor}.{version.micro}")
        print("   要求: Python 3.10 - 3.13 (推荐: 3.12)")
        return False

def main():
    """主构建流程"""
    print("🚀 Steam Manifest Tool 构建脚本")
    print("=" * 50)
    print("📋 Python版本要求: 3.10 - 3.13 (推荐: 3.12)")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查Poetry是否安装
    if not run_command("poetry --version", "检查Poetry安装"):
        print("请先安装Poetry: curl -sSL https://install.python-poetry.org | python3 -")
        sys.exit(1)

    # 安装依赖
    if not run_command("poetry install", "安装项目依赖"):
        sys.exit(1)

    # 运行测试（如果存在）
    test_dir = Path("tests")
    if test_dir.exists():
        run_command("poetry run pytest", "运行测试")

    # 构建Python包
    if not run_command("poetry build", "构建Python包"):
        sys.exit(1)

    # 使用PyInstaller构建可执行文件
    icon_path = Path("src/steam_manifest/assets/main.ico")
    if icon_path.exists():
        pyinstaller_cmd = (
            "poetry run pyinstaller "
            "--onefile "
            "--console "
            f"--icon={icon_path} "
            "--name=steam-manifest-tool "
            "--add-data='src/steam_manifest/assets:steam_manifest/assets' "
            "src/steam_manifest/cli/main.py"
        )
        if not run_command(pyinstaller_cmd, "构建可执行文件"):
            print("⚠️  可执行文件构建失败，但Python包构建成功")
    else:
        print("⚠️  未找到图标文件，跳过可执行文件构建")

    print("\n🎉 构建完成！")
    print("📦 Python包位于: dist/")
    if (
        Path("dist/steam-manifest-tool").exists()
        or Path("dist/steam-manifest-tool.exe").exists()
    ):
        print("🔧 可执行文件位于: dist/")

    print("\n📚 使用方法:")
    print("  安装Python包: pip install dist/steam_manifest_tool-*.whl")
    print("  或直接运行: poetry run steam-manifest")


if __name__ == "__main__":
    main()
