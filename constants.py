"""常量配置模块"""

from typing import Final

# 版本信息
VERSION: Final[str] = "3.5.0"

# 网络配置
TIMEOUT: Final[int] = 30
RETRY_TIMES: Final[int] = 10
RETRY_INTERVAL: Final[int] = 5000
MAX_WORKERS: Final[int] = 4  # 线程池最大工作线程数


class URLs:
    """URL常量管理"""

    # GitHub相关
    GITHUB_API: Final[str] = "https://api.github.com"
    GITHUB_RAW: Final[str] = "https://raw.githubusercontent.com"
    GITHUB_RATE_LIMIT: Final[str] = f"{GITHUB_API}/rate_limit"

    # Steam相关
    STEAM_STORE: Final[str] = "https://store.steampowered.com/api"
    STEAM_SEARCH: Final[str] = f"{STEAM_STORE}/storesearch"
    STEAM_APP_DETAILS: Final[str] = f"{STEAM_STORE}/appdetails"

    @staticmethod
    def github_branch(repo: str, branch: str) -> str:
        """获取GitHub分支URL"""
        return f"{URLs.GITHUB_API}/repos/{repo}/branches/{branch}"

    @staticmethod
    def github_raw(repo: str, branch: str, path: str) -> str:
        """获取GitHub原始内容URL"""
        return f"{URLs.GITHUB_RAW}/{repo}/{branch}/{path}"

    @staticmethod
    def steam_search(term: str) -> str:
        """获取Steam搜索URL"""
        return f"{URLs.STEAM_SEARCH}/?cc=cn&l=zh&term={term}"

    @staticmethod
    def steam_app_details(appid: str) -> str:
        """获取Steam应用详情URL"""
        return f"{URLs.STEAM_APP_DETAILS}?cc=cn&l=zh&appids={appid}"


# HTTP请求头
HTTP_HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json",
    "User-Agent": f"GitHubManifest/{VERSION}",
}

# 仓库配置
DEFAULT_REPOS: Final[list[str]] = [
    "a-herta/manifest",
    "SteamAutoCracks/ManifestHub",
]


class Files:
    """文件相关常量"""

    MANIFEST_SUFFIX: Final[str] = ".manifest"
    CONFIG_JSON: Final[str] = "config.json"
    APPINFO_VDF: Final[str] = "appinfo.vdf"
    KEY_VDF: Final[str] = "key.vdf"
    STEAM_EXE: Final[str] = "steam.exe"


class Steam:
    """Steam相关常量"""

    REG_PATH: Final[str] = r"Software\Valve\Steam"
    REG_KEY: Final[str] = "SteamPath"
    PLUGIN_DIR: Final[str] = r"config\stplug-in"
    DEPOT_CACHE: Final[str] = r"config\depotcache"


# 日志格式
LOG_FORMAT: Final[str] = "%(log_color)s %(asctime)s [%(levelname)s] [%(thread)d] %(message)s"
