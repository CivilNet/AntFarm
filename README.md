# AntFarm
这个程序用来在支付宝App里养鸡和种树。目前只支持Android手机。不支持iOS的原因在于AntFarm程序基于ADB。
关于该程序的更多背景，请访问：https://zhuanlan.zhihu.com/gemfield

# 功能
- 蚂蚁庄园中自动喂粮食；
- 蚂蚁庄园中自动驱赶偷吃的鸡；
- 蚂蚁森林中摘好友的能量；
- 蚂蚁森林中早上7点到7点半不断的摘取好友的能量。

# 如何使用
- AntFarm程序需要运行在个人电脑上，然后使用USB线缆将你的Android手机连接到个人电脑上，手机端调整usb连接方式为MTP，打开支付宝App并调整蚂蚁森林和蚂蚁庄园的图标在首页上展示；
- AntFarm程序使用Python构建，所以你的个人电脑可以是Linux、Windows、Mac操作系统。使用该命令克隆代码到个人电脑上：
`git clone https://github.com/CivilNet/AntFarm`
- 在个人电脑上配置ADB

# 如何在个人电脑上配置ADB
## Linux
- 安装adb：`sudo apt install adb`
- 安装OpenCV依赖：`pip install opencv_python`

## Windows
- 下载并安装Python、Pip，并设置好PATH环境变量；
- 安装OpenCV依赖：`pip install opencv_python`
- 下载最新ADB压缩包：https://dl.google.com/android/repository/platform-tools-latest-windows.zip
- 解压到自己指定的目录，并添加该目录到PATH环境变量中。

## macOS
没试过，原理应该类似。