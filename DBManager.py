import datetime
import json
import os
import sqlite3
from PathUtil import root_dir

# 组件二进制信息表
table_component_info = 'table_component_info'
# 失败记录表
table_error_info = 'table_error_info'

# 获取路径
def get_path() -> str:
    # return '/Users/xxx/Documents/二进制/BinaryComponent/binary_exception.db'
    return '%s/binary_exception.db' % root_dir()

def get_strftime() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 创建数据库表
def creat_tab(sql: str):
    path = get_path()
    con = sqlite3.connect(path)  # 不存在会自动创建
    cur = con.cursor()
    cur.execute(sql)
    con.commit()
    cur.close()
    con.close()

# 创建组件信息数据库表
def creat_table_component_info():
    sql = '''CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, name TEXT, 
                save_time timestamp not null default (datetime('now','localtime')))''' % (table_component_info)
    creat_tab(sql)

# 创建错误信息数据库表
def creat_table_error_info():
    sql = '''CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, reason TEXT, 
                save_time timestamp not null default (datetime('now','localtime')))''' % (table_error_info)
    creat_tab(sql)

# 废弃
#  组件信息数据库表插入数据
def insert_component_info_data(nameTag: str):
    creat_table_component_info()
    path = get_path()
    con = sqlite3.connect(path)  # 不存在会自动创建
    cur = con.cursor()
    cur.execute('''INSERT INTO table_component_info VALUES (?,?,?);''', (None, nameTag, get_strftime()))
    con.commit()
    cur.close()
    con.close()

# 保存静态化失败的记录 线上已使用
def insert_error_info_data(reason: str):
    creat_table_error_info()
    path = get_path()
    con = sqlite3.connect(path)  # 不存在会自动创建
    cur = con.cursor()
    cur.execute('''INSERT INTO table_error_info VALUES (?,?,?);''', (None, reason, get_strftime()))
    con.commit()
    cur.close()
    con.close()

# 根据名称筛选数据库表信息
def select_component_info_data(nameTag: str) -> list:
    path = get_path()
    con = sqlite3.connect(path)  # 不存在会自动创建
    cur = con.cursor()
    sql = "SELECT id, name, save_time from {table_info} where name = ?".format(table_info=table_component_info)
    arg = (nameTag,)
    result = cur.execute(sql, arg).fetchall()
    for item in result:
        print("item:", item)
    cur.close()
    con.close()
    return result

# 保存静态化失败的记录 线上已使用
# def saveErrorToSqlite(msg):
#     sqlite_path = '%s/binary_exception.db' % root_dir()
#     con = sqlite3.connect(sqlite_path)  # 不存在会自动创建
#     cur = con.cursor()
#     sql = "CREATE TABLE IF NOT EXISTS binary_static(id INTEGER PRIMARY KEY,reason TEXT,save_time timestamp not null default (datetime('now','localtime')))"
#     cur.execute(sql)
#     # 插入数据
#     cur.execute("INSERT INTO binary_static VALUES (?,?,?);",
#                 (None, msg, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
#     con.commit()
#     # 关闭游标
#     cur.close()
#     # 断开数据库连接
#     con.close()

# 保存已经静态化的组件，component = 组件+版本号，作为一个字段
def saveBinaryComponent(component):
    insert_component_info_data(component)

# component = 组件+版本号,根据component搜索是否存在
def check_podspec_if_static(static_component_dir, name_versions):
    podspec_path = os.path.join(static_component_dir, '%s.podspec.json' % name_versions[0])
    print(podspec_path)
    with open(podspec_path) as f:
        podspec_json = json.load(f)
        source = podspec_json.get('source')
        if source and source.get("http"):
            return True
        else:
            return False


# return (podspec_exists, haveStaticed)
def componentExists(component):
    home = os.environ['HOME']
    static_dir = os.path.join(home, '.cocoapods/repos/zr_static_module_spec')
    print(static_dir)
    name_versions = component.split('+')
    print(name_versions)
    if len(name_versions) != 2:
        raise Exception("通过组件路径没有获取到组件名称和版本号信息，判断组件是否已经存在，失败")
    static_component_dir = os.path.join(static_dir, '%s/%s' % (name_versions[0],name_versions[1]))
    if os.path.exists(static_component_dir):
        return (True, check_podspec_if_static(static_component_dir, name_versions))
    else:
        return (False, False)


if __name__ == '__main__':
    # creat_table_component_info()
    # insert_component_info_data('IM-1.0.2')
    #
    # creat_table_error_info()
    # insert_error_info_data('版本号错误')

    componentExists('Mantle+2.1.6')