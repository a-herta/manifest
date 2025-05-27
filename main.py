import logging
import os
import subprocess
import time
import winreg
from argparse import ArgumentParser
from datetime import datetime
from multiprocessing import Lock, pool
from pathlib import Path

import httpx
import vdf
from colorama import Fore
from colorlog import ColoredFormatter
from retrying import retry


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


def init_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s v{version}"
    )
    parser.add_argument("-a", "--appid", help="steam appid")
    parser.add_argument("-k", "--key", help="github API key")
    parser.add_argument("-r", "--repo", help="github repo name")
    parser.add_argument("-f", "--fixed", action="store_true", help="fixed manifest")
    parser.add_argument("-d", "--debug", action="store_true", help="debug mode")
    return parser.parse_args()


def remove_duplicates(tuples: list[tuple[int, str | None]]):
    result_dict = {}
    for t in tuples:
        if t[0] not in result_dict or (
                result_dict[t[0]][1] is None and t[1] is not None
        ):
            result_dict[t[0]] = t
    return list(result_dict.values())


class MainApp:
    def __init__(self):
        self.args = init_args()
        self.logr = self.init_logger()
        self.manifests: list[str] = []
        self.depots: list[tuple[int, str | None]] = []
        self.lock = Lock()
        self.appinfo = self.get_appinfo()

    def init_logger(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            "%(log_color)s %(asctime)s [%(levelname)s] [%(thread)d] %(message)s"
        )
        handler.setFormatter(formatter)
        level = logging.DEBUG if self.args.debug else logging.INFO
        logger.addHandler(handler)
        logger.setLevel(level)
        return logger

    def get_repos(self):
        repo_list = [
            "a-herta/manifest",
            "SteamAutoCracks/ManifestHub"
        ]
        repo = self.args.repo
        if repo:
            repo_list.insert(0, repo)
        return repo_list

    def get_app_id(self, name: str):
        games: list = self.check_game_list(name)
        if not games:
            self.logr.error(f"⛔ 未检索到游戏信息, 请重试")
            time.sleep(1)
            exit()
        self.logr.info("🔍 检索到以下游戏:")

        def get_name(data: dict):
            return data["schinese_name"] if data["schinese_name"] else data["name"]

        for idx, game in enumerate(games, 1):
            self.logr.info(f"🔄️ {idx}.[{game['appid']}] {get_name(game)}")
        if len(games) != 1:
            time.sleep(1)

            def retry_input():
                input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                prompt = f"{Fore.CYAN} {input_time} [INPUT] 📝 请输入游戏编号: "
                text = input(prompt)
                if text.isdigit() and 1 <= int(text) <= len(games):
                    return text
                else:
                    self.logr.warning(f"⛔ 输入有误")
                    return retry_input()

            choice = retry_input()
            selected: dict = games[int(choice) - 1]
        else:
            selected: dict = games[0]
        game_id = selected["appid"]
        game_name = get_name(selected)
        self.logr.info(f"✅ 已选择: [{game_id}] {game_name}")
        return [game_id]

    def get_appinfo(self):
        input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        prompt = f"{Fore.CYAN} {input_time} [INPUT] 📝 请输入游戏名/ID: "
        try:
            appid = self.args.appid or input(prompt)
            return [appid] if appid.isdigit() else self.get_app_id(appid)
        except KeyboardInterrupt:
            exit()

    def run(self):
        steam_path = self.check_steam_path()
        if not steam_path:
            self.logr.error(f"⛔ Steam路径不存在")
            return
        reset_time = self.check_api_limit()
        if reset_time:
            self.logr.error(f"⛔ 请求次数已用尽, 重置时间: {reset_time}")
            return
        curr_repo = self.check_curr_repo()
        if not curr_repo:
            self.logr.error(f"⛔ 仓库暂无数据, 入库失败: {self.appinfo[0]}")
            return
        try:
            self.start(curr_repo, self.appinfo[0], steam_path)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            self.logr.error(f"⛔ 出现异常: {e}")
        if not self.args.appid:
            self.logr.critical("🛑 运行结束")
            time.sleep(0.1)
            subprocess.call("pause", shell=True)

    def check_steam_path(self):
        try:
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path = Path(winreg.QueryValueEx(hkey, "SteamPath")[0])
            if "steam.exe" in os.listdir(steam_path):
                self.logr.info(f"🚩 检测到Steam: {steam_path}")
                return steam_path
            return None
        except Exception as e:
            self.logr.error(e)
            return None

    def check_api_limit(self):
        try:
            api_url = os.getenv("GITHUB_API_URL") or "https://api.github.com/rate_limit"
            limit_res = self.api_request(api_url)
            reset = limit_res["rate"]["reset"]
            remaining = limit_res["rate"]["remaining"]
            self.logr.info(f"🙌 剩余请求次数: {remaining}")
            reset_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset))
            if remaining == 0:
                return reset_time
            return None
        except Exception as e:
            self.logr.error(f"⛔ 检查API限制时出现异常: {e}")
            return None

    def check_game_list(self, name: str):
        game_res = self.api_request(f"https://steamui.com/loadGames.php?search={name}")
        return game_res["games"]

    def check_curr_repo(self):
        last_date = None
        curr_repo = None
        repos = self.get_repos()
        for repo in repos:
            branch_res = self.api_request(
                f"https://api.github.com/repos/{repo}/branches/{self.appinfo[0]}"
            )
            if branch_res and "commit" in branch_res:
                date = branch_res["commit"]["commit"]["committer"]["date"]
                if last_date is None or date > last_date:
                    last_date = date
                    curr_repo = repo
        self.logr.info(f"📦 当前清单仓库: {curr_repo}")
        return curr_repo

    def start(self, repo: str, branch: str, path: Path, is_dlc=False):
        self.depots.append((int(branch), None))
        branch_res = self.api_request(
            f"https://api.github.com/repos/{repo}/branches/{branch}"
        )
        if not branch_res or "commit" not in branch_res:
            return
        tree_url = branch_res["commit"]["commit"]["tree"]["url"]
        commit_date = branch_res["commit"]["commit"]["committer"]["date"]
        tree_res = self.api_request(tree_url)
        if not tree_res or "tree" not in tree_res:
            return
        with pool.ThreadPool() as tpool:
            tasks = [
                tpool.apply_async(self.manifest, (repo, branch, tree["path"], path))
                for tree in tree_res["tree"]
            ]
            try:
                for task in tasks:
                    task.get()
            except KeyboardInterrupt:
                with self.lock:
                    tpool.terminate()
                raise
        if all(task.successful() for task in tasks) and not is_dlc:
            self.set_appinfo(path)
            self.logr.info(f"⌛ 清单最后更新时间: {commit_date}")
            self.logr.info(f"🌟 入库成功: {self.appinfo}")

    def manifest(self, repo: str, branch: str, path: str, steam_path: Path):
        try:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            with self.lock:
                self.logr.debug(f"📄 处理文件: {path}")

            if path.endswith(".manifest"):
                self.manifests.append(path)
                depot_cache = steam_path / "config" / "depotcache"
                depot_cache.mkdir(parents=True, exist_ok=True)
                save_path = depot_cache / path
                if save_path.exists():
                    self.logr.warning(f"👋 清单已存在: {path}")
                    return
                manifest_res = self.raw_content(url)
                if manifest_res is not None:
                    save_path.write_bytes(manifest_res)
                    self.logr.info(f"💾 清单已下载: {path}")

            elif path.endswith(".vdf"):
                if path in ["appinfo.vdf"]:
                    info_res = self.raw_content(url)
                    appinfo_config = vdf.loads(info_res.decode())
                    appinfo_dict: dict[str, str] = appinfo_config["common"]
                    appname = appinfo_dict["name"]
                    self.appinfo.append(appname)
                elif path in ["key.vdf", "Key.vdf"]:
                    key_res = self.raw_content(url)
                    depot_config = vdf.loads(key_res.decode())
                    depot_dict: dict = depot_config["depots"]
                    self.depots.extend((int(k), v["DecryptionKey"]) for k, v in depot_dict.items())
                    self.logr.info(f"🔍 检索到密钥信息: {depot_dict}...")

            elif path.endswith(".json") and path in ["config.json"]:
                config_res = self.api_request(url)
                dlcs: list[int | str] = config_res.get("dlcs", [])
                ddlc: list[int | str] = config_res.get("packagedlcs", [])
                if dlcs:
                    self.logr.info(f"🔍 检索到DLC信息: {dlcs}...")
                    self.depots.extend((k, None) for k in dlcs)
                if ddlc:
                    self.logr.info(f"🔍 检索到独立DLC: {ddlc}...")
                    for dlc in ddlc:
                        self.start(repo, dlc, steam_path, True)

        except Exception as e:
            self.logr.error(f"⛔ 出现异常: {e}")
            raise

    def set_appinfo(self, path: Path):
        depot_list = sorted(set(self.depots), key=lambda x: x[0])
        depot_list = remove_duplicates(depot_list)
        lua_content = ""
        if len(self.appinfo) > 1:
            lua_content = f"-- {self.appinfo[1]}\n"
        lua_content += "".join(
            (
                f'addappid({depot_id}, 1, "{depot_key}")\n'
                if depot_key
                else f"addappid({depot_id}, 1)\n"
            )
            for depot_id, depot_key in depot_list
        )
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
        lua_filename = f"{self.appinfo[0]}.lua"
        lua_path = path / "config" / "stplug-in"
        lua_path.mkdir(parents=True, exist_ok=True)
        lua_filepath = lua_path / lua_filename
        with open(lua_filepath, 'w', encoding='utf-8') as f:
            f.write(lua_content)
        self.logr.info(f"💎 解锁信息已保存: {lua_filepath}")

    @retry(wait_fixed=5000, stop_max_attempt_number=10)
    def api_request(self, url: str):
        with httpx.Client() as client:
            with self.lock:
                self.logr.debug(f"📍 请求地址: {url}")
            token = os.getenv("GITHUB_API_TOKEN") or self.args.key
            headers = {"Authorization": f"Bearer {token}" if token else ""}
            result = client.get(url, headers=headers, follow_redirects=True)
            json: dict = result.json()
            if result.status_code == 200:
                with self.lock:
                    self.logr.debug(f"📥 成功结果: {json}")
                return json
            return None

    @retry(wait_fixed=5000, stop_max_attempt_number=10)
    def raw_content(self, url: str):
        with httpx.Client() as client:
            with self.lock:
                self.logr.debug(f"📤 请求内容: {url}")
            result = client.get(url, follow_redirects=True)
            if result.status_code == 200:
                return result.content
            return None


if __name__ == "__main__":
    version = "3.5.0"
    show_banner()
    MainApp().run()
