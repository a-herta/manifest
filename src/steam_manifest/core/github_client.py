"""GitHub API client for Steam Manifest Tool."""

import os
import logging
from typing import Dict, Any, Optional
from threading import Lock

import httpx
from retrying import retry

from .config import Config, URLBuilder


class GitHubClient:
    """GitHub API client for accessing repositories and content."""

    def __init__(
        self, api_token: Optional[str] = None, logger: Optional[logging.Logger] = None
    ):
        """Initialize GitHub client.

        Args:
            api_token: GitHub API token for authentication
            logger: Logger instance
        """
        self.api_token = api_token or os.getenv("GITHUB_API_TOKEN")
        self.logger = logger or logging.getLogger(__name__)
        self.lock = Lock()

        # Prepare headers
        self.headers = Config.HTTP_HEADERS.copy()
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    @retry(wait_fixed=Config.RETRY_INTERVAL, stop_max_attempt_number=Config.RETRY_TIMES)
    def api_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Send HTTP GET request and get JSON response.

        Args:
            url: Request URL

        Returns:
            JSON response data or None if request failed
        """
        try:
            with httpx.Client(
                timeout=Config.TIMEOUT, headers=self.headers, follow_redirects=True
            ) as client:
                with self.lock:
                    self.logger.debug(f"📡 Sending request: {url}")

                response = client.get(url)

                # Handle special status codes
                if response.status_code == 429:  # Rate limit
                    reset_time = response.headers.get("X-RateLimit-Reset")
                    if reset_time:
                        from datetime import datetime

                        reset_datetime = datetime.fromtimestamp(int(reset_time))
                        wait_time = (reset_datetime - datetime.now()).total_seconds()
                        self.logger.warning(
                            f"⚠️ Rate limit reached, retrying in {wait_time:.0f} seconds"
                        )
                    raise Exception("Rate limit exceeded")
                elif response.status_code == 404:
                    self.logger.debug(f"⚠️ Resource not found: {url}")
                    return None

                response.raise_for_status()
                json_data = response.json()

                with self.lock:
                    self.logger.debug(
                        f"📥 Received response: {len(str(json_data))} bytes"
                    )

                return json_data

        except httpx.TimeoutException:
            self.logger.error(f"⌛ Request timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"🔧 HTTP request failed: {e.response.status_code} - {url}"
            )
            return None
        except Exception as e:
            self.logger.error(f"❌ Request exception: {str(e)} - {url}")
            return None

    @retry(wait_fixed=Config.RETRY_INTERVAL, stop_max_attempt_number=Config.RETRY_TIMES)
    def download_raw_content(self, url: str) -> Optional[bytes]:
        """Download raw content from URL.

        Args:
            url: Request URL

        Returns:
            Binary response data or None if download failed
        """
        try:
            with httpx.Client(
                timeout=Config.TIMEOUT,
                headers=Config.HTTP_HEADERS,
                follow_redirects=True,
            ) as client:
                with self.lock:
                    self.logger.debug(f"📥 Downloading: {url}")

                response = client.get(url)
                response.raise_for_status()

                content = response.content
                with self.lock:
                    self.logger.debug(f"✅ Download completed: {len(content)} bytes")

                return content

        except Exception as e:
            self.logger.error(f"❌ Download failed: {str(e)} - {url}")
            return None

    def check_rate_limit(self) -> Optional[str]:
        """Check GitHub API rate limit.

        Returns:
            Reset time string if rate limit exceeded, None otherwise
        """
        try:
            response = self.api_request(URLBuilder.github_rate_limit())
            if not response or "rate" not in response:
                raise Exception("Unable to get API rate limit info")

            reset = response["rate"]["reset"]
            remaining = response["rate"]["remaining"]

            self.logger.info(f"📊 GitHub API remaining requests: {remaining}")

            if remaining == 0:
                import time

                return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset))

            return None

        except Exception as e:
            self.logger.error(f"⚠️ Rate limit check failed: {str(e)}")
            return None

    def get_branch_info(self, repo: str, branch: str) -> Optional[Dict[str, Any]]:
        """Get branch information from repository.

        Args:
            repo: Repository name (owner/repo)
            branch: Branch name

        Returns:
            Branch information or None if not found
        """
        url = URLBuilder.github_branch(repo, branch)
        return self.api_request(url)

    def get_file_content(
        self, repo: str, branch: str, path: str
    ) -> Optional[Dict[str, Any]]:
        """Get file content from repository.

        Args:
            repo: Repository name (owner/repo)
            branch: Branch name
            path: File path

        Returns:
            File content as JSON or None if failed
        """
        url = URLBuilder.github_raw(repo, branch, path)
        return self.api_request(url)

    def download_file(self, repo: str, branch: str, path: str) -> Optional[bytes]:
        """Download file content from repository.

        Args:
            repo: Repository name (owner/repo)
            branch: Branch name
            path: File path

        Returns:
            File content as bytes or None if failed
        """
        url = URLBuilder.github_raw(repo, branch, path)
        return self.download_raw_content(url)
