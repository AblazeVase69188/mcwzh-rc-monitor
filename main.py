import sys
import requests
import pywikiapi as wiki
import time
import json
from datetime import datetime, timedelta

def format_timestamp(timestamp_str): # 将UTC时间改为UTC+8
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
    timestamp += timedelta(hours=8)
    return timestamp.strftime('%H:%M:%S')

def format_comment(comment): # 摘要为空时输出（空）而不是【】
    return "（空）" if comment == "" else f"【{comment}】"

def print_rc(new_data): # 解析新更改数据并输出
    if new_data:
        for item in new_data:
            length_difference = item['newlen'] - item['oldlen']
            formatted_time = format_timestamp(item['timestamp'])
            comment_display = format_comment(item['comment'])
            if item['type'] == 'log': # pycharm自动缩进有点难绷
                logtype_display = "用户创建" if item['logtype'] == "newusers" else \
                    "删除" if item['logtype'] == "delete" else \
                        "封禁" if item['logtype'] == "block" else \
                            "保护" if item['logtype'] == "protect" else \
                                "滥用过滤器" if item['logtype'] == "abusefilter" else \
                                    "用户权限" if item['logtype'] == "rights" else \
                                        "移动" if item['logtype'] == "move" else \
                                            item['logtype']
                logaction_display = "创建" if item['logaction'] == "create" else \
                    "上传" if item['logaction'] == "upload" else \
                        "删除" if item['logaction'] == "delete" else \
                            "移动" if item['logaction'] == "move" else \
                                "覆盖上传" if item['logaction'] == "overwrite" else \
                                    "封禁" if item['logaction'] == "block" else \
                                        "更改封禁" if item['logaction'] == "reblock" else \
                                            "解除封禁" if item['logaction'] == "unblock" else \
                                                "移动保护设置" if item['logaction'] == "move_prot" else \
                                                    "保护" if item['logaction'] == "protect" else \
                                                        "移除保护" if item['logaction'] == "unprotect" else \
                                                            "修改" if item['logaction'] == "modify" else \
                                                                "登录状态创建账号" if item['logaction'] == "create2" else \
                                                                    "登录状态创建账号2" if item['logaction'] == "byemail" else \
                                                                        "迁移" if item['logaction'] == "migrated" else \
                                                                            "权限更改" if item['logaction'] == "rights" else \
                                                                                "移动" if item['logaction'] == "move" else \
                                                                                    item['logaction']
                if item['logtype'] == "upload":
                    print(f"（上传日志）{formatted_time}，{item['user']}对{item['title']}执行了{logaction_display}操作，摘要为{comment_display}。（https://zh.minecraft.wiki/?diff={item['revid']}）（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
                elif item['logtype'] == "move":
                    print(f"（移动日志）{formatted_time}，{item['user']}对{item['title']}执行了{logaction_display}操作，摘要为{comment_display}。（https://zh.minecraft.wiki/?diff={item['revid']}）")
                else:
                    print(f"（{logtype_display}日志）{formatted_time}，{item['user']}对{item['title']}执行了{logaction_display}操作，摘要为{comment_display}。")
            elif item['type'] == 'edit':
                print(f"{formatted_time}，{item['user']}在{item['title']}做出编辑，字节更改为{length_difference}，摘要为{comment_display}。（https://zh.minecraft.wiki/?diff={item['revid']}）（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
            elif item['type'] == 'new':
                print(f"{formatted_time}，{item['user']}创建{item['title']}，字节更改为{length_difference}，摘要为{comment_display}。（https://zh.minecraft.wiki/?diff={item['revid']}）（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
            elif item['type'] == 'external': # 未知类型，直接输出原文
                print(item)

def get_data(): # 从Mediawiki API获取数据
    api_url = "https://zh.minecraft.wiki/api.php?action=query&format=json&list=recentchanges&formatversion=2&rcprop=user%7Ctitle%7Ctimestamp%7Cids%7Cloginfo%7Csizes%7Ccomment&rcshow=!bot&rclimit=25&rctype=edit%7Cnew%7Clog%7Cexternal"
    # 设置：不要获取机器人编辑，每次获取25个编辑（SimpleBatchUpload大约每秒最多上传5个文件）
    try:
        response = requests.get(api_url,headers={"User-Agent": "AblazeVase69188's recent changes monitor (355846525@qq.com)"})
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException:
        print("未获取到数据，请检查API URL或网络连接。")
        sys.exit(1)

# 登录
with open("config.json", "r") as config_file:
    config = json.load(config_file)
    username = config["username"]
    password = config["password"]
site = wiki.Site("https://zh.minecraft.wiki/api.php", retry_after_conn=30)
site.login(username, password)

# 给第一次循环准备对比数据
data2 = get_data()

while 1: # 主循环，每5秒获取一次数据
    time.sleep(5)
    data1 = get_data()

    # 根据时间戳差异确定新增数据
    timestamps1 = [item['timestamp'] for item in data2['query']['recentchanges']]
    timestamps2 = [item['timestamp'] for item in data1['query']['recentchanges']]
    new_timestamps = [ts for ts in timestamps2 if ts not in timestamps1]
    new_data = [item for item in data1['query']['recentchanges'] if item['timestamp'] in new_timestamps]
    print_rc(new_data)

    time.sleep(5)
    data2 = get_data()

    # 根据时间戳确定新增数据
    timestamps1 = [item['timestamp'] for item in data1['query']['recentchanges']]
    timestamps2 = [item['timestamp'] for item in data2['query']['recentchanges']]
    new_timestamps = [ts for ts in timestamps2 if ts not in timestamps1]
    new_data = [item for item in data2['query']['recentchanges'] if item['timestamp'] in new_timestamps]
    print_rc(new_data)
