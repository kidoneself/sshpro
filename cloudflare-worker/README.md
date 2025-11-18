# NASPT 服务配置生成器 - Cloudflare Worker

基于 Cloudflare Workers + KV 的全自动 Docker 服务配置管理系统。

## ✨ 核心特性

### 🎯 用户端
- 📊 可视化服务选择界面
- ✅ 多选服务并生成配置链接
- 🔗 一键复制，直接用于 NASPT
- 📱 响应式设计，移动端友好

### 🛠️ 管理端
- 🌐 在线 Web 管理界面
- ➕ 添加新服务（立即生效）
- ✏️ 编辑现有服务配置
- 🗑️ 删除不需要的服务
- 🚀 零停机更新

### 🔌 RESTful API
- 动态生成 Docker Compose 配置
- KV 存储，边缘计算
- CORS 支持，跨域访问
- 完整的 CRUD 操作

## 🚀 快速开始

### 方式 1: Wrangler CLI 部署（推荐）

```bash
# 1. 安装 Wrangler
npm install -g wrangler

# 2. 登录 Cloudflare
wrangler login

# 3. 创建 KV 命名空间
wrangler kv:namespace create "SERVICES_KV"
# 将返回的 ID 填入 wrangler.toml 的 kv_namespaces.id

# 4. 部署 Worker
wrangler deploy

# 5. 初始化 KV 数据
curl https://your-worker.workers.dev/api/init-services

# 6. 访问管理界面
open https://your-worker.workers.dev/admin
```

### 方式 2: Cloudflare Dashboard 部署

详见 [全自动KV方案-完整指南.md](./全自动KV方案-完整指南.md)

## 📖 使用指南

### 用户使用
1. 访问 Worker URL（如：`https://naspt-services.your-account.workers.dev`）
2. 勾选需要的 Docker 服务
3. 点击"生成配置链接"
4. 复制链接，在 NASPT 中使用

### 管理服务
1. 访问 `/admin` 路径
2. 在表单中填写服务信息和 Docker Compose 配置
3. 点击"保存服务" → **立即生效，无需重新部署**
4. 支持编辑和删除现有服务

## 🔧 本地开发

```bash
# 启动开发服务器
wrangler dev

# 访问本地服务
open http://localhost:8787
```

## API 使用

### 1. 获取所有服务列表

```http
GET /api/all-services
```

**响应示例**:
```json
[
  {
    "id": "moviepilot",
    "name": "MoviePilot",
    "desc": "影视自动化管理",
    "category": "media"
  },
  {
    "id": "qbittorrent",
    "name": "qBittorrent",
    "desc": "BT下载工具",
    "category": "download"
  }
]
```

### 2. 获取筛选后的配置

```http
GET /api/services?ids=moviepilot,qbittorrent,embyserver
```

**参数**:
- `ids`: 服务 ID 列表，用逗号分隔

**响应示例**:
```json
{
  "version": "1.0",
  "description": "筛选的服务配置 (3 个服务)",
  "services": {
    "moviepilot": { ... },
    "qbittorrent": { ... },
    "embyserver": { ... }
  },
  "networks": {
    "moviepilot-network": {
      "driver": "bridge"
    }
  },
  "defaultEnvVars": {
    "DOCKER_PATH": "/volume1/docker",
    "MEDIA_DIR": "/volume1/media",
    "MUSIC_DIR": "/volume1/music",
    "RECORD_DIR": "/volume1/record"
  }
}
```

## 在 NASPT 中使用

1. **打开 NASPT 应用**
   - 访问 http://localhost:15432

2. **加载服务配置**
   - 在"加载服务配置"输入框中粘贴生成的 URL
   - 点击"加载配置"按钮
   - 服务配置会自动填充到 Docker Compose 编辑器

## 自定义域名（可选）

1. 在 Cloudflare Dashboard 中进入 Worker
2. 点击 `Triggers` → `Add Custom Domain`
3. 输入你的域名（需要已在 Cloudflare 托管）
4. 完成 DNS 配置

示例：`https://services.your-domain.com`

## 📁 项目结构

```
cloudflare-worker/
├── worker.js                      # Worker 主代码 (1258 行)
├── services-data.js               # 初始服务数据配置
├── wrangler.toml                  # Worker 部署配置
├── package.json                   # NPM 依赖配置
├── deploy.sh                      # 自动部署脚本
├── .gitignore                     # Git 忽略配置
├── README.md                      # 本文档
├── CHANGELOG.md                   # 更新日志
├── PROJECT_STRUCTURE.md           # 项目结构详细说明
├── 全自动KV方案-完整指南.md      # 完整技术文档
└── 快速开始.md                    # 快速部署指南
```

详见 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## 🔄 更新服务配置

### 推荐方式：使用管理界面（零停机）

1. 访问 `/admin` 管理界面
2. 添加/编辑/删除服务
3. **立即生效，无需重新部署！**

### 传统方式：修改代码（需重新部署）

修改 `services-data.js`，然后：

```bash
wrangler deploy
```

## 免费额度

Cloudflare Workers 免费计划：
- ✅ 每天 100,000 次请求
- ✅ 无限 Workers
- ✅ 全球 CDN 加速
- ✅ 自动 HTTPS

对于个人使用完全足够！

## 故障排除

### 部署失败

1. 确保已登录 Cloudflare：
   ```bash
   wrangler whoami
   ```

2. 检查 wrangler.toml 配置是否正确

3. 查看详细错误信息：
   ```bash
   wrangler deploy --verbose
   ```

### CORS 错误

Worker 已配置 CORS 头，允许所有来源访问。如果仍有问题，检查浏览器控制台错误。

### 服务未显示

检查 `services-data.js` 格式是否正确，确保是有效的 JavaScript 对象。

## 许可证

MIT License

## 支持

如有问题，请提交 Issue 或查看 [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)。
