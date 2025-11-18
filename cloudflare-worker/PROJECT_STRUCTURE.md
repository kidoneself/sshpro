# 项目结构

```
cloudflare-worker/
├── worker.js                      # Cloudflare Worker 主代码
├── services-data.js               # 初始服务数据配置
├── wrangler.toml                  # Worker 部署配置
├── package.json                   # NPM 依赖配置
├── deploy.sh                      # 自动部署脚本
├── .gitignore                     # Git 忽略配置
├── README.md                      # 项目说明文档
├── CHANGELOG.md                   # 更新日志
├── PROJECT_STRUCTURE.md           # 本文件 - 项目结构说明
├── 全自动KV方案-完整指南.md      # 详细技术文档
└── 快速开始.md                    # 快速部署指南
```

## 核心文件说明

### worker.js (1258 行)
Cloudflare Worker 主代码，包含：
- 路由处理逻辑
- KV 数据读写函数
- RESTful API 实现 (CRUD)
- 用户界面 HTML（首页和管理页）
- CORS 处理
- 缓存控制

### services-data.js (140 行)
初始服务数据配置：
- Docker 服务定义
- 网络配置
- 默认环境变量
- 用于 KV 初始化

### wrangler.toml (27 行)
Worker 部署配置：
- Worker 名称和入口文件
- KV 命名空间绑定
- 兼容性日期设置

## API 端点

### 用户 API
- `GET /` - 主页（服务选择界面）
- `GET /api/services?ids=xxx,yyy` - 获取指定服务配置

### 管理 API
- `GET /admin` - 管理界面
- `GET /api/all-services` - 获取所有服务列表
- `POST /api/service` - 添加新服务
- `PUT /api/service` - 更新服务
- `DELETE /api/service?id=xxx` - 删除服务
- `GET /api/init-services` - 初始化 KV 数据

## 技术栈

- **运行环境**: Cloudflare Workers (Edge Computing)
- **存储**: Cloudflare KV (Key-Value Store)
- **前端**: 原生 HTML/CSS/JavaScript
- **API**: RESTful 架构
- **部署**: Wrangler CLI

## 开发建议

### 本地测试
```bash
wrangler dev
```

### 查看日志
```bash
wrangler tail
```

### 管理 KV
```bash
# 查看所有 KV 数据
wrangler kv:key list --namespace-id=YOUR_ID

# 读取特定 key
wrangler kv:key get services_config --namespace-id=YOUR_ID

# 删除 key
wrangler kv:key delete KEY_NAME --namespace-id=YOUR_ID
```

## 代码风格

- 使用 2 空格缩进
- 函数命名采用驼峰命名法
- API 函数以 `handle` 开头
- 完整的注释和文档字符串
- 错误处理和日志记录
