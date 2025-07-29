"""Steam Manifest Tool - A modern tool for fetching Steam game manifest files."""

__version__ = "3.5.0"
__author__ = "Steam Manifest Team"
__description__ = "A tool for fetching and managing Steam game manifest files"

from .core.client import SteamManifestClient
from .core.config import Config

__all__ = ["SteamManifestClient", "Config"]
