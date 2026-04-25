import getpass  # 安全获取密码输入
import select  # I/O多路复用，同时监视多个socket
import socket  # 网络通信核心库
import sys  # 系统功能，如退出程序
import threading  # 多线程支持
import argparse  # 命令行参数解析
import paramiko  # SSH协议库，实现SSH客户端/服务器功能

# 外部客户端 -> SSH服务器（监听端口）-> SSH隧道（chan）-> 内网主机（运行脚本）-> 目标服务（remote_host:remote_port）


def verbose(message):
    """打印详细日志信息"""
    if options.verbose:  # 根据命令行选项决定是否打印
        print(message)


def parse_options():
    """解析命令行参数"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='SSH Reverse Tunnel')

    # 添加命令行选项：
    parser.add_argument('-u', '--user', default=getpass.getuser(),
                        help='SSH用户名(默认为当前用户)')
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help='要转发的本地端口(默认8080)')
    parser.add_argument('-k', '--keyfile',
                        help='用于认证的私钥文件')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='启用详细输出')
    parser.add_argument('--look-for-keys', action='store_true',
                        help='在~/.ssh/中查找密钥')
    parser.add_argument('--readpass', action='store_true',
                        help='提示输入密码')
    parser.add_argument('server', help='SSH服务器地址(格式:host:port)')
    parser.add_argument('remote', help='远程目标地址(格式:host:port)')

    # 解析参数
    args = parser.parse_args()

    # 解析服务器地址(格式: host:port)
    # 如果指定了端口，使用指定端口，否则默认22
    server_host, server_port = args.server.split(':')
    server_port = int(server_port) if ':' in args.server else 22

    # 解析远程目标地址(格式: host:port)
    # 如果指定了端口，使用指定端口，否则默认80
    remote_host, remote_port = args.remote.split(':')
    remote_port = int(remote_port) if ':' in args.remote else 80

    return args, (server_host, server_port), (remote_host, remote_port)


def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    """建立反向SSH隧道"""
    try:
        # 请求SSH服务器进行端口转发
        # 参数1: 绑定的本地地址(''表示所有接口)
        # 参数2: 要转发的本地端口
        transport.request_port_forward('', server_port)

        # 打印日志
        verbose(f"Forwarding remote port {server_port} to {remote_host}:{remote_port}")

        # 持续监听传入连接
        while True:
            # 等待传入连接(最多等待1000毫秒)
            chan = transport.accept(1000)

            # 如果超时没有连接，继续等待
            if chan is None:
                continue

            # 创建线程处理连接
            thr = threading.Thread(
                target=handler,  # 指定处理函数
                args=(chan, remote_host, remote_port)  # 传递给处理函数的参数
            )
            thr.daemon = True  # 设置为守护线程(主线程退出时会自动终止)
            thr.start()  # 启动线程
    except Exception as e:
        print(f"Tunnel error: {e}")
        sys.exit(1)  # 出错时退出程序


def handler(chan, host, port):
    """处理隧道连接"""
    # 创建TCP套接字
    sock = socket.socket()  # 内网主机作为客户端主动连接到内网中的某一服务(remote:port)
    try:
        # 连接到目标服务
        sock.connect((host, port))

        # 打印隧道打开信息
        verbose(f"Tunnel open: {chan.origin_addr} -> {host}:{port}")
    except Exception as e:
        # 连接失败处理
        verbose(f"Connection to {host}:{port} failed: {e}")
        chan.close()  # 关闭通道
        return  # 结束处理

    # 双向数据转发
    try:
        while True:
            # 使用select同时监听套接字和通道
            # r - 可读的文件描述符列表
            # w - 可写的文件描述符列表(这里不需要)
            # x - 异常文件描述符列表(这里不需要)
            # 当sock或chan有数据可读时返回
            r, w, x = select.select([sock, chan], [], [])

            # 如果套接字有数据可读(目标服务有响应)
            if sock in r:    # 内网服务返回数据 → 转发给外部用户
                data = sock.recv(1024)
                if len(data) == 0:
                    break

                # 通过SSH通道发送数据
                chan.send(data)

            # 如果SSH通道有数据可读(客户端有请求)
            if chan in r:   # 外部用户发送请求 → 转发给内网服务
                data = chan.recv(1024)

                if len(data) == 0:
                    break

                # 发送数据到目标服务
                sock.send(data)
    except Exception as e:
        # 处理隧道错误
        verbose(f"Tunnel error: {e}")
    finally:
        # 无论是否出错，最终清理资源
        chan.close()  # 关闭SSH通道
        sock.close()  # 关闭套接字
        verbose(f"Tunnel closed from {chan.origin_addr}")


def main():
    global options  # 声明options为全局变量

    # 解析命令行参数
    options, server, remote = parse_options()
    password = None

    # 如果需要密码认证
    if options.readpass:
        # 安全获取密码(不会显示在终端)
        password = getpass.getpass('Enter SSH password: ')

    # 创建SSH客户端实例
    client = paramiko.SSHClient()

    # 加载系统保存的主机密钥
    client.load_system_host_keys()

    # 设置未知主机密钥策略(自动添加新主机到已知主机列表)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 打印连接信息
    verbose(f'Connecting to SSH host {server[0]}:{server[1]}...')

    try:
        # 连接到SSH服务器
        client.connect(
            server[0],  # 主机名
            server[1],  # 端口
            username=options.user,  # 用户名
            key_filename=options.keyfile,  # 密钥文件
            look_for_keys=options.look_for_keys,  # 是否查找密钥
            password=password  # 密码
        )
    except Exception as e:
        # 连接失败处理
        print(f'*** Failed to connect to {server[0]}:{server[1]}: {e}')
        sys.exit(1)  # 退出程序

    # 建立反向隧道
    try:
        reverse_forward_tunnel(
            options.port,  # 本地端口
            remote[0],  # 远程主机
            remote[1],  # 远程端口
            client.get_transport()  # 获取SSH传输对象
        )
    except KeyboardInterrupt:
        # 用户按下Ctrl+C中断程序
        print('\nC-c: Port forwarding stopped.')
        sys.exit(0)  # 正常退出


# 程序入口点
if __name__ == '__main__':
    main()