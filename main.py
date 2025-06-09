import requests
import pywikiapi as wiki
import json
import time
import sys
from datetime import datetime
from playsound3 import playsound
from playsound3.playsound3 import PlaysoundException
from winotify import Notification

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
    "upload": "上传",
    "move": "移动",
    "renameuser": "用户更名"
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
    "rights": "权限更改",
    "revert": "恢复至旧版本",
    "restore": "还原修订版本",
    "event": "更改日志可见性",
    "renameuser": "重命名用户"
}

MESSAGE_TEMPLATES = {
    "log": {
        "upload": "（{magenta}上传日志{reset}）{time}，{user}对{title}执行了{action}操作，摘要为{comment}。",
        "move": "（{magenta}移动日志{reset}）{time}，{user}移动页面{title}至{target_title}，摘要为{comment}。",
        "renameuser": "（{magenta}用户更名日志{reset}）{time}，{user}重命名用户{olduser}为{newuser}，摘要为{comment}。",
        "default": "（{magenta}{log_type}日志{reset}）{time}，{user}对{title}执行了{action}操作，摘要为{comment}。"
    },
    "edit": "{time}，{user}在{title}做出编辑，字节更改为{length_diff}，摘要为{comment}。",
    "new": "{time}，{user}创建{title}，字节更改为{length_diff}，摘要为{comment}。"
}

TOAST_TEMPLATES = {
    "log": {
        "upload": "（上传日志）{user}对{title}执行了{action}操作，摘要为{comment}。",
        "move": "（移动日志）{user}移动页面{title}至{target_title}，摘要为{comment}。",
        "renameuser": "（用户更名日志）{user}重命名用户{olduser}为{newuser}，摘要为{comment}。",
        "default": "（{log_type}日志）{user}对{title}执行了{action}操作，摘要为{comment}。"
    },
    "edit": "{user}在{title}做出编辑，字节更改为{length_diff}，摘要为{comment}。",
    "new": "{user}创建{title}，字节更改为{length_diff}，摘要为{comment}。"
}

def generate_messages(item, special_users): # 生成控制台消息和弹窗消息文本
    base_params = {
        "time": format_timestamp(item['timestamp']),
        "user": item['user'],
        "title": item['title'],
        "comment": item['comment'],
    }
    if item['type'] == 'log' and item['logtype'] == 'move':
        base_params["target_title"] = item['logparams']['target_title']
    elif item['type'] == 'log' and item['logtype'] == 'renameuser':
        base_params["olduser"] = item['logparams']['olduser']
        base_params["newuser"] = item['logparams']['newuser']

    console_params = base_params.copy()
    console_params.update({
        "user": format_user(base_params["user"], special_users),
        "title": f"{Colors.BLUE}{base_params['title']}{Colors.RESET}",
        "comment": format_comment(base_params['comment']),
        "magenta": Colors.MAGENTA,
        "reset": Colors.RESET
    })

    toast_params = base_params.copy()
    toast_params.update({
        "comment": "（空）" if base_params['comment'] == "" else base_params['comment']
    })

    if item['type'] == 'log':
        log_type = LOG_TYPE_MAP.get(item['logtype'], item['logtype'])
        action = LOG_ACTION_MAP.get(item['logaction'], item['logaction'])

        console_params.update({
            "log_type": log_type,
            "action": f"{Colors.MAGENTA}{action}{Colors.RESET}"
        })
        if item['logaction'] == 'move':
            console_params.update({
                "target_title": f"{Colors.BLUE}{console_params["target_title"]}{Colors.RESET}"
            })
        elif item['logaction'] == 'renameuser':
            console_params.update({
                "olduser": f"{Colors.BLUE}{console_params["olduser"]}{Colors.RESET}",
                "newuser": f"{Colors.BLUE}{console_params["newuser"]}{Colors.RESET}"
            })

        template_key = item['logtype'] if item['logtype'] in MESSAGE_TEMPLATES["log"] else "default"
        console_msg = MESSAGE_TEMPLATES["log"][template_key].format(**console_params)

        toast_params.update({
            "log_type": log_type,
            "action": action
        })
        toast_msg = TOAST_TEMPLATES["log"][template_key].format(**toast_params)
    else:
        console_params["length_diff"] = f"{Colors.MAGENTA}{format_length_diff(item['newlen'], item['oldlen'])}{Colors.RESET}"
        console_msg = MESSAGE_TEMPLATES[item['type']].format(**console_params)

        toast_params["length_diff"] = format_length_diff(item['newlen'], item['oldlen'])
        toast_msg = TOAST_TEMPLATES[item['type']].format(**toast_params)

    return console_msg, toast_msg

def generate_url(item): # 生成url
    if item['type'] == 'log':
        if item['logtype'] in ["upload", "move"]:  # 只有上传日志和移动日志具备有效revid值
            return f"https://zh.minecraft.wiki/?diff={item['revid']}"
        else:
            return f"https://zh.minecraft.wiki/Special:%E6%97%A5%E5%BF%97/{item['logtype']}"
    else:
        return f"https://zh.minecraft.wiki/?diff={item['revid']}"

def notification(msg_body,url): # 产生弹窗通知
    toast = Notification(
        app_id="Minecraft Wiki RecentChanges Monitor",
        title="",
        msg=msg_body
    )
    toast.add_actions(label="打开网页", launch=url)
    toast.show()
    sound_play()

def sound_play(): # 播放音效
    try:
        playsound("sound.mp3", block=False)
    except PlaysoundException:
        pass

def format_timestamp(timestamp_str): # 将UTC时间改为UTC+8
    time_part = timestamp_str[11:19]
    hour = int(time_part[0:2])
    hour = (hour + 8) % 24
    return f"{Colors.CYAN}{hour:02d}{time_part[2:]}{Colors.RESET}"

def format_comment(comment): # 摘要为空时输出（空）
    return f"（空）" if comment == "" else f"{Colors.CYAN}{comment}{Colors.RESET}"

def format_user(user, special_users): # 有巡查豁免权限的用户标记为绿色
    return f"{Colors.GREEN}{user}{Colors.RESET}" if user in special_users else f"{Colors.BLUE}{user}{Colors.RESET}"

def format_length_diff(newlen, oldlen): # 字节数变化输出和mw一致
    diff = newlen - oldlen
    return f"+{diff}" if diff > 0 else f"{diff}"

def print_rc(new_data): # 处理数据
    for item in new_data:
        console_msg, toast_msg = generate_messages(item, special_users)
        url = generate_url(item)

        print(console_msg)
        print(f"（{Colors.YELLOW}{url}{Colors.RESET}）")
        if item['type'] == "log" and item['logtype'] == "upload" and item['user'] not in special_users:
            print(f"（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
        print("")

        if item['user'] not in special_users: # 无巡查豁免权限用户执行操作才出现弹窗
            notification(toast_msg, url)

def get_data(api_url): # 从Mediawiki API获取数据
    tries = 0
    while 1:
        try:
            response = requests.get(api_url, headers={"User-Agent": ua})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            tries += 1
            if tries > 1:
                break

            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"（{current_time}）{Colors.RED}未获取到数据，20秒后重试。{Colors.RESET}", end='\n\n')
            toast = Notification(
                app_id="Minecraft Wiki RecentChanges Monitor",
                title="",
                msg="未获取到数据，20秒后重试。"
            )
            toast.show()
            sound_play()
            time.sleep(20)

    print(f"{Colors.RED}重试失败，请检查网络连接。{Colors.RESET}")
    toast = Notification(
        app_id="Minecraft Wiki RecentChanges Monitor",
        title="",
        msg="重试失败，请检查网络连接。"
    )
    toast.show()
    sound_play()
    input("按任意键退出")
    sys.exit(1)

# 登录
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    username = config["username"]
    password = config["password"]
    ua = config["ua"]
site = wiki.Site("https://zh.minecraft.wiki/api.php", retry_after_conn=30)
site.login(username, password)

print("启动成功", end='\n\n')

# 获取巡查豁免权限用户列表
try:
    with open('Autopatrolled_user.json', 'r', encoding='utf-8') as special_users_file:
        special_users = set(json.load(special_users_file))
except FileNotFoundError:
    print("巡查豁免权限用户列表获取失败", end='\n\n')
    special_users = set()

# 最近更改：不要获取机器人编辑，每次最多获取100个编辑
rc_url = "https://zh.minecraft.wiki/api.php?action=query&format=json&list=recentchanges&formatversion=2&rcprop=user%7Ctitle%7Ctimestamp%7Cids%7Cloginfo%7Csizes%7Ccomment&rcshow=!bot&rclimit=100&rctype=edit%7Cnew%7Clog%7Cexternal"

# 给第一次循环准备对比数据
initial_rc_url = "https://zh.minecraft.wiki/api.php?action=query&format=json&list=recentchanges&formatversion=2&rcprop=user%7Ctitle%7Ctimestamp%7Cids%7Cloginfo%7Csizes%7Ccomment&rcshow=!bot&rclimit=1&rctype=edit%7Cnew%7Clog%7Cexternal"
initial_data = get_data(initial_rc_url)
last_timestamp = initial_data['query']['recentchanges'][0]['timestamp']

while 1: # 主循环，每5秒获取一次数据
    time.sleep(5)
    current_url = f"{rc_url}&rcend={last_timestamp}" if last_timestamp else rc_url
    current_data = get_data(current_url)

    new_items = current_data['query']['recentchanges'][-2::-1]

    if not new_items:
        continue

    last_timestamp = new_items[0]['timestamp']

    print_rc(new_items)
