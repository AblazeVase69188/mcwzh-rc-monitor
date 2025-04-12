import sys
import requests
import pywikiapi as wiki
import time
import json
from datetime import datetime, timedelta

def format_timestamp(timestamp_str):
    # 解析时间戳并加8小时
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
    timestamp += timedelta(hours=8)
    return timestamp.strftime('%H:%M:%S')

def printrc(new_data):
    if new_data:
        """print("上次查询以来的新更改：")"""
        for item in new_data:
            length_difference = item['newlen'] - item['oldlen']
            formatted_time = format_timestamp(item['timestamp'])
            if item['type'] == 'log':
                logtype_display = "用户创建" if item['logtype'] == "newusers" else \
                    "上传" if item['logtype'] == "upload" else \
                        "删除" if item['logtype'] == "delete" else \
                            "移动" if item['logtype'] == "move" else \
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
                                                                "登录状态创建账号" if item[
                                                                                          'logaction'] == "create2" else \
                                                                    "登录状态创建账号2" if item[
                                                                                               'logaction'] == "byemail" else \
                                                                        "迁移" if item['logaction'] == "migrated" else \
                                                                            "权限更改" if item[
                                                                                              'logaction'] == "rights" else \
                                                                                "移动" if item[
                                                                                              'logaction'] == "move" else \
                                                                                    item['logaction']
                print(f"（{logtype_display}日志）{formatted_time}，{item['user']}对{item['title']}执行了{logaction_display}操作。")
            elif item['type'] == 'edit':
                print(f"{formatted_time}，{item['user']}在{item['title']}做出编辑，字节更改为{length_difference}。（https://zh.minecraft.wiki/?diff={item['revid']}）（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
            elif item['type'] == 'new':
                print(f"{formatted_time}，{item['user']}创建{item['title']}。（https://zh.minecraft.wiki/?diff={item['revid']}）（特殊巡查：https://zh.minecraft.wiki/index.php?curid={item['pageid']}&action=markpatrolled&rcid={item['rcid']}）")
            elif item['type'] == 'external':
                print(item)
    else:
        """print("上次查询以来没有新更改")"""

def get_data():
    """print("正在从Mediawiki API获取数据...")"""
    try:
        response = requests.get(api_url,headers={"User-Agent": "AblazeVase69188's recent changes monitor (355846525@qq.com)"})
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()  # 将响应内容解析为JSON
        return data
    except requests.exceptions.RequestException:
        print("未获取到数据，请检查API URL或网络连接。")
        sys.exit(1)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
    username = config["username"]
    password = config["password"]
site = wiki.Site("https://zh.minecraft.wiki/api.php", retry_after_conn=30)
site.login(username, password)
api_url = "https://zh.minecraft.wiki/api.php?action=query&format=json&list=recentchanges&formatversion=2&rcprop=user%7Ctitle%7Ctimestamp%7Cids%7Cloginfo%7Csizes&rcshow=!bot&rclimit=10&rctype=edit%7Cnew%7Clog%7Cexternal"

data2 = get_data()

while 1:
    time.sleep(5)
    data1 = get_data()

    # 提取两组数据中的时间戳
    timestamps1 = [item['timestamp'] for item in data2['query']['recentchanges']]
    timestamps2 = [item['timestamp'] for item in data1['query']['recentchanges']]
    # 找出新增的时间戳
    new_timestamps = [ts for ts in timestamps2 if ts not in timestamps1]
    # 根据新增的时间戳找到对应的新增数据
    new_data = [item for item in data1['query']['recentchanges'] if item['timestamp'] in new_timestamps]
    printrc(new_data)

    time.sleep(5)
    data2 = get_data()

    # 提取两组数据中的时间戳
    timestamps1 = [item['timestamp'] for item in data1['query']['recentchanges']]
    timestamps2 = [item['timestamp'] for item in data2['query']['recentchanges']]
    # 找出新增的时间戳
    new_timestamps = [ts for ts in timestamps2 if ts not in timestamps1]
    # 根据新增的时间戳找到对应的新增数据
    new_data = [item for item in data2['query']['recentchanges'] if item['timestamp'] in new_timestamps]
    printrc(new_data)
