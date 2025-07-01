"""Git仓库同步工具，用于同步远程仓库的分支到本地"""

from typing import Optional

from git import Head, Reference, Remote, Repo
from git.exc import GitCommandError


def sync_remote_branches(repo: Repo, remote_name: str = 'origin') -> None:
    """同步远程仓库的所有分支到本地

    Args:
        repo: Git仓库实例
        remote_name: 远程仓库名称，默认为'origin'

    Raises:
        ValueError: 当仓库中没有配置远程仓库时抛出
    """
    # 获取远程仓库
    if not repo.remotes:
        raise ValueError("仓库中没有配置远程仓库")

    origin: Remote = repo.remotes[remote_name]

    try:
        # 获取远程最新信息
        print(f"正在从 {remote_name} 拉取更新...")
        origin.fetch()
        print("拉取完成")
    except GitCommandError as e:
        print(f"拉取远程仓库时出错: {e}")
        return

    # 遍历所有远程分支
    for remote_ref in origin.refs:
        # 提取远程分支名（例如 origin/master -> master）
        remote_branch_name: str = remote_ref.remote_head

        # 跳过 HEAD 引用
        if remote_branch_name == 'HEAD':
            continue

        # 检查本地是否存在对应分支
        if remote_branch_name in repo.heads:
            local_branch: Head = repo.heads[remote_branch_name]
            tracking_branch: Optional[Reference] = local_branch.tracking_branch()
            # 如果已存在但未跟踪正确分支，则更新跟踪分支
            if tracking_branch != remote_ref:
                local_branch.set_tracking_branch(remote_ref)
                print(f"更新本地分支 {remote_branch_name} 跟踪分支为 {remote_ref}")
            continue

        # 创建本地分支并设置跟踪
        try:
            local_branch = repo.create_head(remote_branch_name, remote_ref)
            local_branch.set_tracking_branch(remote_ref)
            print(f"已创建本地分支 {remote_branch_name} 并跟踪 {remote_name}/{remote_branch_name}")
        except GitCommandError as e:
            print(f"创建分支 {remote_branch_name} 失败: {e}")
