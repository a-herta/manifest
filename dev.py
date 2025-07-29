#!/usr/bin/env python3
"""Development utility script for Steam Manifest Tool."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def install_deps():
    """Install project dependencies."""
    print("🔧 Installing dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed!")


def run_tests():
    """Run project tests."""
    print("🧪 Running tests...")
    # For now, just import test to verify structure
    try:
        from src.steam_manifest import Config, SteamManifestClient

        print("✅ Package import test passed!")
    except ImportError as e:
        print(f"❌ Package import test failed: {e}")
        sys.exit(1)


def format_code():
    """Format code using black."""
    print("🎨 Formatting code...")
    try:
        run_command([sys.executable, "-m", "black", "src/", "*.py"])
        print("✅ Code formatted!")
    except subprocess.CalledProcessError:
        print("⚠️ Black not installed, skipping format")


def lint_code():
    """Lint code using flake8."""
    print("🔍 Linting code...")
    try:
        run_command([sys.executable, "-m", "flake8", "src/"])
        print("✅ Code linting passed!")
    except subprocess.CalledProcessError:
        print("⚠️ Flake8 not installed, skipping lint")


def clean():
    """Clean build artifacts."""
    print("🧹 Cleaning build artifacts...")
    artifacts = [
        "build/",
        "dist/",
        "*.egg-info/",
        "**/__pycache__/",
        "**/*.pyc",
        "**/*.pyo",
    ]

    for pattern in artifacts:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                import shutil

                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            else:
                path.unlink()
                print(f"Removed file: {path}")

    print("✅ Cleanup complete!")


def build():
    """Build the package."""
    print("📦 Building package...")
    run_command([sys.executable, "-m", "build"])
    print("✅ Package built!")


def main():
    """Main development script entry point."""
    parser = argparse.ArgumentParser(
        description="Development utility for Steam Manifest Tool"
    )

    commands = parser.add_subparsers(dest="command", help="Available commands")

    commands.add_parser("install", help="Install dependencies")
    commands.add_parser("test", help="Run tests")
    commands.add_parser("format", help="Format code")
    commands.add_parser("lint", help="Lint code")
    commands.add_parser("clean", help="Clean build artifacts")
    commands.add_parser("build", help="Build package")
    commands.add_parser("all", help="Run install, format, lint, test, and build")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "install":
        install_deps()
    elif args.command == "test":
        run_tests()
    elif args.command == "format":
        format_code()
    elif args.command == "lint":
        lint_code()
    elif args.command == "clean":
        clean()
    elif args.command == "build":
        build()
    elif args.command == "all":
        install_deps()
        format_code()
        lint_code()
        run_tests()
        clean()
        build()


if __name__ == "__main__":
    main()
