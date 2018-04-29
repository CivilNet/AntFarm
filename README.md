# AntFarm
这个程序用来在支付宝App里养鸡和种树。目前只支持Android手机。不支持iOS的原因在于AntFarm程序基于ADB。
关于该程序的更多背景，请访问：https://zhuanlan.zhihu.com/p/35940345

# 功能
- 蚂蚁庄园中自动喂粮食；
- 蚂蚁庄园中自动驱赶偷吃的鸡；
- 蚂蚁森林中摘好友的能量；
- 蚂蚁森林中早上7点到7点半不断的摘取好友的能量。

# 如何使用
- AntFarm程序需要运行在个人电脑上，然后使用USB线缆将你的Android手机连接到个人电脑上，手机端调整usb连接方式为MTP，打开支付宝App并调整蚂蚁森林和蚂蚁庄园的图标在首页上展示；
- AntFarm程序使用Python构建，所以你的个人电脑可以是Linux、Windows、Mac操作系统。使用该命令克隆代码到个人电脑上：
`git clone https://github.com/CivilNet/AntFarm`
- 在个人电脑上配置ADB和OpenCV依赖（参考下节）；
- 使用下面的命令开始养鸡种树：`python ant.py` 。这将会使用default模式来开始养鸡种树；
- AntFarm支持4种模式(使用--mode指定)：farm,forest,default,all

#### default模式
这种模式下，AntFarm在启动的时候会去检查蚂蚁庄园和蚂蚁森林，然后在7:00AM ~ 7:35AM之间会不断检查蚂蚁森林，其它时间都在蚂蚁庄园：`python ant.py` 或者 `python ant.py --mode default`。这种模式也是Gemfield最常用的模式。
#### farm模式
这种模式下，AntFarm只负责养鸡：`python ant.py --mode farm`
#### forest模式
这种模式下，AntFarm只负责种树：`python ant.py --mode forest`
#### all模式
这种模式下，AntFarm在启动的时候会去检查蚂蚁庄园和蚂蚁森林，然后在整点的时候会检查蚂蚁森林，其它时间都在检查蚂蚁庄园：`python ant.py --mode all`

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

# 已知问题
- 识别蚂蚁森林可收取能量球的正确率大约为97%，离100%当然还有提升空间。不过Gemfield没有过多的时间来研究和试验，目前为止还没有找到优雅的轻量级（不使用深度学习框架）算法，谁能找到轻量级的优雅的100%正确率算法，发100块钱红包；
- 支付宝的蚂蚁森林或者蚂蚁庄园的界面在载入时，有时会出现预期之外的弹窗（如节日广告推送），可能会导致程序逻辑线混乱（说'可能'是因为AntFarm本身还是健壮的，能应付一些错误）；
- 基于adb的原理使得程序运行依赖个人电脑，不够灵活，谁能改变这个现状，发100块钱红包；
- 手机不能息屏，程序运行费电，不够环保，深感内疚，谁最先能解决这个问题，发100块钱红包；
- 目前没有在Linux或Windows PC上支持iPhone的轻量级（至少达到adb水平）的优雅的解决方案，谁能解决这个问题，发100块钱红包。