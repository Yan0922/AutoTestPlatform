"""算法测试平台 Django 项目包.

使用 PyMySQL 模拟 mysqlclient，免去 Windows 上 C 编译依赖。
对 PyMySQL 的版本号做一次"伪装"，让 Django 4.2 通过 mysqlclient>=1.4.3 的版本检查。
"""
try:
    import pymysql

    pymysql.version_info = (1, 4, 6, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
