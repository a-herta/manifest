"""Git仓库清理工具，用于重置分支历史并推送到远程仓库"""

import os
import sys
from typing import Dict

from git import GitCommandError, Repo

from repo import sync_remote_branches


def process_branch(repo: Repo, branch: str) -> None:
    """处理单个Git分支，重置其历史

    Args:
        repo: Git仓库实例
        branch: 分支名称
    """
    try:
        repo.git.checkout('-f', branch)
        print(f'切换到分支 {branch}')
    except GitCommandError as e:
        print(f'无法切换分支 {branch}: {e}')
        return

    # 获取当前提交信息
    tree_hash = repo.git.rev_parse('HEAD^{tree}')
    original_author = repo.git.log('-1', '--format=%an <%ae>', 'HEAD').strip()
    original_date = repo.git.log('-1', '--format=%aI', 'HEAD').strip()

    # 创建新提交
    env: Dict[str, str] = {
        'GIT_AUTHOR_NAME': original_author.split('<')[0].strip(),
        'GIT_AUTHOR_EMAIL': original_author.split('<')[1].strip('> '),
        'GIT_AUTHOR_DATE': original_date,
        'GIT_COMMITTER_NAME': 'github-actions[bot]',
        'GIT_COMMITTER_EMAIL': 'github-actions[bot]@users.noreply.github.com'
    }
    new_commit = repo.git.commit_tree(tree_hash, '-m', 'first commit', env=env).strip()

    # 重置分支历史
    repo.git.reset('--hard', new_commit)


def main() -> None:
    """主函数，处理仓库中的所有分支"""
    # 打开本地仓库
    repo_path = os.getcwd()
    repo = Repo(repo_path)

    # 获取所有本地分支
    sync_remote_branches(repo)
    local_branches = [head.name for head in repo.heads if head.name != 'main']
    print(f'共有待处理分支：{len(local_branches)}')

    # 保存当前原始分支
    original_branch = repo.active_branch.name
    print(f'当前原始分支: {original_branch}')

    try:
        for branch in local_branches:
            process_branch(repo, branch)
    except GitCommandError as e:
        print(f'处理失败: {e}')
        repo.git.checkout('-f', original_branch)
        sys.exit(1)

    # 恢复原始分支状态
    repo.git.checkout('-f', original_branch)

    # 强制推送所有分支
    print('正在强制推送所有分支...')
    repo.git.push('origin', '--all', '--force')

    print('操作完成！所有分支历史已重置并强制推送到远程仓库。')


if __name__ == '__main__':
    main()
