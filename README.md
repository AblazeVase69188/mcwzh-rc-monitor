# mcwzh-rc-monitor
每5秒尝试获取一次中文Minecraft Wiki最近更改的变化情况，新更改内容在Windows终端输出，如果是无巡查豁免权限的用户执行的操作还会产生通知弹窗并播放音效。

部分功能仅持有巡查员权限的用户可正常使用（其实只有特殊巡查那个链接才是）。程序仅在Windows 11上可用（其实只是我没在Windows 10上面测试过而已）。

程序需要同目录存在`Autopatrolled_user.json`、`config.json`和`sound.mp3`才能正常运作。在这之前你应该需要先在[[Special:机器人密码]]创建一个机器人并获得密码，然后填入`config.json`。
