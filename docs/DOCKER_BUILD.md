# Docker 构建指南

## 多架构构建（推荐）

支持 `linux/amd64` 和 `linux/arm64` 两种架构。

### 前置要求

1. 安装 Docker Buildx（Docker Desktop 已包含）
2. 如果使用 Docker Engine，需要安装 buildx 插件：
   ```bash
   docker buildx install
   ```

### 构建多架构镜像

#### 1. 构建并推送到 Docker Hub

```bash
# 构建并推送到 Docker Hub
./build-docker.sh latest your-dockerhub-username

# 例如：
./build-docker.sh latest myusername
# 会构建: myusername/naspt:latest
```

#### 2. 构建并推送到私有 Registry

```bash
# 构建并推送到私有 Registry
./build-docker.sh latest registry.example.com

# 例如：
./build-docker.sh latest registry.example.com:5000
# 会构建: registry.example.com:5000/naspt:latest
```

#### 3. 仅构建本地镜像（不推送）

修改 `build-docker.sh`，将 `--push` 改为 `--load`（注意：`--load` 只支持单架构）

### 本地单架构构建（用于测试）

```bash
# 构建当前系统架构的镜像
./build-docker-local.sh latest

# 或者直接使用 docker build
docker build -t naspt:latest .
```

### 运行容器

#### 使用 docker-compose

```bash
docker-compose up -d
```

#### 使用 docker run

```bash
docker run -d \
  --name naspt \
  -p 15432:15432 \
  --restart unless-stopped \
  naspt:latest
```

### 验证多架构镜像

```bash
# 查看镜像支持的架构
docker buildx imagetools inspect your-username/naspt:latest
```

### 手动构建多架构镜像

如果脚本不工作，可以手动执行：

```bash
# 创建 builder
docker buildx create --name multiarch --use

# 启动 builder
docker buildx inspect --bootstrap

# 构建并推送
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag your-username/naspt:latest \
  --push \
  .
```

## 注意事项

1. **多架构构建需要推送**：`docker buildx build` 的 `--load` 选项只支持单架构，多架构构建必须使用 `--push`
2. **需要登录 Registry**：推送前需要先登录
   ```bash
   docker login  # Docker Hub
   # 或
   docker login registry.example.com  # 私有 Registry
   ```
3. **构建时间**：多架构构建会为每个架构分别构建，耗时较长
4. **端口映射**：应用默认使用 15432 端口，确保映射正确

