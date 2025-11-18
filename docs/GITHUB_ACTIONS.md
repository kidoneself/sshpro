# GitHub Actions 自动构建指南

本项目使用 GitHub Actions 自动构建 macOS、Windows 和 Docker 镜像。

## 工作流说明

### 1. 自动触发条件

- **推送到 main 分支**：自动构建所有平台
- **创建版本标签（v*）**：构建并创建 GitHub Release
- **Pull Request**：仅构建可执行文件（不推送 Docker）
- **手动触发**：可在 Actions 页面手动运行

### 2. 构建内容

#### macOS 应用
- 构建 `.app` 应用包
- 自动打包为 `naspt-macos.zip`
- 保存为 Artifact，保留 30 天

#### Windows 可执行文件
- 构建 `naspt.exe` 单文件
- 保存为 Artifact，保留 30 天

#### Docker 镜像
- 多架构构建：`linux/amd64` 和 `linux/arm64`
- 自动推送到 Docker Hub：`kidself/naspt`
- 标签规则：
  - `latest`：main 分支最新版本
  - `v1.0.0`：版本标签
  - `1.0`：主版本号

## 配置 Docker Hub

### 1. 创建 Docker Hub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

1. 进入仓库：`Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下两个 secrets：

   - **Name**: `DOCKER_USERNAME`
     **Value**: 你的 Docker Hub 用户名（例如：`kidself`）

   - **Name**: `DOCKER_PASSWORD`
     **Value**: 你的 Docker Hub 访问令牌（Access Token）

### 2. 获取 Docker Hub Access Token

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 进入 `Account Settings` → `Security`
3. 点击 `New Access Token`
4. 输入描述（如：`GitHub Actions`）
5. 复制生成的 token（只显示一次）
6. 将 token 添加到 GitHub Secrets 的 `DOCKER_PASSWORD`

## 使用方式

### 自动构建

每次推送到 `main` 分支时，会自动触发构建：

```bash
git push origin main
```

### 创建版本发布

创建版本标签会自动构建并创建 GitHub Release：

```bash
# 创建标签
git tag v1.0.0
git push origin v1.0.0
```

### 手动触发

1. 进入 GitHub 仓库的 `Actions` 页面
2. 选择 `Build Executables` 工作流
3. 点击 `Run workflow`
4. 选择分支并运行

## 下载构建产物

### 从 GitHub Actions

1. 进入仓库的 `Actions` 页面
2. 选择最新的工作流运行
3. 在 `Artifacts` 部分下载：
   - `naspt-macos`：macOS 应用包
   - `naspt-macos-zip`：macOS 压缩包
   - `naspt-windows`：Windows 可执行文件

### 从 GitHub Releases

如果创建了版本标签，可以在 `Releases` 页面下载：
- `naspt-macos.zip`
- `naspt.exe`

### 从 Docker Hub

```bash
# 拉取最新版本
docker pull kidself/naspt:latest

# 拉取特定版本
docker pull kidself/naspt:v1.0.0

# 运行
docker run -d --rm --name naspt -p 15432:15432 kidself/naspt:latest
```

## 工作流文件

- `.github/workflows/build.yml`：主构建工作流
- `.github/workflows/build-on-demand.yml`：按需构建工作流

## 故障排查

### Docker 构建失败

1. **检查 Secrets 配置**
   - 确认 `DOCKER_USERNAME` 和 `DOCKER_PASSWORD` 已正确设置
   - 确认 Docker Hub token 有效

2. **检查 Docker Hub 权限**
   - 确认账户有权限推送到 `kidself/naspt`

### 可执行文件构建失败

1. **检查依赖**
   - 确认 `requirements.txt` 和 `scripts/requirements-build.txt` 正确
   - 检查 PyInstaller 版本兼容性

2. **查看构建日志**
   - 在 Actions 页面查看详细错误信息

## 注意事项

1. **Docker 构建仅在 push 时触发**：Pull Request 不会推送 Docker 镜像
2. **Artifacts 保留时间**：默认保留 30 天，可在工作流中修改
3. **Docker 镜像标签**：main 分支自动标记为 `latest`
4. **版本标签格式**：使用 `v1.0.0` 格式（v 开头）

