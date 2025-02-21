import datetime
import os
import re
import vdf

from git import Repo, GitCommandError, Actor
from repo import sync_remote_branches


def is_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def is_japanese(text):
    return bool(re.search(r'[\u3040-\u30ff]', text))


def append_names(english, chinese, japanese):
    names = []
    if english and english not in names:
        names.append(english)
    if chinese and chinese not in names:
        names.append(chinese)
    if japanese and japanese not in names:
        names.append(japanese)
    final_name = '  <br/>'.join(names)
    return final_name


def process_branch(repo, branch, results):
    try:
        repo.git.checkout('-f', branch)
        print(f'切换到分支 {branch}')
    except GitCommandError as e:
        print(f'无法切换分支 {branch}: {e}')
        return

    vdf_path = 'appinfo.vdf'
    if not os.path.exists(vdf_path):
        print(f'分支 {branch} 不存在 appinfo.vdf')
        return

    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = vdf.load(f)
    except Exception as e:
        print(f'解析 {vdf_path} 失败: {e}')
        return

    common = data.get('common', {})
    depots = data.get('depots', {})
    appid = data.get('appid', '')
    type_ = common.get('type', '')

    if not appid or not type_:
        print(f'分支 {branch} 缺少 appid 或 type 字段')
        return

    name = common.get('name', '')
    name_localized = common.get('name_localized', {})

    english = name_localized.get('english', '')
    schinese = name_localized.get('schinese', '')
    tchinese = name_localized.get('tchinese', '')
    japanese = name_localized.get('japanese', '')
    if is_chinese(name):
        chinese_name = schinese or tchinese or name
        final_name = append_names(english, chinese_name, japanese)
    elif is_japanese(name):
        chinese_name = schinese or tchinese
        japanese_name = japanese or name
        final_name = append_names(english, chinese_name, japanese_name)
    else:
        english_name = english or name
        chinese_name = schinese or tchinese
        final_name = append_names(english_name, chinese_name, japanese)

    updated_time: str = depots.get('branches', {}).get('public', {}).get('timeupdated', {})
    updated = datetime.datetime.fromtimestamp(int(updated_time))

    stat_files = [f for f in os.listdir() if f.endswith('.bin')]
    stat = stat_files[0] if stat_files else None

    results[appid] = {
        'APPID': appid,
        '名称': final_name,
        '类型': type_,
        '成就': stat,
        '更新时间': updated
    }


def generate_readme(results):
    sorted_results = sorted(results.values(), key=lambda x: int(x['APPID']))
    table = ['| APPID | 名称 | 成就 | 类型 | 更新时间 |', '|-------|------|------|------|----------|']
    for item in sorted_results:
        db_info = f'[{item['APPID']}](https://steamdb.info/app/{item['APPID']})'
        stat_info = f'[✅](https://github.com/a-herta/manifest/blob/{item['APPID']}/{item['成就']})' if \
            item['成就'] else ''
        table.append(
            f'| {db_info} | {item['名称']} | {stat_info} | {item['类型']} | {item['更新时间']} |')
    return '\n'.join(table)


def commit_push(repo):
    # 提取原作者
    original_author = repo.git.log('-1', '--format=%an <%ae>', 'HEAD').strip()
    author = Actor(original_author.split('<')[0].strip(), original_author.split('<')[1].strip('> '))

    # 创建新提交
    repo.index.add(['README.md'])

    commit_msg = 'Update README.md'
    committer = Actor('github-actions[bot]', 'github-actions[bot]@users.noreply.github.com')

    repo.index.commit(commit_msg, author=author, committer=committer)
    remote = repo.remote(name="origin")
    remote.push(refspec="HEAD:main")

    print('README.md 已推送至远程仓库。')


def main():
    repo_path = os.getcwd()
    repo = Repo(repo_path)

    results = {}

    # 获取所有本地分支（排除主分支）
    sync_remote_branches(repo)
    local_branches = [head.name for head in repo.heads if head.name != 'main']
    print(f'共有待处理分支：{len(local_branches)}')

    # 保存当前原始分支
    original_branch = repo.active_branch.name
    print(f'当前原始分支: {original_branch}')

    try:
        for branch in local_branches:
            process_branch(repo, branch, results)
    finally:
        repo.git.checkout(original_branch)
        print(f'切换回原始分支 {original_branch}')

    # 生成README内容
    readme_content = generate_readme(results)

    # 写入文件
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print('操作完成！README.md 已生成')

    commit_push(repo)


if __name__ == '__main__':
    main()
