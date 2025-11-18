# macOS 应用打包指南

## 前置要求

1. **macOS 系统**（macOS 10.13+）
2. **Python 3.11+** 已安装
3. **所有依赖已安装**

## 打包步骤

### 1. 安装依赖

```bash
# 安装项目依赖
pip3 install -r requirements.txt

# 安装打包工具
pip3 install -r scripts/requirements-build.txt
```

### 2. 执行打包

**方式一：使用脚本（推荐）**
```bash
bash scripts/build-mac.sh
```

**方式二：手动执行**
```bash
python3 -m PyInstaller scripts/build-mac.spec
```

### 3. 获取应用

打包完成后，应用位于：
```
dist/naspt.app
```

## 使用打包后的应用

### 方式一：直接运行
```bash
open dist/naspt.app
```

### 方式二：双击运行
在 Finder 中找到 `dist/naspt.app`，双击运行。

### 方式三：命令行运行
```bash
dist/naspt.app/Contents/MacOS/naspt
```

## 应用特点

- **单文件应用包**：`naspt.app` 是一个应用包（.app bundle）
- **自动打开浏览器**：运行后会自动打开浏览器访问 http://localhost:15432
- **控制台输出**：可以通过终端查看日志

## 常见问题

### 1. "无法打开，因为来自身份不明的开发者"

**解决方法：**
1. 右键点击 `naspt.app`
2. 选择"打开"
3. 在弹出的对话框中点击"打开"

或者：
```bash
# 移除隔离属性
xattr -cr dist/naspt.app
```

### 2. 防火墙提示

首次运行会提示防火墙，选择"允许"。

### 3. 端口被占用

如果 15432 端口被占用，程序会报错。需要：
- 关闭占用端口的程序
- 或修改 `app.py` 中的端口号

## 文件大小

预计打包后的应用大小：**80-150MB**

## 分发应用

可以将 `naspt.app` 复制给其他 macOS 用户使用，无需安装 Python 或任何依赖。

## 添加图标

如果需要自定义图标：

1. 准备图标文件 `icon.icns`（macOS 图标格式）
2. 在 `scripts/build-mac.spec` 中修改：
```python
icon='icon.icns',  # 图标文件路径
```

## 代码签名（可选）

如果需要代码签名（避免"身份不明的开发者"警告）：

```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/naspt.app
```

## 创建 DMG 安装包（可选）

如果需要创建 DMG 安装包：

```bash
# 安装 create-dmg（如果未安装）
brew install create-dmg

# 创建 DMG
create-dmg dist/naspt.app dist/
```

