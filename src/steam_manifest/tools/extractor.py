"""Steam application information extractor for repository statistics."""

import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import vdf
from git import Actor, GitCommandError, Repo

from ..utils.git_helper import sync_remote_branches


def is_chinese(text: str) -> bool:
    """Check if text contains Chinese characters.

    Args:
        text: Text to check

    Returns:
        True if contains Chinese characters
    """
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def is_japanese(text: str) -> bool:
    """Check if text contains Japanese characters.

    Args:
        text: Text to check

    Returns:
        True if contains Japanese characters
    """
    return bool(re.search(r"[\u3040-\u30ff]", text))


def combine_multilingual_names(
    english: Optional[str], chinese: Optional[str], japanese: Optional[str]
) -> str:
    """Combine multilingual names with <br/> separator.

    Args:
        english: English name
        chinese: Chinese name
        japanese: Japanese name

    Returns:
        Combined multilingual name string
    """
    names: List[str] = []

    for name in [english, chinese, japanese]:
        if name and name not in names:
            names.append(name)

    return "  <br/>".join(names)


class RepositoryExtractor:
    """Extracts Steam application information from Git repository."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize repository extractor.

        Args:
            repo_path: Path to Git repository, defaults to current directory
        """
        self.repo_path = repo_path or Path.cwd()
        self.repo = Repo(self.repo_path)
        self.results: Dict[str, Dict[str, Any]] = {}

    def process_branch(self, branch_name: str) -> None:
        """Process single branch information.

        Args:
            branch_name: Name of the branch to process
        """
        try:
            self.repo.git.checkout("-f", branch_name)
            print(f"Switched to branch {branch_name}")
        except GitCommandError as e:
            print(f"Unable to switch to branch {branch_name}: {e}")
            return

        vdf_path = self.repo_path / "appinfo.vdf"
        if not vdf_path.exists():
            print(f"Branch {branch_name} does not contain appinfo.vdf")
            return

        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                data = vdf.load(f)
        except Exception as e:
            print(f"Failed to parse {vdf_path}: {e}")
            return

        # Extract application information
        common: Dict[str, Any] = data.get("common", {})
        depots: Dict[str, Any] = data.get("depots", {})
        app_id: str = data.get("appid", "")
        app_type: str = common.get("type", "")

        if not app_id or not app_type:
            print(f"Branch {branch_name} missing appid or type fields")
            return

        # Process names
        name: str = common.get("name", "")
        name_localized: Dict[str, str] = common.get("name_localized", {})

        english = name_localized.get("english", "")
        simplified_chinese = name_localized.get("schinese", "")
        traditional_chinese = name_localized.get("tchinese", "")
        japanese = name_localized.get("japanese", "")

        # Determine final name based on primary language
        if is_chinese(name):
            chinese_name = simplified_chinese or traditional_chinese or name
            final_name = combine_multilingual_names(english, chinese_name, japanese)
        elif is_japanese(name):
            chinese_name = simplified_chinese or traditional_chinese
            japanese_name = japanese or name
            final_name = combine_multilingual_names(
                english, chinese_name, japanese_name
            )
        else:
            english_name = english or name
            chinese_name = simplified_chinese or traditional_chinese
            final_name = combine_multilingual_names(
                english_name, chinese_name, japanese
            )

        # Get update time
        update_timestamp = (
            depots.get("branches", {}).get("public", {}).get("timeupdated", "")
        )
        if update_timestamp:
            updated = datetime.datetime.fromtimestamp(int(update_timestamp))
        else:
            updated = datetime.datetime.now()

        # Find achievement file
        achievement_files = [
            f for f in os.listdir(self.repo_path) if f.endswith(".bin")
        ]
        achievement_file = achievement_files[0] if achievement_files else None

        # Store results
        self.results[app_id] = {
            "APPID": app_id,
            "名称": final_name,
            "类型": app_type,
            "成就": achievement_file,
            "更新时间": updated,
        }

    def generate_readme_content(self) -> List[str]:
        """Generate README file content.

        Returns:
            List of README content lines
        """
        sorted_results = sorted(self.results.values(), key=lambda x: int(x["APPID"]))

        table_lines = [
            "| APPID | 名称 | 成就 | 类型 | 更新时间 |",
            "|-------|------|------|------|----------|",
        ]

        for item in sorted_results:
            db_link = f"[{item['APPID']}](https://steamdb.info/app/{item['APPID']})"

            achievement_link = (
                f"[✅](https://github.com/a-herta/manifest/blob/{item['APPID']}/{item['成就']})"
                if item["成就"]
                else ""
            )

            table_lines.append(
                f"| {db_link} | {item['名称']} | {achievement_link} | {item['类型']} | {item['更新时间']} |"
            )

        return table_lines

    def commit_and_push_readme(self) -> None:
        """Commit and push README.md to repository."""
        try:
            # Get original author info
            original_author = self.repo.git.log(
                "-1", "--format=%an <%ae>", "HEAD"
            ).strip()
            author_name = original_author.split("<")[0].strip()
            author_email = original_author.split("<")[1].strip("> ")
            author = Actor(author_name, author_email)

            # Stage and commit
            self.repo.index.add(["README.md"])

            commit_message = "Update README.md"
            committer = Actor(
                "github-actions[bot]", "github-actions[bot]@users.noreply.github.com"
            )

            self.repo.index.commit(commit_message, author=author, committer=committer)

            # Push to remote
            remote = self.repo.remote(name="origin")
            remote.push(refspec="HEAD:main")

            print("README.md has been pushed to remote repository.")

        except Exception as e:
            print(f"Error committing and pushing README.md: {e}")


def extract_repository_info(repo_path: Optional[Path] = None) -> None:
    """Extract repository information and generate README.

    Args:
        repo_path: Path to Git repository, defaults to current directory
    """
    extractor = RepositoryExtractor(repo_path)

    # Sync remote branches
    sync_remote_branches(extractor.repo)

    # Get all local branches except main
    local_branches = [head.name for head in extractor.repo.heads if head.name != "main"]
    print(f"Total branches to process: {len(local_branches)}")

    # Save current branch
    original_branch = extractor.repo.active_branch.name
    print(f"Current original branch: {original_branch}")

    try:
        # Process all branches
        for branch in local_branches:
            extractor.process_branch(branch)
    finally:
        # Return to original branch
        extractor.repo.git.checkout(original_branch)
        print(f"Switched back to original branch {original_branch}")

    # Generate and write README
    readme_content = extractor.generate_readme_content()
    readme_path = extractor.repo_path / "README.md"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_content))

    print("Operation completed! README.md has been generated")

    # Commit and push
    extractor.commit_and_push_readme()


if __name__ == "__main__":
    extract_repository_info()
