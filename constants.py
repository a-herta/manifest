"""
常量配置模块
"""

# 版本信息
VERSION = "3.5.0"

# 网络配置
TIMEOUT = 30
RETRY_TIMES = 10
RETRY_INTERVAL = 5000
MAX_WORKERS = 4  # 线程池最大工作线程数


# URL配置
class URLs:
    """URL常量管理"""
    # GitHub相关
    GITHUB_API = "https://api.github.com"
    GITHUB_RAW = "https://raw.githubusercontent.com"
    GITHUB_RATE_LIMIT = f"{GITHUB_API}/rate_limit"

    # Steam相关
    STEAM_STORE = "https://store.steampowered.com/api"
    STEAM_SEARCH = f"{STEAM_STORE}/storesearch"
    STEAM_APP_DETAILS = f"{STEAM_STORE}/appdetails"

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
HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": f"GitHubManifest/{VERSION}"
}

# 仓库配置
DEFAULT_REPOS = [
    "a-herta/manifest",
    "SteamAutoCracks/ManifestHub"
]


# 文件相关
class Files:
    """文件相关常量"""
    MANIFEST_SUFFIX = ".manifest"
    CONFIG_JSON = "config.json"
    APPINFO_VDF = "appinfo.vdf"
    KEY_VDF = "key.vdf"
    STEAM_EXE = "steam.exe"


# Steam相关
class Steam:
    """Steam相关常量"""
    REG_PATH = r"Software\Valve\Steam"
    REG_KEY = "SteamPath"
    PLUGIN_DIR = r"config\stplug-in"
    DEPOT_CACHE = r"config\depotcache"


# 日志格式
LOG_FORMAT = "%(log_color)s %(asctime)s [%(levelname)s] [%(thread)d] %(message)s"
