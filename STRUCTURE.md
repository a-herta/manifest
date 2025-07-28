# Steam Manifest Tool - Project Structure

This document describes the modernized project structure and organization.

## 🏗️ Project Structure

```
steam-manifest-tool/
├── src/
│   └── steam_manifest/
│       ├── __init__.py              # Main package
│       ├── core/                    # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration settings
│       │   ├── client.py           # Main client orchestrator
│       │   ├── github_client.py    # GitHub API client
│       │   └── steam_client.py     # Steam API client
│       ├── utils/                   # Utility functions
│       │   ├── __init__.py
│       │   ├── logger.py           # Logging utilities
│       │   ├── input_helper.py     # Input handling
│       │   ├── deduplicator.py     # Deduplication logic
│       │   ├── steam_helper.py     # Steam-related helpers
│       │   └── git_helper.py       # Git repository helpers
│       ├── cli/                     # Command line interface
│       │   ├── __init__.py
│       │   ├── main.py             # CLI entry point
│       │   ├── args.py             # Argument parsing
│       │   └── banner.py           # Banner display
│       └── tools/                   # Additional tools
│           ├── __init__.py
│           ├── extractor.py        # Repository info extractor
│           └── cleaner.py          # Repository history cleaner
├── main.py                         # Main entry point (legacy compatibility)
├── extract.py                      # Extract tool entry (legacy compatibility)
├── clean.py                        # Clean tool entry (legacy compatibility)
├── requirements.txt                # Python dependencies
├── setup.py                        # Setup script
├── pyproject.toml                  # Modern Python project configuration
├── README.md                       # Project documentation
└── STRUCTURE.md                    # This file
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- **Core**: Business logic and main functionality
- **Utils**: Reusable utility functions
- **CLI**: Command line interface and user interaction
- **Tools**: Standalone tools for specific tasks

### 2. **Modern Python Standards**
- Type hints throughout the codebase
- Dataclasses and modern Python features
- PEP 8 compliant code style
- Comprehensive documentation

### 3. **Clean Architecture**
- Clear dependency flow
- Easy to test and maintain
- Modular design
- Single responsibility principle

### 4. **User Experience**
- Consistent command line interface
- Helpful error messages with emojis
- Progress indicators
- Graceful error handling

## 📦 Modules Overview

### Core Modules

- **`config.py`**: Centralized configuration management with type safety
- **`client.py`**: Main orchestrator that coordinates all operations
- **`github_client.py`**: Handles all GitHub API interactions
- **`steam_client.py`**: Manages Steam API communications

### Utility Modules

- **`logger.py`**: Colored logging with configurable levels
- **`input_helper.py`**: Enhanced user input with timestamps
- **`deduplicator.py`**: Removes duplicate entries with priority logic
- **`steam_helper.py`**: Steam installation detection and helpers
- **`git_helper.py`**: Git repository synchronization utilities

### CLI Modules

- **`main.py`**: Main CLI entry point with error handling
- **`args.py`**: Command line argument parsing and validation
- **`banner.py`**: ASCII art banner display

### Tool Modules

- **`extractor.py`**: Extracts repository information and generates README
- **`cleaner.py`**: Cleans Git repository history and force pushes

## 🚀 Entry Points

The project provides multiple entry points:

1. **Main Application**: `python main.py` or `steam-manifest`
2. **Repository Extractor**: `python extract.py` or `steam-extract`
3. **Repository Cleaner**: `python clean.py` or `steam-clean`

## 🔧 Configuration

Configuration is centralized in `src/steam_manifest/core/config.py`:

- Network settings (timeouts, retry attempts)
- File paths and extensions
- Steam registry settings
- GitHub repository defaults
- HTTP headers and user agents

## 📋 Code Style

The project follows modern Python code style guidelines:

- **Type Hints**: All functions have proper type annotations
- **Docstrings**: Comprehensive documentation for all public methods
- **Error Handling**: Graceful error handling with informative messages
- **Naming**: Consistent snake_case naming convention
- **Structure**: Logical organization with clear module boundaries

## 🧪 Testing

The modular structure makes the code easy to test:

- Each module can be tested independently
- Clear interfaces between components
- Dependency injection for better testability
- Mocking-friendly design

## 🔄 Migration from Legacy Code

The legacy files are kept for compatibility:

- `main.py`: Redirects to new CLI
- `extract.py`: Redirects to new extractor
- `clean.py`: Redirects to new cleaner
- `constants.py`: Replaced by `config.py` (removed)
- `repo.py`: Replaced by `git_helper.py` (removed)

## 🎨 Benefits of New Structure

1. **Better Maintainability**: Clear module boundaries and responsibilities
2. **Enhanced Readability**: Consistent naming and documentation
3. **Improved Testability**: Modular design with dependency injection
4. **Future Extensibility**: Easy to add new features and tools
5. **Professional Standards**: Follows Python packaging best practices