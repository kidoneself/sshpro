/**
 * NASPT 服务配置生成器 - Cloudflare Worker
 * 功能：
 * 1. 提供可视化配置页面
 * 2. 根据选择的服务动态生成 JSON 配置
 */

import { SERVICES_DATA } from './services-data.js';

// KV 存储键名
const KV_KEY_SERVICES = 'services_config';
const KV_KEY_NETWORKS = 'networks_config';
const KV_KEY_ENV_VARS = 'default_env_vars';

/**
 * 从 KV 获取所有服务，如果不存在则返回静态数据
 */
async function getServicesFromKV(env) {
  if (!env.SERVICES_KV) return SERVICES_DATA.services;
  const servicesJson = await env.SERVICES_KV.get(KV_KEY_SERVICES);
  return servicesJson ? JSON.parse(servicesJson) : SERVICES_DATA.services;
}

/**
 * 保存服务到 KV
 */
async function saveServicesToKV(env, services) {
  if (!env.SERVICES_KV) throw new Error('KV 未配置');
  await env.SERVICES_KV.put(KV_KEY_SERVICES, JSON.stringify(services));
}

/**
 * 从 KV 获取网络配置
 */
async function getNetworksFromKV(env) {
  if (!env.SERVICES_KV) return SERVICES_DATA.networks;
  const networksJson = await env.SERVICES_KV.get(KV_KEY_NETWORKS);
  return networksJson ? JSON.parse(networksJson) : SERVICES_DATA.networks;
}

/**
 * 从 KV 获取默认环境变量
 */
async function getEnvVarsFromKV(env) {
  if (!env.SERVICES_KV) return SERVICES_DATA.defaultEnvVars;
  const envVarsJson = await env.SERVICES_KV.get(KV_KEY_ENV_VARS);
  return envVarsJson ? JSON.parse(envVarsJson) : SERVICES_DATA.defaultEnvVars;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS 头
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // 处理 OPTIONS 请求
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // 路由处理
    if (url.pathname === '/api/services') {
      return handleServicesAPI(url, env, corsHeaders);
    } else if (url.pathname === '/api/all-services') {
      return handleAllServicesAPI(env, corsHeaders);
    } else if (url.pathname === '/admin') {
      // 服务管理页面
      return handleAdminPage();
    } else if (url.pathname === '/api/init-services') {
      // 初始化服务数据到 KV
      return handleInitServices(env, corsHeaders);
    } else if (url.pathname === '/api/service') {
      // 管理单个服务（CRUD）
      if (request.method === 'POST') {
        return await handleAddService(request, env, corsHeaders);
      } else if (request.method === 'PUT') {
        return await handleUpdateService(request, env, corsHeaders);
      } else if (request.method === 'DELETE') {
        return await handleDeleteService(url, env, corsHeaders);
      } else {
        return new Response(JSON.stringify({ success: false, message: '不支持的方法' }), {
          status: 405,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    } else {
      // 默认返回配置页面
      return handleConfigPage();
    }
  },
};

/**
 * 处理服务 API 请求（从 KV 读取）
 * GET /api/services?ids=moviepilot,qbittorrent,embyserver
 */
async function handleServicesAPI(url, env, corsHeaders) {
  try {
    const idsParam = url.searchParams.get('ids');
    
    if (!idsParam) {
      return new Response(
        JSON.stringify({ 
          success: false, 
          message: '缺少 ids 参数。示例: /api/services?ids=moviepilot,qbittorrent' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    const requestedIds = idsParam.split(',').map(id => id.trim()).filter(Boolean);
    
    if (requestedIds.length === 0) {
      return new Response(
        JSON.stringify({ success: false, message: 'ids 参数不能为空' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 从 KV 获取数据
    const allServices = await getServicesFromKV(env);
    const allNetworks = await getNetworksFromKV(env);
    const defaultEnvVars = await getEnvVarsFromKV(env);

    // 过滤服务
    const filteredServices = {};
    const requiredNetworks = new Set();

    requestedIds.forEach(id => {
      if (allServices[id]) {
        filteredServices[id] = allServices[id];
        
        // 收集需要的网络
        const requiresNetwork = allServices[id].requiresNetwork;
        if (requiresNetwork) {
          requiredNetworks.add(requiresNetwork);
        }
      }
    });

    if (Object.keys(filteredServices).length === 0) {
      return new Response(
        JSON.stringify({ 
          success: false, 
          message: '未找到匹配的服务',
          available_services: Object.keys(allServices)
        }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 过滤网络配置
    const filteredNetworks = {};
    requiredNetworks.forEach(networkName => {
      if (allNetworks[networkName]) {
        filteredNetworks[networkName] = allNetworks[networkName];
      }
    });

    // 构建响应
    const response = {
      version: "1.0",
      description: `筛选的服务配置 (${requestedIds.length} 个服务)`,
      services: filteredServices,
      networks: filteredNetworks,
      defaultEnvVars: defaultEnvVars,
    };

    return new Response(JSON.stringify(response, null, 2), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `服务器错误: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 获取所有可用服务列表（从 KV 读取）
 * GET /api/all-services
 */
async function handleAllServicesAPI(env, corsHeaders) {
  try {
    const allServices = await getServicesFromKV(env);
    
    // 确保 allServices 是对象
    if (!allServices || typeof allServices !== 'object') {
      throw new Error('服务数据格式错误');
    }
    
    const servicesList = Object.entries(allServices).map(([id, service]) => ({
      id,
      name: service.name,
      desc: service.desc,
      category: service.category || 'other',
      downloadUrl: service.downloadUrl || '',
      requiresNetwork: service.requiresNetwork || '',
    }));

    return new Response(JSON.stringify(servicesList), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('handleAllServicesAPI error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        message: `错误: ${error.message}`,
        stack: error.stack 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 返回配置页面
 */
function handleConfigPage() {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NASPT 服务配置生成器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e4e4e7;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .logo svg {
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: #a1a1aa;
            margin-top: 8px;
        }

        .card {
            background: rgba(30, 30, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .category {
            margin-bottom: 24px;
        }

        .category-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #3b82f6;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid rgba(59, 130, 246, 0.3);
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 12px;
        }

        .service-item {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .service-item:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.5);
            transform: translateY(-2px);
        }

        .service-item.selected {
            background: rgba(59, 130, 246, 0.2);
            border-color: #3b82f6;
        }

        .service-item label {
            display: flex;
            align-items: flex-start;
            cursor: pointer;
            gap: 8px;
        }

        .service-item input[type="checkbox"] {
            margin-top: 4px;
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .service-info {
            flex: 1;
        }

        .service-name {
            font-weight: 600;
            color: #e4e4e7;
            margin-bottom: 4px;
        }

        .service-desc {
            font-size: 0.85rem;
            color: #a1a1aa;
        }

        .actions {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }

        .btn {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #e4e4e7;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .result {
            display: none;
        }

        .result.show {
            display: block;
        }

        .result-url {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(59, 130, 246, 0.5);
            border-radius: 8px;
            padding: 16px;
            font-family: 'Courier New', monospace;
            color: #3b82f6;
            word-break: break-all;
            position: relative;
        }

        .copy-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid #3b82f6;
            color: #3b82f6;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        .copy-btn:hover {
            background: rgba(59, 130, 246, 0.3);
        }

        .copy-btn.copied {
            background: rgba(34, 197, 94, 0.2);
            border-color: #22c55e;
            color: #22c55e;
        }

        .selection-info {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
            text-align: center;
            color: #3b82f6;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #a1a1aa;
        }

        @media (max-width: 768px) {
            .services-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="32" height="32" rx="8" fill="url(#gradient)"/>
                    <path d="M8 12L16 8L24 12L16 16L8 12Z" fill="white" opacity="0.9"/>
                    <path d="M8 16L16 20L24 16V20L16 24L8 20V16Z" fill="white" opacity="0.7"/>
                    <defs>
                        <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#3b82f6"/>
                            <stop offset="1" stop-color="#2563eb"/>
                        </linearGradient>
                    </defs>
                </svg>
                <h1>NASPT</h1>
            </div>
            <p class="subtitle">Docker 服务配置生成器 | <a href="/admin" style="color: #3b82f6; text-decoration: none;">🛠️ 添加服务</a></p>
        </div>

        <div id="loading" class="loading">
            <p>加载服务配置中...</p>
        </div>

        <div id="content" style="display: none;">
            <div class="card">
                <div id="selection-info" class="selection-info" style="display: none;">
                    已选择 <strong id="selected-count">0</strong> 个服务
                </div>

                <div id="services-container"></div>

                <div class="actions">
                    <button class="btn btn-secondary" onclick="clearSelection()">清空选择</button>
                    <button class="btn btn-primary" onclick="generateConfig()">生成配置链接</button>
                </div>
            </div>

            <div id="result" class="card result">
                <h3 style="margin-bottom: 16px; color: #3b82f6;">生成的配置链接</h3>
                <div style="position: relative;">
                    <div id="result-url" class="result-url"></div>
                    <button class="copy-btn" onclick="copyToClipboard()">复制</button>
                </div>
                <p style="margin-top: 16px; color: #a1a1aa; font-size: 0.9rem;">
                    💡 将此链接粘贴到 NASPT 的"加载服务配置"功能中使用
                </p>
            </div>
        </div>
    </div>

    <script>
        let allServices = [];

        // 加载服务列表
        async function loadServices() {
            try {
                const response = await fetch('/api/all-services');
                allServices = await response.json();
                
                // 按类别分组
                const categories = {
                    'media': { title: '📺 媒体服务', services: [] },
                    'download': { title: '⬇️ 下载工具', services: [] },
                    'network': { title: '🌐 网络工具', services: [] },
                    'tool': { title: '🔧 实用工具', services: [] },
                    'other': { title: '📦 其他服务', services: [] }
                };

                allServices.forEach(service => {
                    const category = service.category || 'other';
                    if (categories[category]) {
                        categories[category].services.push(service);
                    } else {
                        categories.other.services.push(service);
                    }
                });

                // 渲染服务列表
                const container = document.getElementById('services-container');
                Object.entries(categories).forEach(([key, category]) => {
                    if (category.services.length > 0) {
                        const categoryDiv = document.createElement('div');
                        categoryDiv.className = 'category';
                        categoryDiv.innerHTML = \`
                            <div class="category-title">\${category.title}</div>
                            <div class="services-grid">
                                \${category.services.map(service => \`
                                    <div class="service-item" onclick="toggleService('\${service.id}')">
                                        <label>
                                            <input type="checkbox" id="service-\${service.id}" 
                                                   value="\${service.id}" onchange="updateSelection()">
                                            <div class="service-info">
                                                <div class="service-name">\${service.name}</div>
                                                <div class="service-desc">\${service.desc}</div>
                                            </div>
                                        </label>
                                    </div>
                                \`).join('')}
                            </div>
                        \`;
                        container.appendChild(categoryDiv);
                    }
                });

                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
            } catch (error) {
                document.getElementById('loading').innerHTML = \`
                    <p style="color: #ef4444;">加载失败: \${error.message}</p>
                \`;
            }
        }

        function toggleService(serviceId) {
            const checkbox = document.getElementById(\`service-\${serviceId}\`);
            checkbox.checked = !checkbox.checked;
            updateSelection();
        }

        function updateSelection() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            let count = 0;
            
            checkboxes.forEach(cb => {
                const item = cb.closest('.service-item');
                if (cb.checked) {
                    item.classList.add('selected');
                    count++;
                } else {
                    item.classList.remove('selected');
                }
            });

            const selectionInfo = document.getElementById('selection-info');
            const selectedCount = document.getElementById('selected-count');
            
            if (count > 0) {
                selectionInfo.style.display = 'block';
                selectedCount.textContent = count;
            } else {
                selectionInfo.style.display = 'none';
            }
        }

        function clearSelection() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = false);
            updateSelection();
            document.getElementById('result').classList.remove('show');
        }

        function generateConfig() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
            const selectedIds = Array.from(checkboxes).map(cb => cb.value);

            if (selectedIds.length === 0) {
                alert('请至少选择一个服务');
                return;
            }

            const url = \`\${window.location.origin}/api/services?ids=\${selectedIds.join(',')}\`;
            
            document.getElementById('result-url').textContent = url;
            document.getElementById('result').classList.add('show');
            
            // 滚动到结果
            document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function copyToClipboard() {
            const url = document.getElementById('result-url').textContent;
            const btn = document.querySelector('.copy-btn');
            
            navigator.clipboard.writeText(url).then(() => {
                btn.textContent = '已复制!';
                btn.classList.add('copied');
                
                setTimeout(() => {
                    btn.textContent = '复制';
                    btn.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                alert('复制失败，请手动复制');
            });
        }

        // 页面加载时初始化
        loadServices();
    </script>
</body>
</html>`;

  return new Response(html, {
    headers: { 
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    },
  });
}

/**
 * 初始化服务数据到 KV
 * GET /api/init-services
 */
async function handleInitServices(env, corsHeaders) {
  try {
    if (!env.SERVICES_KV) {
      return new Response(
        JSON.stringify({ success: false, message: 'KV 未配置' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 从 services-data.js 导入到 KV
    await env.SERVICES_KV.put(KV_KEY_SERVICES, JSON.stringify(SERVICES_DATA.services));
    await env.SERVICES_KV.put(KV_KEY_NETWORKS, JSON.stringify(SERVICES_DATA.networks));
    await env.SERVICES_KV.put(KV_KEY_ENV_VARS, JSON.stringify(SERVICES_DATA.defaultEnvVars));

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: '服务数据已初始化到 KV',
        count: Object.keys(SERVICES_DATA.services).length
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `初始化失败: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 添加新服务
 * POST /api/service
 */
async function handleAddService(request, env, corsHeaders) {
  try {
    const data = await request.json();
    const { id, name, desc, composeConfig, downloadUrl, category, requiresNetwork } = data;

    // 验证
    if (!id || !name || !desc || !composeConfig || !category) {
      return new Response(
        JSON.stringify({ success: false, message: '请填写所有必填字段' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 获取现有服务
    const services = await getServicesFromKV(env);

    // 检查 ID 是否已存在
    if (services[id]) {
      return new Response(
        JSON.stringify({ success: false, message: `服务 ID "${id}" 已存在` }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 构建新服务
    const newService = {
      name: name.trim(),
      desc: desc.trim(),
      config: composeConfig.trim(),
      downloadUrl: downloadUrl?.trim() || '',
      category: category,
    };

    if (requiresNetwork) {
      newService.requiresNetwork = requiresNetwork.trim();
    }

    // 添加到服务列表
    services[id] = newService;

    // 保存到 KV
    await saveServicesToKV(env, services);

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: '服务添加成功，已立即生效！',
        serviceId: id 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `错误: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 更新服务
 * PUT /api/service
 */
async function handleUpdateService(request, env, corsHeaders) {
  try {
    const data = await request.json();
    const { id, name, desc, composeConfig, downloadUrl, category, requiresNetwork } = data;

    if (!id) {
      return new Response(
        JSON.stringify({ success: false, message: '缺少服务 ID' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const services = await getServicesFromKV(env);

    if (!services[id]) {
      return new Response(
        JSON.stringify({ success: false, message: `服务 "${id}" 不存在` }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 更新服务
    services[id] = {
      name: name.trim(),
      desc: desc.trim(),
      config: composeConfig.trim(),
      downloadUrl: downloadUrl?.trim() || '',
      category: category,
    };

    if (requiresNetwork) {
      services[id].requiresNetwork = requiresNetwork.trim();
    }

    await saveServicesToKV(env, services);

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: '服务更新成功，已立即生效！',
        serviceId: id 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `错误: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 删除服务
 * DELETE /api/service?id=xxx
 */
async function handleDeleteService(url, env, corsHeaders) {
  try {
    const id = url.searchParams.get('id');

    if (!id) {
      return new Response(
        JSON.stringify({ success: false, message: '缺少服务 ID' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const services = await getServicesFromKV(env);

    if (!services[id]) {
      return new Response(
        JSON.stringify({ success: false, message: `服务 "${id}" 不存在` }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    delete services[id];
    await saveServicesToKV(env, services);

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: '服务删除成功，已立即生效！',
        serviceId: id 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `错误: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 服务生成 API（已废弃，保留用于兼容）
 * POST /api/generate-service
 */
async function handleGenerateService(request, corsHeaders) {
  try {
    const data = await request.json();
    const { id, name, desc, composeConfig, downloadUrl, category, requiresNetwork } = data;

    // 验证必填字段
    if (!id || !name || !desc || !composeConfig || !category) {
      return new Response(
        JSON.stringify({ success: false, message: '请填写所有必填字段' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 将 YAML 格式转换为 JSON 字符串（保留换行和缩进）
    const configString = composeConfig.trim();

    // 构建服务对象
    const serviceObject = {
      name: name.trim(),
      desc: desc.trim(),
      config: configString,
      downloadUrl: downloadUrl?.trim() || '',
      category: category,
    };

    if (requiresNetwork) {
      serviceObject.requiresNetwork = requiresNetwork.trim();
    }

    // 生成代码片段
    const codeSnippet = `    "${id}": ${JSON.stringify(serviceObject, null, 6).replace(/^/gm, '    ').trim()}`;

    return new Response(
      JSON.stringify({ 
        success: true, 
        code: codeSnippet,
        serviceId: id 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, message: `错误: ${error.message}` }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * 服务管理页面
 * GET /admin
 */
function handleAdminPage() {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NASPT 服务管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e4e4e7;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        .nav-link { display: inline-block; margin-bottom: 16px; color: #3b82f6; text-decoration: none; }
        .card {
            background: rgba(30, 30, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
        }
        .btn-danger { background: #ef4444; color: white; }
        .btn-secondary { background: rgba(255, 255, 255, 0.1); color: #e4e4e7; }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; }
        input, select, textarea {
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #e4e4e7;
            font-family: inherit;
        }
        textarea { font-family: 'Courier New', monospace; min-height: 200px; resize: vertical; }
        .service-list { display: grid; gap: 12px; }
        .service-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .service-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px; }
        .service-actions { display: flex; gap: 8px; }
        .alert { padding: 12px; border-radius: 8px; margin-bottom: 16px; }
        .alert-success { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: #86efac; }
        .alert-error { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #fca5a5; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="https://naspt-services.kidonself.workers.dev/" class="nav-link">← 返回首页</a>
            <h1>🛠️ 服务管理</h1>
            <p style="color: #a1a1aa;">在线管理 Docker 服务 - 立即生效</p>
        </div>

        <div id="message"></div>

        <!-- 服务列表 -->
        <div class="card">
            <h2 style="margin-bottom: 16px; color: #3b82f6;">现有服务</h2>
            <div id="servicesList" class="service-list">
                <p style="color: #a1a1aa;">加载中...</p>
            </div>
        </div>

        <!-- 添加/编辑服务 -->
        <div class="card">
            <h2 style="margin-bottom: 16px; color: #3b82f6;">添加/编辑服务</h2>
            <form id="serviceForm">
                <input type="hidden" id="editingId">
                
                <div class="form-group">
                    <label>服务 ID *</label>
                    <input type="text" id="serviceId" placeholder="jellyfin" required>
                </div>

                <div class="form-group">
                    <label>服务名称 *</label>
                    <input type="text" id="serviceName" placeholder="Jellyfin" required>
                </div>

                <div class="form-group">
                    <label>服务描述 *</label>
                    <input type="text" id="serviceDesc" placeholder="开源媒体服务器" required>
                </div>

                <div class="form-group">
                    <label>分类 *</label>
                    <select id="serviceCategory" required>
                        <option value="">选择分类</option>
                        <option value="media">📺 媒体服务</option>
                        <option value="download">⬇️ 下载工具</option>
                        <option value="network">🌐 网络工具</option>
                        <option value="tool">🔧 实用工具</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>依赖网络</label>
                    <input type="text" id="serviceNetwork" placeholder="moviepilot-network">
                </div>

                <div class="form-group">
                    <label>下载地址</label>
                    <input type="text" id="serviceDownloadUrl" placeholder="https://example.com/config.tgz">
                </div>

                <div class="form-group">
                    <label>Docker Compose 配置 *</label>
                    <textarea id="serviceCompose" required placeholder="jellyfin:
  image: jellyfin/jellyfin:latest
  container_name: jellyfin
  restart: unless-stopped
  ports:
    - &quot;8096:8096&quot;
  volumes:
    - \${DOCKER_PATH}/jellyfin:/config"></textarea>
                </div>

                <div style="display: flex; gap: 12px;">
                    <button type="submit" class="btn btn-primary">保存服务</button>
                    <button type="button" class="btn btn-secondary" onclick="clearForm()">清空表单</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const WORKER_URL = 'https://naspt-services.kidonself.workers.dev';
        let allServices = [];

        // 加载服务列表
        async function loadServices() {
            try {
                const response = await fetch(WORKER_URL + '/api/all-services');
                const text = await response.text();
                console.log('API Response:', text);
                allServices = JSON.parse(text);
                renderServices();
            } catch (error) {
                console.error('Load error:', error);
                showMessage('加载失败: ' + error.message, 'error');
            }
        }

        // 渲染服务列表
        function renderServices() {
            const container = document.getElementById('servicesList');
            if (allServices.length === 0) {
                container.innerHTML = '<p style="color: #a1a1aa;">暂无服务</p>';
                return;
            }

            container.innerHTML = allServices.map(service => \`
                <div class="service-card">
                    <div class="service-header">
                        <div>
                            <h3 style="color: #e4e4e7; margin-bottom: 4px;">\${service.name}</h3>
                            <p style="color: #a1a1aa; font-size: 0.9rem;">\${service.desc}</p>
                            <p style="color: #6b7280; font-size: 0.85rem; margin-top: 4px;">
                                ID: <code>\${service.id}</code> | 分类: \${getCategoryName(service.category)}
                            </p>
                        </div>
                        <div class="service-actions">
                            <button class="btn btn-secondary" style="padding: 8px 16px;" onclick="editService('\${service.id}')">编辑</button>
                            <button class="btn btn-danger" style="padding: 8px 16px;" onclick="deleteService('\${service.id}')">删除</button>
                        </div>
                    </div>
                </div>
            \`).join('');
        }

        function getCategoryName(category) {
            const names = {
                'media': '📺 媒体',
                'download': '⬇️ 下载',
                'network': '🌐 网络',
                'tool': '🔧 工具'
            };
            return names[category] || category;
        }

        // 显示消息
        function showMessage(msg, type = 'success') {
            const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
            document.getElementById('message').innerHTML = \`
                <div class="alert \${alertClass}">\${msg}</div>
            \`;
            setTimeout(() => {
                document.getElementById('message').innerHTML = '';
            }, 3000);
        }

        // 提交表单
        document.getElementById('serviceForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const editingId = document.getElementById('editingId').value;
            const formData = {
                id: document.getElementById('serviceId').value.trim(),
                name: document.getElementById('serviceName').value.trim(),
                desc: document.getElementById('serviceDesc').value.trim(),
                composeConfig: document.getElementById('serviceCompose').value,
                downloadUrl: document.getElementById('serviceDownloadUrl').value.trim(),
                category: document.getElementById('serviceCategory').value,
                requiresNetwork: document.getElementById('serviceNetwork').value.trim()
            };

            try {
                const method = editingId ? 'PUT' : 'POST';
                const response = await fetch(WORKER_URL + '/api/service', {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                if (result.success) {
                    showMessage(result.message);
                    clearForm();
                    await loadServices();
                } else {
                    showMessage(result.message, 'error');
                }
            } catch (error) {
                showMessage('操作失败: ' + error.message, 'error');
            }
        });

        // 编辑服务
        async function editService(id) {
            const service = allServices.find(s => s.id === id);
            if (!service) return;

            try {
                const response = await fetch(WORKER_URL + '/api/services?ids=' + id);
                const data = await response.json();
                const fullService = data.services[id];

                document.getElementById('editingId').value = id;
                document.getElementById('serviceId').value = id;
                document.getElementById('serviceId').disabled = true;
                document.getElementById('serviceName').value = service.name;
                document.getElementById('serviceDesc').value = service.desc;
                document.getElementById('serviceCategory').value = service.category;
                document.getElementById('serviceNetwork').value = service.requiresNetwork || '';
                document.getElementById('serviceDownloadUrl').value = service.downloadUrl || '';
                document.getElementById('serviceCompose').value = fullService.config;

                document.getElementById('serviceForm').scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                showMessage('获取服务详情失败: ' + error.message, 'error');
            }
        }

        // 删除服务
        async function deleteService(id) {
            if (!confirm('确定要删除服务 "' + id + '" 吗？')) return;

            try {
                const response = await fetch(WORKER_URL + '/api/service?id=' + id, {
                    method: 'DELETE'
                });

                const result = await response.json();
                if (result.success) {
                    showMessage(result.message);
                    await loadServices();
                } else {
                    showMessage(result.message, 'error');
                }
            } catch (error) {
                showMessage('删除失败: ' + error.message, 'error');
            }
        }

        // 清空表单
        function clearForm() {
            document.getElementById('serviceForm').reset();
            document.getElementById('editingId').value = '';
            document.getElementById('serviceId').disabled = false;
        }

        // 初始加载
        loadServices();
    </script>
</body>
</html>
`;
  return new Response(html, {
    headers: { 
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    },
  });
}
