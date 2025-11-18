# 更新日志

## 2025-11-19

### ✨ 新功能
- 完整的 Cloudflare KV 动态服务管理系统
- 在线 Web 管理界面 (`/admin`)
- RESTful API 支持 CRUD 操作
- 实时生效，无需重新部署

### 🛠️ 核心功能
- **用户端**: 可视化选择服务，生成配置链接
- **管理端**: 在线添加、编辑、删除 Docker 服务
- **KV 存储**: 服务配置持久化存储
- **API 端点**:
  - `GET /api/all-services` - 获取所有服务列表
  - `GET /api/services?ids=xxx,yyy` - 获取指定服务配置
  - `POST /api/service` - 添加新服务
  - `PUT /api/service` - 更新服务
  - `DELETE /api/service?id=xxx` - 删除服务
  - `GET /api/init-services` - 初始化 KV 数据

### 🎨 技术特性
- 完全无服务器架构
- 边缘计算，全球加速
- 零停机更新
- CORS 支持
- 缓存控制优化

### 📦 部署方式
```bash
# 安装依赖
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 创建 KV 命名空间
wrangler kv:namespace create "SERVICES_KV"

# 部署
wrangler deploy

# 初始化数据
curl https://your-worker.workers.dev/api/init-services
```

### 📚 文档
- `README.md` - 项目概览和快速开始
- `全自动KV方案-完整指南.md` - 详细技术文档
- `快速开始.md` - 快速部署指南
