import os

# DB_ENGINE=sqlite3 时（本地自检）跳过 PyMySQL 挂载
if os.getenv('DB_ENGINE', 'mysql').lower() != 'sqlite3':
    import pymysql

    pymysql.install_as_MySQLdb()
