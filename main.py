import sys
import requests
import pywikiapi as wiki
import time
import json
from datetime import datetime, timedelta

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

LOG_TYPE_MAP = {
    "newusers": "用户创建",
    "delete": "删除",
    "block": "封禁",
    "protect": "保护",
    "abusefilter": "滥用过滤器",
    "rights": "用户权限",
    "move": "移动"
}

LOG_ACTION_MAP = {
    "create": "创建",
    "upload": "上传",
    "delete": "删除",
    "move": "移动",
    "overwrite": "覆盖上传",
    "block": "封禁",
    "reblock": "更改封禁",
    "unblock": "解除封禁",
    "move_prot": "移动保护设置",
    "protect": "保护",
    "unprotect": "移除保护",
    "modify": "修改",
    "create2": "登录状态创建账号",
    "byemail": "登录状态创建账号2",
    "migrated": "迁移",
    "rights": "权限更改"
}

def format_timestamp(timestamp_str): # 将UTC时间改为UTC+8
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
    timestamp += timedelta(hours=8)
    return timestamp.strftime('%H:%M:%S')

def format_comment(comment): # 摘要为空时输出（空）而不是【】
    return f"（空）" if comment == "" else f"{Colors.CYAN}{comment}{Colors.RESET}"

def format_user(user, special_users): # 有巡查豁免权限的用户标记为绿色
    return f"{Colors.GREEN}{user}{Colors.RESET}" if user in special_users else f"{Colors.BLUE}{user}{Colors.RESET}"

def format_length_diff(newlen, oldlen):
    return f"+{newlen-oldlen}" if newlen - oldlen > 0 else f"{newlen-oldlen}"

def print_rc(new_data): # 解析新更改数据并输出
    if new_data:
        for item in new_data:
            length_difference = format_length_diff(item['newlen'], item['oldlen'])
            formatted_time = format_timestamp(item['timestamp'])
            comment_display = format_comment(item['comment'])
            user_display = format_user(item['user'], special_users)
            if item['type'] == 'log':
                logtype_display = LOG_TYPE_MAP.get(item['logtype'], item['logtype'])
                logaction_display = LOG_ACTION_MAP.get(item['logaction'], item['logaction'])
                if item['logtype'] == "upload":
                    print(f"（{Colors.MAGENTA}上传日志{Colors.RESET}）{Colors.CYAN}{formatted_time}{Colors.RESET}，{Colors.BLUE}{user_display}{Colors.RESET}对{Colors.BLUE}{item['title']}{Colors.RESET}执行了{Colors.MAGENTA}{logaction_display}{Colors.RESET}操作，摘要为{comment_display}。")
                    print(f"（{Colors.YELLOW}https://zh.minecraft.wiki/?diff={item['revid']}{Colors.RESET}）")
                    print(f"（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）",end='\n\n')
                elif item['logtype'] == "move":
                    print(f"（{Colors.MAGENTA}移动日志{Colors.RESET}）{Colors.CYAN}{formatted_time}{Colors.RESET}，{Colors.BLUE}{user_display}{Colors.RESET}对{Colors.BLUE}{item['title']}{Colors.RESET}执行了{Colors.MAGENTA}{logaction_display}{Colors.RESET}操作，摘要为{comment_display}。")
                    print(f"（{Colors.YELLOW}https://zh.minecraft.wiki/?diff={item['revid']}{Colors.RESET}）", end='\n\n')
                else:
                    print(f"（{Colors.MAGENTA}{logtype_display}日志{Colors.RESET}）{Colors.CYAN}{formatted_time}{Colors.RESET}，{Colors.BLUE}{user_display}{Colors.RESET}对{Colors.BLUE}{item['title']}{Colors.RESET}执行了{Colors.MAGENTA}{logaction_display}{Colors.RESET}操作，摘要为{comment_display}。",end='\n\n')
            elif item['type'] == 'edit':
                print(f"{Colors.CYAN}{formatted_time}{Colors.RESET}，{Colors.BLUE}{user_display}{Colors.RESET}在{Colors.BLUE}{item['title']}{Colors.RESET}做出编辑，字节更改为{Colors.MAGENTA}{length_difference}{Colors.RESET}，摘要为{comment_display}。")
                print(f"（{Colors.YELLOW}https://zh.minecraft.wiki/?diff={item['revid']}{Colors.RESET}）", end='\n\n')
            elif item['type'] == 'new':
                print(f"{Colors.CYAN}{formatted_time}{Colors.RESET}，{Colors.BLUE}{user_display}{Colors.RESET}创建{Colors.BLUE}{item['title']}{Colors.RESET}，字节更改为{Colors.MAGENTA}{length_difference}{Colors.RESET}，摘要为{comment_display}。")
                print(f"（{Colors.YELLOW}https://zh.minecraft.wiki/?diff={item['revid']}{Colors.RESET}）", end='\n\n')
            elif item['type'] == 'external': # 未知类型，直接输出原文
                print(item, end='\n\n')

def get_data(api_url): # 从Mediawiki API获取数据
    try:
        response = requests.get(api_url,headers={"User-Agent": "AblazeVase69188's recent changes monitor (355846525@qq.com)"})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"（{current_time}）{Colors.RED}未获取到数据，请检查网络连接。{Colors.RESET}")
        input("按任意键退出")
        sys.exit(1)

# 登录
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    username = config["username"]
    password = config["password"]
site = wiki.Site("https://zh.minecraft.wiki/api.php", retry_after_conn=30)
site.login(username, password)

print("启动成功", end='\n\n')

try:
    with open('Autopatrolled_user.json', 'r', encoding='utf-8') as special_users_file:
        special_users = json.load(special_users_file)
except FileNotFoundError:
    print("巡查豁免权限用户列表获取失败", end='\n\n')
    special_users = []

# 最近更改：不要获取机器人编辑，每次获取25个编辑（SimpleBatchUpload大约每秒最多上传5个文件）
rc_url = "https://zh.minecraft.wiki/api.php?action=query&format=json&list=recentchanges&formatversion=2&rcprop=user%7Ctitle%7Ctimestamp%7Cids%7Cloginfo%7Csizes%7Ccomment&rcshow=!bot&rclimit=25&rctype=edit%7Cnew%7Clog%7Cexternal"

# 给第一次循环准备对比数据
previous_data = get_data(rc_url)

while 1: # 主循环，每5秒获取一次最近更改数据
    time.sleep(5)
    current_data = get_data(rc_url)

    # 根据时间戳差异确定新增数据
    timestamps1 = [item['timestamp'] for item in previous_data['query']['recentchanges']]
    timestamps2 = [item['timestamp'] for item in current_data['query']['recentchanges']]
    new_timestamps = [ts for ts in timestamps2 if ts not in timestamps1]
    new_data = [item for item in current_data['query']['recentchanges'] if item['timestamp'] in new_timestamps]
    print_rc(new_data)
    previous_data = current_data
