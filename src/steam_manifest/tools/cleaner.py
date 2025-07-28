"""Git repository history cleaner for Steam Manifest repositories."""

import sys
from typing import Dict, Optional
from pathlib import Path

from git import GitCommandError, Repo

from ..utils.git_helper import sync_remote_branches


class RepositoryCleaner:
    """Cleans Git repository branch history."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize repository cleaner.
        
        Args:
            repo_path: Path to Git repository, defaults to current directory
        """
        self.repo_path = repo_path or Path.cwd()
        self.repo = Repo(self.repo_path)
    
    def process_branch(self, branch_name: str) -> None:
        """Process single Git branch, resetting its history.

        Args:
            branch_name: Name of the branch to process
        """
        try:
            self.repo.git.checkout('-f', branch_name)
            print(f'Switched to branch {branch_name}')
        except GitCommandError as e:
            print(f'Unable to switch to branch {branch_name}: {e}')
            return

        try:
            # Get current commit information
            tree_hash = self.repo.git.rev_parse('HEAD^{tree}')
            original_author = self.repo.git.log('-1', '--format=%an <%ae>', 'HEAD').strip()
            original_date = self.repo.git.log('-1', '--format=%aI', 'HEAD').strip()

            # Prepare environment variables for new commit
            env_vars: Dict[str, str] = {
                'GIT_AUTHOR_NAME': original_author.split('<')[0].strip(),
                'GIT_AUTHOR_EMAIL': original_author.split('<')[1].strip('> '),
                'GIT_AUTHOR_DATE': original_date,
                'GIT_COMMITTER_NAME': 'github-actions[bot]',
                'GIT_COMMITTER_EMAIL': 'github-actions[bot]@users.noreply.github.com'
            }
            
            # Create new commit with original tree
            new_commit = self.repo.git.commit_tree(
                tree_hash, 
                '-m', 'first commit', 
                env=env_vars
            ).strip()

            # Reset branch history to new commit
            self.repo.git.reset('--hard', new_commit)
            print(f'Reset history for branch {branch_name}')
            
        except GitCommandError as e:
            print(f'Error processing branch {branch_name}: {e}')
            raise
    
    def clean_all_branches(self) -> None:
        """Clean history for all branches except main."""
        # Sync remote branches first
        sync_remote_branches(self.repo)
        
        # Get all local branches except main
        local_branches = [head.name for head in self.repo.heads if head.name != 'main']
        print(f'Total branches to process: {len(local_branches)}')

        # Save current branch
        original_branch = self.repo.active_branch.name
        print(f'Current original branch: {original_branch}')

        try:
            # Process each branch
            for branch in local_branches:
                self.process_branch(branch)
                
        except GitCommandError as e:
            print(f'Processing failed: {e}')
            # Try to restore original branch
            try:
                self.repo.git.checkout('-f', original_branch)
            except GitCommandError:
                pass
            raise
        finally:
            # Restore original branch
            try:
                self.repo.git.checkout('-f', original_branch)
                print(f'Restored to original branch {original_branch}')
            except GitCommandError as e:
                print(f'Failed to restore original branch: {e}')

    def force_push_all_branches(self) -> None:
        """Force push all branches to remote repository."""
        try:
            print('Force pushing all branches...')
            self.repo.git.push('origin', '--all', '--force')
            print('Successfully force pushed all branches to remote repository.')
        except GitCommandError as e:
            print(f'Failed to force push branches: {e}')
            raise


def clean_repository_history(repo_path: Optional[Path] = None) -> None:
    """Clean repository history and force push to remote.
    
    Args:
        repo_path: Path to Git repository, defaults to current directory
    """
    try:
        cleaner = RepositoryCleaner(repo_path)
        
        # Clean all branch histories
        cleaner.clean_all_branches()
        
        # Force push all branches
        cleaner.force_push_all_branches()
        
        print('Operation completed! All branch histories have been reset and force pushed to remote repository.')
        
    except Exception as e:
        print(f'Operation failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    clean_repository_history()