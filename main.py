import logging
import os
import subprocess
import sys
import time
import winreg
from argparse import ArgumentParser, Namespace
from datetime import datetime
from multiprocessing import Lock, pool
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import vdf
from colorama import Fore, init
from colorlog import ColoredFormatter
from retrying import retry

from constants import (
    DEFAULT_REPOS,
    Files,
    HTTP_HEADERS,
    LOG_FORMAT,
    MAX_WORKERS,
    RETRY_INTERVAL,
    RETRY_TIMES,
    Steam,
    TIMEOUT,
    URLs,
    VERSION,
)

# Initialize colorama
init(autoreset=True)


def show_banner():
    print(
        rf"""
         ('-. .-.   ('-.  _  .-')   .-') _      ('-.     
        ( OO )  / _(  OO)( \( -O ) (  OO) )    ( OO ).-. 
        ,--. ,--.(,------.,------. /     '._   / . --. / 
        |  | |  | |  .---'|   /`. '|'--...__)  | \-.  \  
        |   .|  | |  |    |  /  | |'--.  .--'.-'-'  |  | 
        |       |(|  '--. |  |_.' |   |  |    \| |_.'  | 
        |  .-.  | |  .--' |  .  '.'   |  |     |  .-.  | 
        |  | |  | |  `---.|  |\  \    |  |     |  | |  | 
        `--' `--' `------'`--' '--'   `--'     `--' `--' 
        """
    )


def init_command_args() -> Namespace:
    """初始化命令行参数"""
    parser = ArgumentParser(description="🚀 Steam 清单文件获取工具")
    parser.add_argument("-v", "--version", action="version", version=f"📦 %(prog)s v{VERSION}")
    parser.add_argument("-a", "--appid", help="🎮 Steam 应用ID")
    parser.add_argument("-k", "--key", help="🔑 GitHub API 访问密钥")
    parser.add_argument("-r", "--repo", help="📁 GitHub 仓库名称")
    parser.add_argument("-f", "--fixed", action="store_true", help="📌 固定清单模式")
    parser.add_argument("-d", "--debug", action="store_true", help="🔍 调试模式")
    return parser.parse_args()


def remove_duplicates(tuples: List[Tuple[int, Optional[str]]]) -> List[Tuple[int, Optional[str]]]:
    """移除重复的仓库记录，优先保留带密钥的记录"""
    result_dict = {}
    for t in tuples:
        if t[0] not in result_dict or (result_dict[t[0]][1] is None and t[1] is not None):
            result_dict[t[0]] = t
    return list(result_dict.values())


def custom_input(prompt: str) -> str:
    """自定义输入函数，支持颜色和格式化"""
    input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    prompt = f"{Fore.CYAN} {input_time} [INPUT] {prompt}"
    return input(prompt)


class MainApp:
    def __init__(self):
        """初始化应用程序"""
        try:
            self.lock = Lock()
            self.args = init_command_args()
            self.logger = self.init_logger()
            self.appinfo = self.init_appid()
            self.manifests: List[str] = []
            self.depots: List[Tuple[int, Optional[str]]] = []
        except Exception as e:
            self.logger.error(f"⚠️ 程序初始化失败: {e}")
            sys.exit(1)

    def init_logger(self) -> logging.Logger:
        """初始化日志系统"""
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.args.debug else logging.INFO)
        return logger

    def init_appid(self) -> List[str]:
        """初始化游戏ID"""
        try:
            appid = self.args.appid or custom_input('请输入游戏名称/ID:')
            return [str(appid)] if appid.isdigit() else self.query_app_id(appid)
        except KeyboardInterrupt:
            exit()

    def query_app_id(self, name: str) -> List[str]:
        """查询Steam应用ID
        Args:
            name: Steam应用
        Returns:
            List[str]: 应用ID
        """
        try:
            # 获取游戏信息
            game_res = self.api_request(URLs.steam_search(name))
            if not game_res or "items" not in game_res:
                raise Exception("未检索游戏信息")

            game_list: List[Dict[str, Any]] = game_res['items']
            if not game_list:
                raise Exception("未检索游戏信息")

            self.logger.info("🎯 检索到以下游戏:")
            for idx, game in enumerate(game_list, 1):
                self.logger.info(f"📌 {idx}. [{game['id']}] [{game['type']}] {game['name']}")
            if len(game_list) != 1:
                time.sleep(1)

                def retry_input():
                    text = custom_input('请选择游戏序号:')
                    if text.isdigit() and 1 <= int(text) <= len(game_list):
                        return text
                    else:
                        self.logger.warning("⚠️ 输入无效，请重新选择")
                        return retry_input()

                choice = retry_input()
                selected: dict = game_list[int(choice) - 1]
            else:
                selected: dict = game_list[0]
            game_id = selected['id']
            self.logger.info(f"✨ 已选择游戏: [{game_id}] {selected['name']}")
            return [str(game_id)]
        except Exception as e:
            self.logger.error(f"❌ 搜索游戏时发生错误: {str(e)}")
            time.sleep(1)
            exit()

    def execute(self):
        """执行主程序"""
        steam_path = self.verify_steam_path()
        if not steam_path:
            self.logger.error("❌ 未找到Steam安装路径")
            return

        reset_time = self.verify_rate_limit()
        if reset_time:
            self.logger.error(f"❌ API请求次数已达上限，重置时间: {reset_time}")
            return

        curr_repo = self.verify_latest_repository()
        if not curr_repo:
            self.logger.error(f"❌ 仓库中未找到AppID: {self.appinfo[0]} 的数据")
            return

        try:
            self.handle_repository(curr_repo, self.appinfo[0], steam_path)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            self.logger.error(f"❌ 发生错误: {str(e)}")

        if not self.args.appid:
            time.sleep(0.1)
            subprocess.call("pause", shell=True)

    def verify_steam_path(self) -> Optional[Path]:
        """验证Steam安装路径"""
        try:
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, Steam.REG_PATH)
            steam_path = Path(winreg.QueryValueEx(hkey, Steam.REG_KEY)[0])
            if Files.STEAM_EXE in os.listdir(steam_path):
                self.logger.info(f"🎮 已定位Steam安装路径: {steam_path}")
                return steam_path
            self.logger.error("⛔ Steam安装目录验证失败")
            return None
        except FileNotFoundError:
            self.logger.error("⛔ 未检测到Steam安装环境")
            return None
        except Exception as e:
            self.logger.error(f"⛔ Steam路径验证异常: {str(e)}")
            return None

    def verify_rate_limit(self) -> Optional[str]:
        """验证GitHub API访问限制"""
        try:
            limit_res = self.api_request(URLs.GITHUB_RATE_LIMIT)
            if not limit_res or "rate" not in limit_res:
                raise Exception("无法获取API限制信息")
            reset = limit_res['rate']['reset']
            remaining = limit_res['rate']['remaining']
            self.logger.info(f"📊 GitHub API剩余请求次数: {remaining}")
            reset_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset))
            if remaining == 0:
                return reset_time
            return None
        except Exception as e:
            self.logger.error(f"⚠️ API限制检查异常: {str(e)}")
            return None

    def verify_latest_repository(self) -> Optional[str]:
        """验证最新清单仓库数据"""
        try:
            last_date: Optional[str] = None
            curr_repo: Optional[str] = None
            repos = DEFAULT_REPOS.copy()
            if self.args.repo:
                repos.insert(0, self.args.repo)
            for repo in repos:
                try:
                    branch_res = self.api_request(
                        URLs.github_branch(repo, self.appinfo[0]))
                    if not branch_res or "commit" not in branch_res:
                        self.logger.debug(f"📝 仓库中未找到匹配的分支: {repo}")
                        continue
                    date = branch_res['commit']['commit']['committer']['date']
                    if not last_date or last_date < date:
                        last_date = date
                        curr_repo = repo
                except Exception as e:
                    self.logger.warning(f"⚠️ 检查仓库 {repo} 时发生错误: {str(e)}")
                    continue
            if curr_repo:
                self.logger.info(f"📦 使用清单仓库: {curr_repo}")
            return curr_repo
        except Exception as e:
            self.logger.error(f"❌ 查找最新仓库时发生错误: {str(e)}")
            return None

    def handle_repository(self, repo: str, branch: str, steam_path: Path, is_dlc: bool = False):
        """处理仓库分支"""
        try:
            self.depots.append((int(branch), None))
            # 获取分支信息
            branch_res = self.api_request(URLs.github_branch(repo, branch))
            if not branch_res or "commit" not in branch_res:
                self.logger.warning(f"⚠️ 仓库 {repo} 中未找到分支 {branch}")
                return

            # 获取文件树
            commit_date = branch_res['commit']['commit']['committer']['date']
            tree_url = branch_res['commit']['commit']['tree']['url']
            tree_res = self.api_request(tree_url)
            if not tree_res or "tree" not in tree_res:
                self.logger.warning(f"⚠️ 分支 {branch} 中未找到文件详情")
                return

            # 使用线程池处理文件
            files = tree_res['tree']
            with pool.ThreadPool(MAX_WORKERS) as tpool:
                tasks = []
                for tree in files:
                    task = tpool.apply_async(self.process_manifest_file, (repo, branch, tree['path'], steam_path))
                    tasks.append(task)

                try:
                    for task in tasks:
                        task.get(timeout=TIMEOUT)

                except KeyboardInterrupt:
                    self.logger.warning("⚠️ 操作已被用户中断")
                    with self.lock:
                        tpool.terminate()
                    raise
                except TimeoutError:
                    self.logger.error(f"❌ 处理分支 {branch} 超时")
                    return
                except Exception as e:
                    self.logger.error(f"❌ 处理分支 {branch} 时发生错误: {str(e)}")
                    return

            if Files.CONFIG_JSON not in [t['path'] for t in files]:
                self.logger.info("🔍 正在从Steam商店获取DLC信息...")
                ddlc = self.query_steam_dlc(branch)
                if ddlc:
                    self.logger.info(f"🎯 检测到DLC内容: {ddlc}")
                    for dlc in ddlc:
                        time.sleep(2)
                        self.handle_repository(repo, str(dlc), steam_path, True)

            # 如果不是处理DLC且所有任务成功，保存信息
            if all(task.successful() for task in tasks) and not is_dlc:
                self.store_app_info(steam_path)
                self.logger.info(f"📅 成功入库: {self.appinfo}, 最后更新时间: {commit_date}")

        except Exception as e:
            self.logger.error(f"❌ 处理仓库 {repo} 分支 {branch} 时发生错误: {str(e)}")
            raise

    def query_steam_dlc(self, appid: str) -> List[int]:
        """获取Steam DLC信息
        Args:
            appid: Steam应用ID
        Returns:
            List[int]: DLC ID列表
        """
        try:
            detail_res = self.api_request(URLs.steam_app_details(appid))
            if not detail_res or not isinstance(detail_res, dict):
                return []

            app_data = detail_res.get(appid, {})
            if not app_data.get("success"):
                self.logger.warning(f"⚠️ 无法获取游戏信息: {appid}")
                return []

            appname = app_data.get("data", {}).get("name", "")
            self.appinfo.append(appname)

            dlc_data = app_data.get("data", {}).get("dlc", [])
            if dlc_data:
                self.logger.info(f"🎮 已从Steam商店获取DLC信息: {dlc_data}")
                dlc_data = [int(dlc_id) for dlc_id in dlc_data]
                self.depots.extend((dlc_id, None) for dlc_id in dlc_data)
            return dlc_data
        except ValueError as e:
            self.logger.error(f"❌ DLC ID格式无效: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ 获取DLC信息时发生错误: {e}")
            return []

    def process_manifest_file(self, repo: str, branch: str, path: str, steam_path: Path):
        """
        处理清单文件
        Args:
            repo: 仓库名称
            branch: 分支名称
            path: 文件路径
            steam_path: Steam安装路径
        """
        try:
            url = URLs.github_raw(repo, branch, path)
            with self.lock:
                self.logger.debug(f"📄 正在处理文件: {path}")

            # 处理清单文件
            if path.endswith(Files.MANIFEST_SUFFIX):
                self.store_manifest_file(path, steam_path, url)
            elif path.endswith(".vdf"):
                self.handle_vdf_file(path, url)
            elif path.endswith(".json") and path == Files.CONFIG_JSON:
                self.handle_conf_file(repo, steam_path, url)

        except Exception as e:
            self.logger.error(f"❌ 处理文件 {path} 时发生错误: {str(e)}")
            raise

    def store_manifest_file(self, path: str, steam_path: Path, url: str):
        """保存清单文件"""
        self.manifests.append(path)
        depot_cache = steam_path / Steam.DEPOT_CACHE
        depot_cache.mkdir(parents=True, exist_ok=True)
        save_path = depot_cache / path

        if save_path.exists():
            self.logger.warning(f"⚠️ 清单文件已存在: {path}")
            return

        manifest_res = self.raw_content(url)
        if manifest_res is not None:
            temp_path = save_path.with_suffix('.tmp')
            try:
                temp_path.write_bytes(manifest_res)
                temp_path.replace(save_path)
                self.logger.info(f"📥 清单文件已下载: {path}")
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise e

    def handle_vdf_file(self, path: str, url: str):
        """处理VDF文件"""
        try:
            content = self.raw_content(url)
            if content is None:
                return

            if path == Files.APPINFO_VDF:
                self.parse_appinfo_vdf(content)
            elif path == Files.KEY_VDF:
                self.parse_key_vdf(content)

        except Exception as e:
            self.logger.error(f"❌ 处理VDF文件时发生错误: {str(e)}")
            raise

    def parse_appinfo_vdf(self, content: bytes):
        """解析 appinfo.vdf 文件"""
        try:
            appinfo_config = vdf.loads(content.decode())
            appinfo_dict: Dict[str, str] = appinfo_config['common']
            appname = appinfo_dict['name']
            self.appinfo.append(appname)
        except Exception as e:
            self.logger.error(f"⛔ 解析 appinfo.vdf 失败: {str(e)}")
            raise

    def parse_key_vdf(self, content: bytes):
        """解析 key.vdf 文件"""
        try:
            depot_config = vdf.loads(content.decode())
            depot_dict: Dict = depot_config['depots']
            self.depots.extend(
                (int(k), v['DecryptionKey'])
                for k, v in depot_dict.items()
            )
            self.logger.info("🔑 已找到解密密钥")
        except Exception as e:
            self.logger.error(f"⛔ 解析 key.vdf 失败: {str(e)}")
            raise

    def handle_conf_file(self, repo: str, steam_path: Path, url: str):
        """处理配置文件"""
        try:
            config_res = self.api_request(url)
            if not config_res:
                raise Exception("无法获取配置文件")

            dlcs: List[int] = config_res.get("dlcs", [])
            ddlc: List[int] = config_res.get("packagedlcs", [])

            if dlcs:
                self.logger.info(f"🎮 检测到DLC内容: {dlcs}")
                self.depots.extend((k, None) for k in dlcs)

            if ddlc:
                self.logger.info(f"🎯 检测到独立DLC: {ddlc}")
                for dlc in ddlc:
                    self.handle_repository(repo, str(dlc), steam_path, True)

        except Exception as e:
            self.logger.error(f"❌ 获取配置文件时发生错误: {str(e)}")

    def store_app_info(self, path: Path) -> None:
        """保存应用程序信息"""
        try:
            # 移除重复并排序仓库记录
            depot_list = sorted(set(self.depots), key=lambda x: x[0])
            depot_list = remove_duplicates(depot_list)

            # 生成lua内容
            lua_content = ""
            if len(self.appinfo) > 1:
                lua_content = f"-- {self.appinfo[1]}\n"

            # 添加appid信息
            lua_content += "".join(
                (
                    f'addappid({depot_id}, 1, "{depot_key}")\n'
                    if depot_key
                    else f"addappid({depot_id}, 1)\n"
                )
                for depot_id, depot_key in depot_list
            )

            # 如果启用了固定模式，添加清单信息
            if self.args.fixed:
                manifest_list = sorted(
                    [
                        (split_x[0], split_x[1].split(".")[0])
                        for split_x in (x.split("_") for x in self.manifests)
                    ],
                    key=lambda x: x[0],
                )
                lua_content += "".join(
                    f'setManifestid({depot_id}, "{manifest_id}")\n'
                    for depot_id, manifest_id in manifest_list
                )

            # 保存到文件
            lua_filename = f"{self.appinfo[0]}.lua"
            lua_path = path / Steam.PLUGIN_DIR
            lua_path.mkdir(parents=True, exist_ok=True)
            lua_filepath = lua_path / lua_filename

            # 使用临时文件确保写入完整性
            temp_filepath = lua_filepath.with_suffix('.tmp')
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                f.write(lua_content)
            temp_filepath.replace(lua_filepath)  # 原子操作

            self.logger.info(f"📝 配置已保存至: {lua_filepath}")
        except Exception as e:
            self.logger.error(f"❌ 保存配置文件时发生错误: {str(e)}")

    @retry(wait_fixed=RETRY_INTERVAL, stop_max_attempt_number=RETRY_TIMES)
    def api_request(self, url: str) -> Dict[str, Any] | None:
        """
        发送HTTP GET请求并获取JSON响应
        参数:
            url: 请求URL
        返回:
            Dict[str, Any] | None: JSON响应数据或请求失败时返回None
        """
        try:
            github_token = os.getenv("GITHUB_API_TOKEN") or self.args.key
            with httpx.Client(
                    timeout=TIMEOUT,
                    headers={
                        **HTTP_HEADERS,
                        "Authorization": f"Bearer {github_token}" if github_token else "",
                    },
                    follow_redirects=True
            ) as client:
                with self.lock:
                    self.logger.debug(f"📡 正在发送请求: {url}")

                result = client.get(url)

                # 处理特殊状态码
                if result.status_code == 429:  # 请求频率限制
                    reset_time = result.headers.get("X-RateLimit-Reset")
                    if reset_time:
                        reset_time = datetime.fromtimestamp(int(reset_time))
                        wait_time = (reset_time - datetime.now()).total_seconds()
                        self.logger.warning(f"⚠️ 已达到请求限制，将在 {wait_time:.0f} 秒后重试")
                    raise Exception("已达到请求频率限制")
                elif result.status_code == 404:
                    self.logger.debug(f"⚠️ 未找到资源: {url}")
                    return None

                result.raise_for_status()
                json_data = result.json()

                with self.lock:
                    self.logger.debug(f"📥 收到响应数据: {len(str(json_data))} 字节")
                return json_data

        except httpx.TimeoutException:
            self.logger.error(f"⌛ 请求超时: {url}")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"🔧 HTTP请求失败: {e.response.status_code} - {url}")
        except Exception as e:
            self.logger.error(f"❌ 请求异常: {str(e)} - {url}")
            return None

    @retry(wait_fixed=RETRY_INTERVAL, stop_max_attempt_number=RETRY_TIMES)
    def raw_content(self, url: str) -> bytes | None:
        """
        下载原始内容
        参数:
            url: 请求URL
        返回:
            bytes | None: 二进制响应数据或下载失败时返回None
        """
        try:
            with httpx.Client(
                    timeout=TIMEOUT,
                    headers=HTTP_HEADERS,
                    follow_redirects=True
            ) as client:
                with self.lock:
                    self.logger.debug(f"📥 正在下载: {url}")

                result = client.get(url)
                result.raise_for_status()

                content = result.content
                with self.lock:
                    self.logger.debug(f"✅ 下载完成: {len(content)} 字节")
                return content

        except Exception as e:
            self.logger.error(f"❌ 下载失败: {str(e)} - {url}")
            return None


if __name__ == "__main__":
    show_banner()
    MainApp().execute()
