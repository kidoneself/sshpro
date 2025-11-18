# Windows EXE 打包指南

## 前置要求

1. **Windows 系统**（Windows 10/11）
2. **Python 3.11+** 已安装
3. **所有依赖已安装**

## 打包步骤

### 1. 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装打包工具
pip install -r scripts/requirements-build.txt
```

### 2. 执行打包

**方式一：使用批处理脚本（推荐）**
```bash
scripts\build-exe.bat
```

**方式二：手动执行**
```bash
pyinstaller scripts\build-exe.spec
```

### 3. 获取 EXE 文件

打包完成后，EXE 文件位于：
```
dist/naspt.exe
```

## 打包配置说明

### build-exe.spec 配置

- **单文件模式**：`--onefile`（已配置）
- **控制台窗口**：`console=True`（显示日志）
- **包含的文件**：
  - `templates/` 目录
  - `static/` 目录（如果有）
- **隐藏导入**：已包含所有必要的模块

### 文件大小

预计打包后的 exe 文件大小：**80-150MB**

## 使用打包后的 EXE

1. 双击 `naspt.exe` 运行
2. 程序会自动：
   - 启动 Web 服务（http://localhost:15432）
   - 打开浏览器访问界面
3. 关闭程序：关闭控制台窗口或按 `Ctrl+C`

## 常见问题

### 1. 打包失败：缺少模块

如果提示缺少某个模块，在 `build-exe.spec` 的 `hiddenimports` 中添加：
```python
hiddenimports=[
    ...
    '缺失的模块名',
]
```

### 2. 杀毒软件误报

首次运行可能被 Windows Defender 拦截，选择"仍要运行"即可。

### 3. 防火墙提示

首次运行会提示防火墙，选择"允许访问"。

### 4. 端口被占用

如果 15432 端口被占用，程序会报错。需要：
- 关闭占用端口的程序
- 或修改 `app.py` 中的端口号

## 优化建议

### 减小文件大小

1. 使用 UPX 压缩（已在配置中启用）
2. 排除不需要的模块
3. 使用虚拟环境，只安装必要的包

### 添加图标

在 `build-exe.spec` 中修改：
```python
icon='icon.ico',  # 添加你的图标文件路径
```

### 隐藏控制台窗口

如果需要隐藏控制台（不推荐，因为看不到日志），修改：
```python
console=False,
```

## 测试建议

打包完成后，建议在干净的 Windows 系统上测试：
1. 确保没有安装 Python
2. 确保没有安装项目依赖
3. 直接运行 exe，测试所有功能

