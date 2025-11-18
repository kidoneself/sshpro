# NASPT - SSH & Docker 管理工具

一个基于Web的SSH连接和Docker管理工具，可以通过浏览器连接到远程SSH服务器，执行Docker Compose部署、批量下载等功能。

## 功能特性

### 1. SSH连接管理
- 支持多个SSH连接配置，可保存到本地浏览器
- 自动尝试切换到root用户（如果密码正确）
- 实时终端交互，基于xterm.js的Web终端
- 支持清屏功能

### 2. Docker Compose部署
- 可视化编辑 `docker-compose.yml` 和 `.env` 文件
- 一键启动、停止服务，查看日志
- 自动将配置文件保存到远程服务器的持久化目录（`<Docker配置路径>/naspt/compose/`）

### 3. 批量下载与解压
- 支持飞牛分享链接自动解析和下载
- 支持普通HTTP/HTTPS链接下载
- 自动解压 tar.gz、tgz、tar 格式文件
- 下载文件保存到 `<Docker配置路径>/naspt/downloads/`
- 解压内容保存到 `<Docker配置路径>/naspt/`

### 4. 路径管理
- 配置Docker路径，自动创建统一的目录结构：
  - `<配置路径>/naspt/` - 主目录
  - `<配置路径>/naspt/downloads/` - 下载文件
  - `<配置路径>/naspt/tmp/` - 临时文件
  - `<配置路径>/naspt/compose/` - Docker Compose

### 5. 服务配置加载
- 支持从远程JSON URL加载服务配置
- 自动解析并填充到Docker Compose编辑器

## 快速开始

### 使用Docker（推荐）

#### 从Docker Hub拉取

```bash
docker pull kidself/naspt:latest
docker run -d --rm --name naspt -p 15432:15432 kidself/naspt:latest
```

#### 本地构建

```bash
# 构建单平台镜像
docker build -t kidself/naspt:latest .

# 构建多平台镜像（amd64 + arm64）
bash build-docker.sh latest kidself
```

### 访问Web界面

打开浏览器访问：`http://localhost:15432`

## 使用步骤

### 1. 添加SSH连接

1. 点击"添加连接"按钮
2. 输入SSH连接信息：
   - 连接名称（用于标识）
   - 主机地址
   - 端口（默认22）
   - 用户名
   - 密码
3. 点击"添加连接"保存

### 2. 连接SSH

1. 在连接列表中找到要连接的服务器
2. 点击"连接"按钮
3. 连接成功后，终端会显示远程服务器的提示符
4. 如果用户名不是root，系统会自动尝试切换到root用户

### 3. 配置Docker路径

1. 在"配置信息"区域输入Docker配置路径（例如：`/volume1/test`）
2. 系统会自动在该路径下创建 `naspt` 目录结构
3. 所有下载、解压、Compose文件都会保存在该目录下

### 4. 部署Docker Compose

1. 在"Docker Compose"区域编辑 `docker-compose.yml` 内容
2. （可选）点击"配置.env"按钮编辑环境变量
3. 点击"启动服务"、"停止服务"或"查看日志"按钮
4. 配置文件会自动保存到远程服务器的 `<配置路径>/naspt/compose/` 目录

### 5. 批量下载

1. 在"批量下载"区域输入下载链接（每行一个）
2. 支持飞牛分享链接（自动解析认证信息）
3. 支持普通HTTP/HTTPS链接
4. 点击"开始下载"按钮
5. 下载的文件会自动解压到目标目录

## 环境变量

- `NASPT_REMOTE_BASE_DIR`: 远程服务器上的默认基础路径（默认：`/docker/naspt`）

## 技术栈

- **后端**: Python 3.11 + Flask + Flask-SocketIO
- **前端**: HTML + JavaScript + xterm.js + Socket.IO Client
- **SSH**: paramiko
- **通信**: WebSocket (Socket.IO)
- **下载**: curl, wget
- **解压**: tar

## 项目结构

```
naspt/
├── app.py                    # Flask应用主文件
├── parse_share_link.py       # 飞牛分享链接解析器
├── requirements.txt          # Python依赖
├── Dockerfile               # Docker构建文件
├── templates/
│   └── index.html           # 主页面
├── docker/                  # 本地数据目录（用于开发）
│   ├── compose/            # Compose文件
│   ├── downloads/          # 下载文件
│   └── tmp/                # 临时文件
├── docs/                    # 文档目录
│   ├── BUILD_EXE.md        # EXE打包指南
│   ├── DOCKER_BUILD.md     # Docker构建文档
│   └── SIGNATURE_ALGORITHM.md  # 签名算法文档
├── scripts/                 # 脚本目录
│   ├── build-docker.sh     # Docker多平台构建脚本
│   ├── build-docker-local.sh  # Docker本地构建脚本
│   ├── build-exe.bat       # Windows EXE打包脚本
│   ├── build-exe.sh        # Linux/macOS EXE打包脚本
│   ├── build-exe.spec      # PyInstaller配置文件
│   └── requirements-build.txt  # 打包依赖
├── examples/                # 示例配置文件
│   ├── docker-compose.naspt.yml  # NASPT部署配置
│   ├── docker-compose.all-services.yml  # 完整服务配置示例
│   ├── docker-compose.example.yml  # 简单配置示例
│   ├── services.example.json  # 服务配置JSON模板
│   └── README.md            # 示例文件说明
└── README.md               # 说明文档
```

## 开发

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

### 构建Docker镜像

```bash
# 单平台构建
docker build -t kidself/naspt:latest .

# 多平台构建（需要先创建buildx builder）
docker buildx create --name multiarch-builder --use
bash scripts/build-docker.sh latest kidself
```

### GitHub Actions 自动构建

项目已配置 GitHub Actions，推送到 `main` 分支会自动构建：

- **macOS 应用**：自动打包为 `.app` 和 `.zip`
- **Windows 可执行文件**：自动打包为 `.exe`
- **Docker 镜像**：自动构建多架构镜像并推送到 Docker Hub

**配置 Docker Hub Secrets**（首次使用需要）：
1. 进入 GitHub 仓库：`Settings` → `Secrets and variables` → `Actions`
2. 添加以下 Secrets：
   - `DOCKER_USERNAME`：你的 Docker Hub 用户名
   - `DOCKER_PASSWORD`：你的 Docker Hub Access Token

详细说明请查看：[GitHub Actions 文档](docs/GITHUB_ACTIONS.md)

## 注意事项

1. SSH密码会以Base64编码保存在浏览器localStorage中，不是真正的加密，请谨慎使用
2. 批量下载功能需要远程服务器有足够的磁盘空间
3. Docker Compose部署需要远程服务器已安装Docker和docker-compose
4. 所有文件操作都在远程服务器上执行，请确保有足够的权限

## 许可证

MIT License
