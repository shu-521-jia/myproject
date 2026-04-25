import sys
import socket
import threading

'''
这段代码创建了一个256字符的映射表，作用是将不可打印字符替换为点号.：
生成逻辑分析：
chr(i) 生成0-255对应的ASCII字符
repr(chr(i)) 获取字符的Python表示形式
当字符为可打印ASCII字符时，repr形式长度为3（例如：'A'）
不可打印字符的repr长度会大于3（例如：'\n'的repr是'\x0a'，长度5）
效果示例：
可打印字符 A → 保留
控制字符 \x00 → 替换为 .
换行符 \n → 替换为 .
'''

HEX_FILTER=''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.'for i in range(256)]
)

def hexdump(src,length=16,show=True):
    # 如果是字节数据 转换为字符串
    if isinstance(src,bytes):
        src = src.decode()
    results = list()

    # 分块处理数据
    for i in range(0,len(src),length):
        word = src[i:i+length]
        printable = word.translate(HEX_FILTER)

        # 把数据转换为十六进制格式(ord()获取ASCII值)
        # 02表示总长度为2 不足前面补0
        # x表示使用小写形式
        # 添加空格分隔符的版本
        hex_chars = [f'{ord(c):02x}' for c in word]

        # 添加空格分隔
        hexa = ' '.join(hex_chars)

        # 起始点的偏移
        hexwidth = length*3

        # 格式化输出
        # i:    当前块的起始索引
        # 04:   总宽度4位，不足前面补0
        # x:    十六进制格式
        # <:    左对齐
        results.append(f"{i:04x}  {hexa:<{hexwidth}}  {printable}")
    if show:
        for line in results:
            print(line)
    else:
        return results

def receive_from(connection):
    buffer = b"" # 初始化空字节缓冲区
    connection.settimeout(5) # 设置超时时间(秒)
    try:
        while 1:
            data = connection.recv(1024) # 单次最多读取1024字节
            if not data: # 接收到空数据说明连接关闭
                break
            buffer+=data
    except Exception as e:
        print(f'Error: str{e}')
    return buffer # 返回所有读取到的数据
def request_handler(buffer):
    '''
    修改请求
    :param buffer:
    :return:
    '''
    return buffer
def response_handler(buffer):
    '''
    修改响应
    :param buffer:
    :return:
    '''
    return buffer

def proxy_handler(client_socket,remote_host,remote_port,receive_first):
    # 连接远程主机
    remote_socket = socket.socket()
    remote_socket.connect((remote_host,remote_port))

    # 确认是否先从服务器获取数据(有的服务器会要求你做这样的操作(比如FTP服务器，会先发给你一条欢迎消息，你收到后才能发送数据给它))
    if receive_first:
        # 获得处理后的数据
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer) # 十六进制展示

        remote_buffer = response_handler(remote_buffer) # 数据处理
        # 转发给客户端
        if len(remote_buffer):
            print("[<==] Sending %d bytes to localhost."%len(remote_buffer))
            client_socket.send(remote_buffer)
    # 主代理循环
    while 1:
        # 处理客户端->服务器的数据
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            line = "[==>]Received %d bytes from localhost."%len(local_buffer)
            print(line)
            hexdump(local_buffer) # 十六进制展示

            local_buffer = request_handler(local_buffer) # 数据处理
            remote_socket.send(local_buffer)
            print("[==>]Send to remote")

        # 处理服务器->客户端数据
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote."%len(remote_buffer))
            hexdump(remote_buffer) # 十六进制展示

            remote_buffer=response_handler(remote_buffer) # 数据处理
            client_socket.send(remote_buffer)
            print("[<==]Send to localhost")

        # 终止条件
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*]No more data.Closing connections")
            break

def server_loop(local_host,local_port,remote_host,remote_port,receive_first):
    server = socket.socket()
    try:
        server.bind((local_host,local_port))
    except Exception as e:
        print('problem on bind: %r'%e)
        print("[!!]Failed to listen on %s:%d"%(local_host,local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print("[*]Listening on %s:%d"%(local_host,local_port))
    server.listen(5)
    while 1:
        client_socket,addr = server.accept()
        line = "> Received incoming connection from %s:%d"%(addr[0],addr[1])
        print(line)

        proxy_thread = threading.Thread(target=proxy_handler,
                    args=(client_socket,
                          remote_host,
                          remote_port,
                          receive_first
        ))
        proxy_thread.start()
def main():
    if len(sys.argv[1:]) != 5:
        print('Usage: ./TCP-proxy.py [localhost] [localport]',end='')

        print("[remotehost] [remoteport] [receivefirst]")
        print('Example: ./TCP-proxy.py 127.0.0.1 9000 192.168.209.128 9000 True')
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    receive_first = sys.argv[5]

    if 'True' in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host,local_port,remote_host,remote_port,receive_first)
if __name__ == '__main__':
    main()