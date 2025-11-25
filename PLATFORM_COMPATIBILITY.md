# 平台兼容性说明

本项目支持 Windows、Linux 和 macOS 平台。本文档说明各平台的兼容性情况和注意事项。

## ✅ 已测试平台

- ✅ Windows 10/11
- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (Ubuntu 20.04+)

## 🔧 平台特定功能

### 1. 进程管理

#### Windows
- 使用 `netstat` 和 `taskkill` 命令
- 使用 `subprocess.CREATE_NO_WINDOW` 标志隐藏控制台窗口

#### macOS/Linux
- 使用 `lsof` 和 `kill` 命令
- 自动检测 `lsof` 命令是否可用
- 优先尝试优雅终止进程，失败后强制终止

### 2. 进程输出读取

#### Windows
- 使用 `readline()` 方法读取进程输出
- 支持 UTF-8 和 GBK 编码自动检测

#### macOS/Linux
- 优先使用 `select.select()` 进行非阻塞读取
- 如果 `select` 模块不可用，回退到 `readline()` 方法
- 仅使用 UTF-8 编码

### 3. 路径处理

- ✅ 使用 `pathlib.Path` 进行跨平台路径处理
- ✅ 使用 `os.path.join()` 构建路径
- ✅ 所有路径分隔符使用 Python 标准库自动处理

### 4. 编码处理

#### Windows
- 默认使用 UTF-8
- 如果 UTF-8 解码失败，尝试 GBK 编码
- 设置 `PYTHONIOENCODING=utf-8` 和 `PYTHONUTF8=1`

#### macOS/Linux
- 仅使用 UTF-8 编码
- 设置 `LANG=en_US.UTF-8` 和 `LC_ALL=en_US.UTF-8`

## 📋 平台特定要求

### macOS

1. **必需工具**
   - `lsof` - 通常已预装，用于端口管理
   - `kill` - 系统命令，用于进程终止

2. **Python 环境**
   - Python 3.9+
   - 建议使用 conda 或 venv 创建虚拟环境

3. **权限**
   - 某些操作可能需要管理员权限（如清理系统端口占用）

### Linux

1. **必需工具**
   - `lsof` - 可能需要安装：`sudo apt-get install lsof` (Ubuntu/Debian)
   - `kill` - 系统命令，通常已预装

2. **Python 环境**
   - Python 3.9+
   - 建议使用系统包管理器或虚拟环境

### Windows

1. **必需工具**
   - `netstat` - Windows 内置命令
   - `taskkill` - Windows 内置命令

2. **Python 环境**
   - Python 3.9+
   - 建议使用 conda 或 venv

## 🚀 启动脚本

### Windows
```bash
start_app.bat              # 普通启动
start_app_auto_reload.bat  # 自动重载启动（开发环境）
restart_app.bat            # 重启应用
```

### macOS/Linux
```bash
chmod +x start_app.sh      # 首次使用需要添加执行权限
./start_app.sh             # 启动应用
```

## ⚠️ 已知问题和限制

### macOS 特定

1. **lsof 命令**
   - macOS 通常预装 `lsof`，如果不可用，启动脚本会跳过端口清理
   - 如果遇到端口占用问题，可以手动执行：
     ```bash
     lsof -ti :5000 | xargs kill -9
     ```

2. **权限问题**
   - 某些系统端口可能需要管理员权限才能清理
   - 如果遇到权限问题，使用 `sudo`：
     ```bash
     sudo lsof -ti :5000 | xargs kill -9
     ```

3. **select 模块**
   - Python 3.4+ 标准库包含 `select` 模块
   - 如果不可用，代码会自动回退到 `readline()` 方法

### Linux 特定

1. **lsof 安装**
   - Ubuntu/Debian: `sudo apt-get install lsof`
   - CentOS/RHEL: `sudo yum install lsof`
   - Arch: `sudo pacman -S lsof`

2. **权限**
   - 清理端口占用可能需要 root 权限
   - 建议使用 `sudo` 或配置适当的用户权限

## 🔍 故障排查

### 端口占用问题

**Windows:**
```bash
netstat -ano | findstr ":5000"
taskkill /F /PID <进程ID>
```

**macOS/Linux:**
```bash
lsof -i :5000
kill -9 <进程ID>
```

### 编码问题

如果遇到编码错误，检查环境变量：
```bash
# macOS/Linux
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Windows (PowerShell)
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
```

### 进程输出读取问题

如果进程输出无法正常显示：
1. 检查 `select` 模块是否可用：`python -c "import select; print('OK')"`
2. 检查 Python 版本（需要 3.9+）
3. 查看日志文件：`logs/<app_name>.log`

## 📝 开发建议

1. **路径处理**
   - 始终使用 `pathlib.Path` 或 `os.path.join()`
   - 避免硬编码路径分隔符（`/` 或 `\`）

2. **平台检测**
   - 使用 `platform.system()` 检测操作系统
   - 使用 `sys.platform` 检测平台类型

3. **编码处理**
   - 统一使用 UTF-8 编码
   - Windows 上可以添加 GBK 作为备选

4. **进程管理**
   - 使用 `subprocess` 模块的标准方法
   - 避免使用平台特定的命令（除非必要）

## 🔄 更新日志

- 2025-11-26: 添加 macOS 兼容性支持
- 2025-11-26: 改进进程管理和端口清理逻辑
- 2025-11-26: 添加跨平台编码处理

