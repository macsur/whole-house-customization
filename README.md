# 木序定制 · 全屋定制平台

基于 Vue 3、Element Plus 与 Django (DRF + MySQL) 的全屋定制橱柜业务系统测试环境：客户端（产品/案例展示、在线定制提交）、管理端（产品/案例/客户/订单管理）、Django 后端 API 与 MySQL 存储，通过 Docker Compose 一键拉起。

## 目录结构

- `client/@latest`：客户前端（Vue3，演示数据静态展示）
- `admin/@latest`：管理端（Vue3，演示数据静态展示）
- `service/WholeHouse`：Django REST Framework 后端（MySQL + PyMySQL）
- `docker-compose.yml` / `Dockerfile.{backend,client,admin}` / `nginx.spa.conf` / `.env.example`：本仓库自带的 Docker 部署资产

## Docker Hub 官方镜像

本仓库配套的我方 Docker Hub 镜像（优先拉取，缺失时自动本地构建兜底）：

- `macttnk/whole-house-backend:<tag>`（Django 后端）
- `macttnk/whole-house-client:<tag>`（客户端 Vue3 + nginx）
- `macttnk/whole-house-admin:<tag>`（管理端 Vue3 + nginx）

`<tag>` 默认 `latest`；可通过环境变量 `WHC_IMAGE_TAG` 指定版本标签（如回滚到旧版本）。

## 路线一：Docker Compose 一键部署（推荐，不依赖 z app）

任意机器，装好 Docker（含 compose 插件）后：

```bash
git clone https://github.com/macsur/whole-house-customization.git
cd whole-house-customization

# 1. 准备环境变量（只放占位符，真实密码绝不入库）
cp .env.example .env
# 编辑 .env：把 __CHANGE_ME_*__ 占位符替换为随机强口令
vim .env

# 2. 一键拉起（优先拉 Docker Hub 镜像；镜像缺失/网络失败时自动本地构建兜底）
docker compose up -d --build
```

启动后默认端口：

| 端点 | 端口 | 说明 |
|------|------|------|
| 客户端 | `5173` | Vue3 展示端 |
| 管理端 | `5172` | Vue3 管理台 |
| 后端 API | `8000` | Django REST，健康检查 `http://<host>:8000/api/health/` |

MySQL 容器（`whc-mysql`）仅在内网通信，不对外映射端口；密码/SECRET 全部走根目录 `.env`。

## 路线二：通过 z app 安装（z.sh 自用应用）

已安装 [CODE MATRIX 代码矩阵](https://zttz.eu.org/z.sh) 的机器：

```bash
z app sync   # 拉取最新自用应用配置
z app 4      # 选择「木序定制 · 全屋定制平台」安装
```

z app 安装与 compose 一键部署共用同一套镜像优先/构建兜底逻辑：

1. **有镜像就拉**：优先从 Docker Hub 拉 `macttnk/whole-house-*:<tag>`，拉到即起容器，装机更快。
2. **没镜像就造**：拉取失败（标签不存在/网络失败）自动回退本地 build，安装输出中明示兜底触发。
3. **造好就上传**：本地构建新版本镜像后，由站主本人在部署机 `docker login` 并按交付帖提供的 push 清单上传（覆盖 `latest` + 版本标签）；密码不经任何脚本与仓库。

## 健康检查

```bash
curl http://<host>:8000/api/health/
# {"code":200,"message":"success","data":{"status":"ok","service":"whole-house-api"}}
```

## 源码开发模式

### 启动客户端

```bash
cd client/@latest
npm install
npm run dev
```

### 启动管理端

```bash
cd admin/@latest
npm install
npm run dev
```

### 启动后端

请先创建 MySQL 数据库，并根据 `service/WholeHouse/.env.example` 创建本地 `.env`。`.env` 需要放在 `service/WholeHouse/.env`，可填写为：

```dotenv
DJANGO_SECRET_KEY=请替换为随机且保密的字符串
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=whole_house_customization
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_HOST=127.0.0.1
DB_PORT=3306
```

其中 `DB_USER` 和 `DB_PASSWORD` 必须与本机 MySQL 账号一致；数据库名如有调整，应同时修改 `DB_NAME`。完整字段说明见 `service/WholeHouse/README.md`。真实 `.env` 已被 Git 忽略，请勿上传密码和密钥。

配置完成后执行：

```bash
cd service/WholeHouse
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

后端默认运行在 `http://127.0.0.1:8000`。详细说明见 `service/WholeHouse/README.md`。

## 隐私红线

本仓库与 README 不包含任何真实 IP、账号 ID、密码、密钥等敏感信息；所有真实凭据一律只存在于部署机的 `.env`（不入库、不入留言板、不入代码）。
