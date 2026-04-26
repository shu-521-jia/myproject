# myproject
一些项目的集合    后续可能会改进
网络安全与渗透测试工具集合（自用开发）

# 简介

本仓库收录了我在学习与实战中独立开发的各类网络安全工具，涵盖 Web 漏洞利用、内网渗透、流量分析、自动化扫描​ 等方向。

工具均使用 Python​ 开发，部分基于 requests、scapy、pynput、paramiko等库实现，已在 DVWA、Vulhub、红日安全靶场​ 等环境中验证可用性。

# 项目列表
## 一、Web 漏洞利用工具


### SQL 盲注自动化工具​
	


支持布尔盲注与时间盲注，自动获取数据库名、表名、列名与数据
	



二分查找算法、位多线程并发、请求量优化




对应文件：test_bak3.py time_blind_injection.py


### 登录爆破工具​

	

多线程 Web 表单爆破，支持字典加载、进度显示、成功特征匹配

	

ThreadPoolExecutor、随机 UA、失败/成功逻辑判断

对应文件：Brute_force2.py


### 目录扫描工具​

	

递归目录 Fuzz，支持深度控制、状态码过滤

	

多线程扫描、剪枝优化、自动去重

 对应文件：MuitiThread_Dirsearch.py

## 二、网络与内网渗透工具



### TCP 代理（类 Burp Upstream Proxy）​

	

支持流量中转、十六进制打印、请求/响应修改

	

Socket 编程、多线程、流量分析与篡改

对应文件：TCP-proxy.py


### ARP 欺骗与流量嗅探​

	

双向 ARP 投毒、流量捕获与 PCAP 保存

	

Scapy、多进程、ARP 表自动恢复

对应文件：arper.py


### 反向 SSH 隧道​

	

内网穿透与端口转发

	

Paramiko、I/O 多路复用、双向数据转发

对应文件：reverse-tunnel.py

## 三、红蓝对抗辅助工具


### 键盘记录器​

	

记录键盘输入、窗口信息、剪贴板内容

	

pynput、Windows API、实时行为监控

对应文件：keylogger.py


# 使用说明

本仓库仅用于 学习、研究与合法授权测试

禁止用于非法渗透、未授权攻击

部分工具依赖 Windows API / Linux 网络权限，请按需运行
