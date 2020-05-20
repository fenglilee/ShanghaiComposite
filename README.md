### 项目中用到的依赖项目

- flask: http://flask.pocoo.org/
- flask-restful: http://flask-restful.readthedocs.io/en/latest/
- flask-restplus: http://flask-restplus.readthedocs.io/en/latest/
- flask-sqlalchemy: http://flask-sqlalchemy.pocoo.org/2.3/
- flask-migrate: https://flask-migrate.readthedocs.io/en/latest/
    - alembic: http://alembic.zzzcomputing.com/en/latest/
- celery: http://docs.celeryproject.org/en/3.1/index.html
- ansible相关：
    - ansible: https://docs.ansible.com/ansible/latest/index.html
    - ansible-runner: https://github.com/ansible/ansible-runner
- pytest: https://docs.pytest.org/en/latest/contents.html

另外，一些相关链接：
- DocString采用google规范：https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- wsgi容器使用Gunicorn: http://docs.gunicorn.org/en/latest/install.html


---
---

### 如何启动该后端Server程序

### 数据库准备
- 创建aops数据库

```sql
CREATE DATABASE `aops` /*!40100 COLLATE 'utf8_unicode_ci' */;
```

- 创建用户普通用户mds，并赋权mds对aops库的操作权限

```sql
CREATE USER 'mds'@'%' IDENTIFIED BY 'Pwd@123';
GRANT ALL PRIVILEGES ON aops.* to mds@"%" IDENTIFIED by "Pwd@123";
FLUSH PRIVILEGES;
```

#### 前置条件
- 本地安装python2.7版本
- git clone代码到本地，进入到项目根目录
- 通过pip安装依赖的python package,执行：

    ```bash
    pip install -r requirements.txt
    ```

#### 启动程序
方式一：通过pycharm启动，进入项目根目录，右击aops/app.py文件：
1. 启动程序
    - 开发时，点击Debug app，报错，但生成配置文件
2. 点击当前调试的配置，设置：

    ```plain
    Scripts Path: <project_root_path>\aops\app.py
    Working Directory: <project_root_path>
    ```
3. 设置环境变量APP_MODE=development，进入开发模式；
4. 重新点击DEBUG即可。

方式二：通过flask启动，进入项目跟目录，执行：
- windows执行：

```bash
set FLASK_APP=aops
set FLASK_ENV=development # 进入开发模式
flask run
```
- Linux执行：

```bash
export FLASK_APP=aops
export FLASK_ENV=development # 进入开发模式
flask run
```

其他详细参数，通过`flaks run --help`查阅

---
---

### 数据库迁移
使用flask-migrate扩展实现，底层使用alembic。以下所有flask相关命令，均在
项目的根目录下执行。

1. 设置需要操作数据库的环境
- 测试环境

    ```bash
    set APP_MODE=development # windows
    export APP_MODE=development # Linux
    ```
- 生产环境

    ```bash
    set APP_MODE=production # windows
    export APP_MODE=production # Linux
    ```

2. 数据库初始化，根目录下生成名为migrations的文件
夹，里面包含了数据库迁移底层库alembic的相关实现。

    ```bash
    flask db init
    ```

3. 数据库迁移。数据库迁移底层的alembic并不能有效的探测到所有变更，
例如无法探测数据库名称、字段名称等一系列变更，具体点[这里](http://alembic.zzzcomputing.com/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)
进行查看，在进行明确的版本迭代前，该用法用不到。

    ```bash
    flask db migrate
    ```

---
---

### gunicorn的使用方式
说明：目前官方gunicorn只能在 `*nux` 平台上运行，不支持windows平台。

1. 没有通过包安装的环境，在根目录下执行：

```bash
gunicorn --workers 4 -k gevent -n aops_server aops
```