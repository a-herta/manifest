"""Git repository helper utilities."""

from typing import Optional

from git import Head, Reference, Remote, Repo
from git.exc import GitCommandError


def sync_remote_branches(repo: Repo, remote_name: str = "origin") -> None:
    """Synchronize all remote repository branches to local.

    Args:
        repo: Git repository instance
        remote_name: Remote repository name, defaults to 'origin'

    Raises:
        ValueError: When repository has no configured remotes
    """
    # Get remote repository
    if not repo.remotes:
        raise ValueError("Repository has no configured remotes")

    origin: Remote = repo.remotes[remote_name]

    try:
        # Fetch latest remote information
        print(f"Fetching updates from {remote_name}...")
        origin.fetch()
        print("Fetch completed")
    except GitCommandError as e:
        print(f"Error fetching remote repository: {e}")
        return

    # Iterate through all remote branches
    for remote_ref in origin.refs:
        # Extract remote branch name (e.g., origin/master -> master)
        remote_branch_name: str = remote_ref.remote_head

        # Skip HEAD reference
        if remote_branch_name == "HEAD":
            continue

        # Check if local branch exists
        if remote_branch_name in repo.heads:
            local_branch: Head = repo.heads[remote_branch_name]
            tracking_branch: Optional[Reference] = local_branch.tracking_branch()

            # If exists but tracking wrong branch, update tracking branch
            if tracking_branch != remote_ref:
                local_branch.set_tracking_branch(remote_ref)
                print(
                    f"Updated local branch {remote_branch_name} to track {remote_ref}"
                )
            continue

        # Create local branch and set tracking
        try:
            local_branch = repo.create_head(remote_branch_name, remote_ref)
            local_branch.set_tracking_branch(remote_ref)
            print(
                f"Created local branch {remote_branch_name} tracking {remote_name}/{remote_branch_name}"
            )
        except GitCommandError as e:
            print(f"Failed to create branch {remote_branch_name}: {e}")
