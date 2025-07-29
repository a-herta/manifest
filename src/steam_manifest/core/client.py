"""Main client for Steam Manifest Tool."""

import logging
import os
import time
from multiprocessing import pool
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import vdf

from ..utils.deduplicator import remove_duplicates
from ..utils.input_helper import custom_input
from ..utils.steam_helper import find_steam_path
from .config import Config, URLBuilder
from .github_client import GitHubClient
from .steam_client import SteamClient


class SteamManifestClient:
    """Main client for Steam Manifest operations."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        repo: Optional[str] = None,
        fixed_mode: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize Steam Manifest client.

        Args:
            api_token: GitHub API token
            repo: Custom repository name
            fixed_mode: Enable fixed manifest mode
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.github_client = GitHubClient(api_token, self.logger)
        self.steam_client = SteamClient(self.logger)
        self.lock = Lock()

        self.custom_repo = repo
        self.fixed_mode = fixed_mode

        # Application state
        self.app_info: List[str] = []
        self.manifests: List[str] = []
        self.depots: List[Tuple[int, Optional[str]]] = []

    def find_app_id(self, search_term: str) -> List[str]:
        """Find Steam application ID by name or return as-is if numeric.

        Args:
            search_term: Application name or ID

        Returns:
            List of application IDs
        """
        if search_term.isdigit():
            return [search_term]

        # Search for applications
        apps = self.steam_client.search_apps(search_term)
        if not apps:
            raise Exception("No applications found")

        self.logger.info("🎯 Found the following applications:")
        for idx, app in enumerate(apps, 1):
            self.logger.info(f"📌 {idx}. [{app['id']}] [{app['type']}] {app['name']}")

        if len(apps) == 1:
            selected = apps[0]
        else:
            time.sleep(1)
            choice = self._get_user_choice(len(apps))
            selected = apps[int(choice) - 1]

        app_id = selected["id"]
        self.logger.info(f"✨ Selected application: [{app_id}] {selected['name']}")
        return [str(app_id)]

    def _get_user_choice(self, max_choice: int) -> str:
        """Get user choice with validation.

        Args:
            max_choice: Maximum valid choice number

        Returns:
            User's choice as string
        """
        while True:
            choice = custom_input("Please select application number:")
            if choice.isdigit() and 1 <= int(choice) <= max_choice:
                return choice
            self.logger.warning("⚠️ Invalid input, please try again")

    def verify_prerequisites(
        self,
    ) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
        """Verify all prerequisites for operation.

        Returns:
            Tuple of (steam_path, rate_limit_reset, current_repo)
        """
        # Check Steam installation
        steam_path = find_steam_path()
        if not steam_path:
            self.logger.error("❌ Steam installation not found")
            return None, None, None

        self.logger.info(f"🎮 Found Steam installation: {steam_path}")

        # Check API rate limit
        reset_time = self.github_client.check_rate_limit()
        if reset_time:
            self.logger.error(f"❌ API rate limit exceeded, resets at: {reset_time}")
            return steam_path, reset_time, None

        # Find latest repository
        current_repo = self._find_latest_repository()
        if not current_repo:
            self.logger.error(f"❌ No repository found for AppID: {self.app_info[0]}")
            return steam_path, None, None

        return steam_path, None, current_repo

    def _find_latest_repository(self) -> Optional[str]:
        """Find the latest repository containing the application.

        Returns:
            Repository name or None if not found
        """
        repos = Config.DEFAULT_REPOS.copy()
        if self.custom_repo:
            repos.insert(0, self.custom_repo)

        latest_date: Optional[str] = None
        current_repo: Optional[str] = None

        for repo in repos:
            try:
                branch_info = self.github_client.get_branch_info(repo, self.app_info[0])
                if not branch_info or "commit" not in branch_info:
                    self.logger.debug(
                        f"📝 No matching branch found in repository: {repo}"
                    )
                    continue

                date = branch_info["commit"]["commit"]["committer"]["date"]
                if not latest_date or latest_date < date:
                    latest_date = date
                    current_repo = repo

            except Exception as e:
                self.logger.warning(f"⚠️ Error checking repository {repo}: {str(e)}")
                continue

        if current_repo:
            self.logger.info(f"📦 Using manifest repository: {current_repo}")

        return current_repo

    def process_repository(
        self, repo: str, branch: str, steam_path: Path, is_dlc: bool = False
    ):
        """Process repository branch and download manifests.

        Args:
            repo: Repository name
            branch: Branch name
            steam_path: Steam installation path
            is_dlc: Whether this is DLC processing
        """
        try:
            self.depots.append((int(branch), None))

            # Get branch information
            branch_info = self.github_client.get_branch_info(repo, branch)
            if not branch_info or "commit" not in branch_info:
                self.logger.warning(f"⚠️ Branch {branch} not found in repository {repo}")
                return

            # Get file tree
            commit_date = branch_info["commit"]["commit"]["committer"]["date"]
            tree_url = branch_info["commit"]["commit"]["tree"]["url"]
            tree_response = self.github_client.api_request(tree_url)

            if not tree_response or "tree" not in tree_response:
                self.logger.warning(f"⚠️ File details not found in branch {branch}")
                return

            # Process files using thread pool
            files = tree_response["tree"]
            with pool.ThreadPool(Config.MAX_WORKERS) as thread_pool:
                tasks = []
                for file_info in files:
                    task = thread_pool.apply_async(
                        self._process_manifest_file,
                        (repo, branch, file_info["path"], steam_path),
                    )
                    tasks.append(task)

                try:
                    for task in tasks:
                        task.get(timeout=Config.TIMEOUT)

                except KeyboardInterrupt:
                    self.logger.warning("⚠️ Operation interrupted by user")
                    with self.lock:
                        thread_pool.terminate()
                    raise
                except Exception as e:
                    self.logger.error(f"❌ Error processing branch {branch}: {str(e)}")
                    return

            # Handle DLC if config.json not found
            if Config.CONFIG_JSON not in [f["path"] for f in files]:
                self.logger.info("🔍 Getting DLC information from Steam store...")
                dlc_list = self.steam_client.get_app_dlc(branch)
                if dlc_list:
                    self.logger.info(f"🎯 Found DLC content: {dlc_list}")
                    for dlc_id in dlc_list:
                        time.sleep(2)
                        self.process_repository(repo, str(dlc_id), steam_path, True)

            # Save application info if all tasks successful and not DLC
            if all(task.successful() for task in tasks) and not is_dlc:
                self._save_app_info(steam_path)
                self.logger.info(
                    f"📅 Successfully processed: {self.app_info}, last updated: {commit_date}"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Error processing repository {repo} branch {branch}: {str(e)}"
            )
            raise

    def _process_manifest_file(
        self, repo: str, branch: str, path: str, steam_path: Path
    ):
        """Process individual manifest file.

        Args:
            repo: Repository name
            branch: Branch name
            path: File path
            steam_path: Steam installation path
        """
        try:
            with self.lock:
                self.logger.debug(f"📄 Processing file: {path}")

            if path.endswith(Config.MANIFEST_SUFFIX):
                self._store_manifest_file(repo, branch, path, steam_path)
            elif path.endswith(".vdf"):
                self._handle_vdf_file(repo, branch, path)
            elif path == Config.CONFIG_JSON:
                self._handle_config_file(repo, branch, path, steam_path)

        except Exception as e:
            self.logger.error(f"❌ Error processing file {path}: {str(e)}")
            raise

    def _store_manifest_file(self, repo: str, branch: str, path: str, steam_path: Path):
        """Store manifest file to Steam depot cache.

        Args:
            repo: Repository name
            branch: Branch name
            path: File path
            steam_path: Steam installation path
        """
        self.manifests.append(path)
        depot_cache = steam_path / Config.STEAM_DEPOT_CACHE
        depot_cache.mkdir(parents=True, exist_ok=True)
        save_path = depot_cache / path

        if save_path.exists():
            self.logger.warning(f"⚠️ Manifest file already exists: {path}")
            return

        content = self.github_client.download_file(repo, branch, path)
        if content is not None:
            temp_path = save_path.with_suffix(".tmp")
            try:
                temp_path.write_bytes(content)
                temp_path.replace(save_path)
                self.logger.info(f"📥 Manifest file downloaded: {path}")
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise e

    def _handle_vdf_file(self, repo: str, branch: str, path: str):
        """Handle VDF files (appinfo.vdf, key.vdf).

        Args:
            repo: Repository name
            branch: Branch name
            path: File path
        """
        try:
            content = self.github_client.download_file(repo, branch, path)
            if content is None:
                return

            if path == Config.APPINFO_VDF:
                self._parse_appinfo_vdf(content)
            elif path == Config.KEY_VDF:
                self._parse_key_vdf(content)

        except Exception as e:
            self.logger.error(f"❌ Error handling VDF file: {str(e)}")
            raise

    def _parse_appinfo_vdf(self, content: bytes):
        """Parse appinfo.vdf file content.

        Args:
            content: VDF file content
        """
        try:
            appinfo_config = vdf.loads(content.decode())
            app_name = appinfo_config["common"]["name"]
            self.app_info.append(app_name)
        except Exception as e:
            self.logger.error(f"⛔ Failed to parse appinfo.vdf: {str(e)}")
            raise

    def _parse_key_vdf(self, content: bytes):
        """Parse key.vdf file content.

        Args:
            content: VDF file content
        """
        try:
            depot_config = vdf.loads(content.decode())
            depot_dict: Dict = depot_config["depots"]
            self.depots.extend(
                (int(k), v["DecryptionKey"]) for k, v in depot_dict.items()
            )
            self.logger.info("🔑 Found decryption keys")
        except Exception as e:
            self.logger.error(f"⛔ Failed to parse key.vdf: {str(e)}")
            raise

    def _handle_config_file(self, repo: str, branch: str, path: str, steam_path: Path):
        """Handle config.json file.

        Args:
            repo: Repository name
            branch: Branch name
            path: File path
            steam_path: Steam installation path
        """
        try:
            config_content = self.github_client.get_file_content(repo, branch, path)
            if not config_content:
                raise Exception("Unable to get config file")

            dlcs: List[int] = config_content.get("dlcs", [])
            package_dlcs: List[int] = config_content.get("packagedlcs", [])

            if dlcs:
                self.logger.info(f"🎮 Found DLC content: {dlcs}")
                self.depots.extend((dlc_id, None) for dlc_id in dlcs)

            if package_dlcs:
                self.logger.info(f"🎯 Found packaged DLC: {package_dlcs}")
                for dlc_id in package_dlcs:
                    self.process_repository(repo, str(dlc_id), steam_path, True)

        except Exception as e:
            self.logger.error(f"❌ Error getting config file: {str(e)}")

    def _save_app_info(self, steam_path: Path):
        """Save application information to Lua file.

        Args:
            steam_path: Steam installation path
        """
        try:
            # Remove duplicates and sort depot records
            depot_list = sorted(set(self.depots), key=lambda x: x[0])
            depot_list = remove_duplicates(depot_list)

            # Generate Lua content
            lua_content = ""
            if len(self.app_info) > 1:
                lua_content = f"-- {self.app_info[1]}\n"

            # Add appid information
            for depot_id, depot_key in depot_list:
                if depot_key:
                    lua_content += f'addappid({depot_id}, 1, "{depot_key}")\n'
                else:
                    lua_content += f"addappid({depot_id}, 1)\n"

            # Add manifest information if fixed mode enabled
            if self.fixed_mode:
                manifest_list = sorted(
                    [
                        (parts[0], parts[1].split(".")[0])
                        for parts in (
                            manifest.split("_") for manifest in self.manifests
                        )
                    ],
                    key=lambda x: x[0],
                )
                for depot_id, manifest_id in manifest_list:
                    lua_content += f'setManifestid({depot_id}, "{manifest_id}")\n'

            # Save to file
            lua_filename = f"{self.app_info[0]}.lua"
            lua_dir = steam_path / Config.STEAM_PLUGIN_DIR
            lua_dir.mkdir(parents=True, exist_ok=True)
            lua_file_path = lua_dir / lua_filename

            # Use temporary file for atomic write
            temp_file_path = lua_file_path.with_suffix(".tmp")
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(lua_content)
            temp_file_path.replace(lua_file_path)

            self.logger.info(f"📝 Configuration saved to: {lua_file_path}")

        except Exception as e:
            self.logger.error(f"❌ Error saving configuration file: {str(e)}")

    def process_app(self, app_ids: List[str]) -> bool:
        """Process Steam application manifest files.

        Args:
            app_ids: List of application IDs to process

        Returns:
            True if successful, False otherwise
        """
        try:
            self.app_info = app_ids.copy()

            # Verify prerequisites
            steam_path, rate_limit_reset, current_repo = self.verify_prerequisites()
            if not steam_path:
                return False
            if rate_limit_reset:
                return False
            if not current_repo:
                return False

            # Process the main application
            self.process_repository(current_repo, app_ids[0], steam_path)
            return True

        except KeyboardInterrupt:
            self.logger.warning("⚠️ Operation interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error occurred: {str(e)}")
            return False
