import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor
import threading


UA_pool = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

class Dirsearch:
    def __init__(self,url,path,max_workers=10):

        self.url = url
        self.file_path = path
        self.path_list = []
        self.max_workers = max_workers
        self.found_urls = set()

        self.lock = threading.Lock()


    def load_dict(self):
        """处理fuzz的字典文件的加载"""
        try:
            with open(self.file_path,'r',encoding='utf-8') as f:
                self.path_list = [line.strip() for line in f if line.strip()]
            print(f'[***]字典文件加载成功,共: {len(self.path_list)}个路径')
        except FileNotFoundError:
            print(f'[!!!]请检查文件是否存在')
        finally:
            if not self.path_list:
                print(f'[!!!]字典文件加载失败,请检查文件是否存在: {self.file_path}')
            else:
                print(f'[***]字典文件加载成功')

    def send_requests(self,url,timeout=5):
        """处理发送请求并返回状态码"""
        try:
            ua = {'User-Agent': random.choice(UA_pool)}
            response = requests.get(url=url,headers=ua,timeout=timeout)
            return len(response.text), response.status_code, response.url
        except requests.exceptions.Timeout:
            print(f'[!!!]请求超时,请重试')
            return 0, 404, None
        except Exception as e:
            print(f'[!!!]错误: {str(e)}')
            return 0, 404, None

    def multi_thread_scan(self, url_list):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self.send_requests,url_list))
        return results

    def dir_fuzz(self,init_url=None,current_depth=0,max_depth=3):
        """处理目录扫描"""
        if current_depth >= max_depth:
            return

        base_url = init_url if init_url else self.url
        print(f'[+]扫描深度 {current_depth}: {base_url}')
        url_list = []
        for path in self.path_list:
            url = base_url.rstrip('/') + '/' + path.strip().lstrip('/')
            url_list.append(url)

        resp_list = self.multi_thread_scan(url_list)

        next_list = []
        for result in resp_list:
            if None in result:
                continue
            length, code, url = result
            with self.lock:
                if self.handle_state(url,length,code) and url not in self.found_urls:
                    next_list.append(url)
                    self.found_urls.add(url)
        for next_url in next_list:
            self.dir_fuzz(next_url,current_depth+1)

    def handle_state(self, url, length, code=404):
        """处理返回的状态码"""
        formal_state = [
            200, 403, 301, 302
        ]
        if code in formal_state:
            print(f'{url}\t{code}\t{length}')
            return True
        return False

    def run_scan(self,max_depth=3):

        if not self.path_list:
            self.load_dict()
            if not self.path_list:
                return
        start_time = time.time()
        print(f'[***] 开始扫描，目标: {self.url}, 线程数: {self.max_workers}, 最大深度: {max_depth}')
        self.dir_fuzz(max_depth=max_depth)

        print(f'扫描完成,共耗时: {time.time() - start_time}')


if __name__ == '__main__':
    url = 'http://node4.anna.nssctf.cn:28176/'
    path = r'wordlist.txt'
    dirsearch = Dirsearch(url,path,25)
    dirsearch.run_scan()

