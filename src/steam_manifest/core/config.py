"""Configuration settings for Steam Manifest Tool."""

from typing import Final


class Config:
    """Configuration settings for the Steam Manifest Tool."""

    # Version information
    VERSION: Final[str] = "3.6.0"

    # Network settings
    TIMEOUT: Final[int] = 30
    RETRY_TIMES: Final[int] = 10
    RETRY_INTERVAL: Final[int] = 5000
    MAX_WORKERS: Final[int] = 4

    # HTTP headers
    HTTP_HEADERS: Final[dict[str, str]] = {
        "Accept": "application/json",
        "User-Agent": f"GitHubManifest/{VERSION}",
    }

    # Default repositories
    DEFAULT_REPOS: Final[list[str]] = [
        "a-herta/manifest",
        "SteamAutoCracks/ManifestHub",
    ]

    # File extensions and names
    MANIFEST_SUFFIX: Final[str] = ".manifest"
    CONFIG_JSON: Final[str] = "config.json"
    APPINFO_VDF: Final[str] = "appinfo.vdf"
    KEY_VDF: Final[str] = "key.vdf"
    STEAM_EXE: Final[str] = "steam.exe"

    # Steam registry settings
    STEAM_REG_PATH: Final[str] = r"Software\Valve\Steam"
    STEAM_REG_KEY: Final[str] = "SteamPath"
    STEAM_PLUGIN_DIR: Final[str] = r"config\stplug-in"
    STEAM_DEPOT_CACHE: Final[str] = r"config\depotcache"

    # Log format
    LOG_FORMAT: Final[str] = (
        "%(log_color)s %(asctime)s [%(levelname)s] [%(thread)d] %(message)s"
    )


class URLBuilder:
    """URL builder for various API endpoints."""

    # Base URLs
    GITHUB_API: Final[str] = "https://api.github.com"
    GITHUB_RAW: Final[str] = "https://raw.githubusercontent.com"
    STEAM_STORE: Final[str] = "https://store.steampowered.com/api"

    @classmethod
    def github_rate_limit(cls) -> str:
        """Get GitHub rate limit URL."""
        return f"{cls.GITHUB_API}/rate_limit"

    @classmethod
    def github_branch(cls, repo: str, branch: str) -> str:
        """Get GitHub branch URL."""
        return f"{cls.GITHUB_API}/repos/{repo}/branches/{branch}"

    @classmethod
    def github_raw(cls, repo: str, branch: str, path: str) -> str:
        """Get GitHub raw content URL."""
        return f"{cls.GITHUB_RAW}/{repo}/{branch}/{path}"

    @classmethod
    def steam_search(cls, term: str) -> str:
        """Get Steam search URL."""
        return f"{cls.STEAM_STORE}/storesearch/?cc=jp&l=zh&term={term}"

    @classmethod
    def steam_app_details(cls, app_id: str) -> str:
        """Get Steam app details URL."""
        return f"{cls.STEAM_STORE}/appdetails?cc=jp&l=zh&appids={app_id}"
