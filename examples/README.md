# 示例配置文件

本目录包含各种示例配置文件，供参考使用。

## 文件说明

### docker-compose.naspt.yml
NASPT 自身的 Docker Compose 部署配置，用于部署 NASPT 服务。

**使用方法：**
```bash
docker compose -f examples/docker-compose.naspt.yml up -d
```

### docker-compose.all-services.yml
完整的 Docker 服务配置示例，包含：
- MoviePilot（影视自动化管理）
- qBittorrent（BT下载）
- Transmission（BT下载）
- EmbyServer（媒体服务器）
- Roon Server（音乐服务器）
- BiliLive-Go（哔哩哔哩直播录制）
- Clash（代理服务）
- FRP Client（内网穿透）

**注意：** 此文件使用环境变量，需要创建 `.env` 文件或设置环境变量：
- `DOCKER_PATH` - Docker配置路径
- `MEDIA_DIR` - 媒体文件目录
- `MUSIC_DIR` - 音乐文件目录
- `RECORD_DIR` - 录制文件目录

### docker-compose.example.yml
简单的 Docker Compose 配置示例模板。

### services.example.json
服务配置 JSON 模板，用于前端加载服务列表。

**使用方法：**
1. 将此文件上传到可访问的 URL
2. 在 NASPT 前端界面中，输入该 URL
3. 点击"加载服务配置"
4. 服务列表会自动填充到 Docker Compose 编辑器

**JSON 结构说明：**
- `services` - 服务配置对象
  - `name` - 服务显示名称
  - `desc` - 服务描述
  - `config` - Docker Compose 配置内容（YAML格式字符串）
  - `downloadUrl` - 可选，数据包下载地址
  - `category` - 服务分类（media/download/network/tool）
  - `requiresNetwork` - 可选，需要的网络名称
- `networks` - 网络配置
- `defaultEnvVars` - 默认环境变量

## 注意事项

1. 所有配置文件中的路径、密码等需要根据实际情况修改
2. 示例文件中的密码为示例，请修改为安全密码
3. 环境变量需要根据你的实际目录结构设置

