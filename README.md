20260119修复同一局域网下ipv6的问题，新增了一个web页面，供游客查询播放情况，及管理员简单配置


# Emby IPLimit 项目

## 项目简介

Emby IPLimit 是一个专门用于监控和限制 Emby 媒体服务器用户访问行为的工具。它能够实时监控用户的播放会话，检测异常登录行为（如同一用户在多个不同IP地址同时播放），并在达到阈值时自动禁用用户账号，提供完整的安全防护和访问控制功能。

## 主要功能

- 🔍 **实时会话监控** - 监控 Emby 用户的播放会话状态
- 🌐 **IP 地理位置查询** - 自动获取用户 IP 地址的地理位置信息
- 🚨 **异常行为检测** - 检测同一用户在不同 IP 地址的并发播放行为
- 🛡️ **自动安全防护** - 达到阈值时自动禁用问题用户
- 📊 **会话记录存储** - 将播放会话记录到本地 SQLite 数据库
- 🔔 **Webhook 通知** - 支持自定义格式的 Webhook 通知
- ⚪ **白名单管理** - 白名单内用户不会被禁用
- 📝 **详细日志** - 完整的操作日志和监控记录

## 技术特性

- **支持 IPv4 和 IPv6** - 完整支持双栈网络环境
- **灵活配置** - 可自定义监控间隔、告警阈值等参数
- **高兼容性** - 支持各种 Webhook 服务（钉钉、企业微信、飞书等）
- **轻量级** - 仅依赖 `requests` 和 `pyyaml` 两个库
- **Docker 支持** - 提供完整的 Docker 部署方案

## 安装部署

### 方式一：Docker 部署（推荐）

#### 1. 拉取镜像
```bash
docker pull pdzhou/emby-iplimit:latest
```

#### 2. 创建数据目录
```bash
mkdir -p /path/to/emby-iplimit/data
```

#### 3. 启动容器
```bash
docker run -d \
  --name emby-iplimit \
  -v /path/to/emby-iplimit/data:/app/data \
  -e TZ=Asia/Shanghai \
  pdzhou/emby-iplimit:latest
```

#### 4. 配置服务
首次启动后，程序会在 `/path/to/emby-iplimit/data` 目录下生成默认配置文件 `config.yaml`，容器会自动停止。

编辑配置文件：
```bash
vim /path/to/emby-iplimit/data/config.yaml
```

重启容器：
```bash
docker restart emby-iplimit
```

### 方式二：本地部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd Emby-IPLimit-main
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 复制配置模板
```bash
cp scripts/default_config.yaml data/config.yaml
```

#### 4. 编辑配置
```bash
vim data/config.yaml
```

#### 5. 运行服务
```bash
python scripts/main.py
```

## 配置说明

### 完整配置示例

```yaml
database:
  name: emby_playback.db

emby:
  server_url: https://emby.example.com
  api_key: your_api_key_here
  check_interval: 10

notifications:
  alert_threshold: 2
  enable_alerts: true

security:
  auto_disable: true
  whitelist:
    - admin
    - user1
    - user2

webhook:
  enabled: true
  url: https://your-webhook-url.com
  timeout: 10
  retry_attempts: 3
  body:
    title: "Emby安全告警"
    content: "用户 {username} 在 {location} 使用 {ip_address} 登录异常"
```

### 配置参数详解

#### 数据库配置 (database)
- `name`: SQLite 数据库文件名，默认 `emby_playback.db`

#### Emby 配置 (emby)
- `server_url`: Emby 服务器地址（必须包含协议）
- `api_key`: Emby API 密钥
- `check_interval`: 监控检查间隔（秒），默认 10 秒

#### 告警配置 (notifications)
- `alert_threshold`: 告警阈值，达到不同 IP 数量时触发禁用
- `enable_alerts`: 是否启用异常告警，不启用的话仅记录而不会触发禁用

#### 安全配置 (security)
- `auto_disable`: 是否自动禁用异常用户
- `whitelist`: 白名单用户名列表（不会被禁用）

#### Webhook 通知配置 (webhook)
- `enabled`: 是否启用 Webhook 通知
- `url`: Webhook 通知地址
- `timeout`: 请求超时时间（秒）
- `retry_attempts`: 请求重试次数
- `body`: 自定义请求体配置，支持模板变量

### Webhook 配置示例

#### 基础配置
```yaml
webhook:
  enabled: true
  url: "https://your-webhook-url.com/api/notify"
  body:
    route_id: "your-route-id"
    title: "Emby安全告警"
    content: "用户 {username} 在 {location} 登录异常"
```

#### 钉钉机器人配置
```yaml
webhook:
  enabled: true
  url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
  body:
    msgtype: "markdown"
    markdown:
      title: "Emby安全告警"
      text: "用户 {username} 在 {location} 使用 {ip_address} 登录异常"
    at:
      isAtAll: false
```

#### 企业微信配置
```yaml
webhook:
  enabled: true
  url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
  body:
    msgtype: "text"
    text:
      content: "Emby告警：{username} 在 {location} 使用 {ip_address} 登录异常"
      mentioned_list: ["@all"]
```

#### 飞书配置
```yaml
webhook:
  enabled: true
  url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
  body:
    msg_type: "interactive"
    card:
      elements:
        - tag: "div"
          text:
            content: "🔔 {title}\n\n用户：{username}\nIP：{ip_address}\n位置：{location}"
            tag: "lark_md"
      header:
        title:
          content: "{title}"
          tag: "plain_text"
```

### 可用的模板变量

在 `body` 配置中可以使用以下模板变量：

- `{username}` - 用户名
- `{user_id}` - 用户ID
- `{ip_address}` - IP地址
- `{ip_type}` - IP类型（IPv4/IPv6）
- `{location}` - 地理位置
- `{session_count}` - 并发会话数
- `{reason}` - 告警原因
- `{device}` - 设备名称
- `{client}` - 客户端名称
- `{timestamp}` - 时间戳

## 使用指南

### 首次部署

1. **获取 Emby API 密钥**
   - 登录 Emby 管理后台
   - 进入 "控制台" → "高级" → "API 密钥"
   - 创建新的 API 密钥

2. **配置网络访问**
   - 确保 Emby IPLimit 服务器能访问 Emby 服务器
   - 检查防火墙和网络配置

3. **测试连接**
   - 启动服务后检查日志输出
   - 确认能正常获取用户会话信息

### 日常维护

#### 查看监控日志
```bash
# Docker 部署
docker logs -f emby-iplimit

# 本地部署
tail -f data/emby_playback.log
```

#### 手动启用/禁用用户
```bash
# 进入 Emby 容器（如果使用 Docker）
docker exec -it emby-iplimit python

# 或者直接修改数据库或使用 Emby API
```

#### 清理历史数据
```bash
# 备份数据库
cp data/emby_playback.db data/emby_playback.db.backup

# 清理过期数据（根据需要手动修改脚本）
```

## 故障排除

### 常见问题

1. **无法连接到 Emby 服务器**
   - 检查 `server_url` 配置是否正确
   - 验证 API 密钥是否有效
   - 确认网络连通性

2. **Webhook 通知失败**
   - 检查 `url` 地址是否正确
   - 验证 `body` 配置格式
   - 查看网络和防火墙设置

3. **IP地址显示异常**
   - 检查 Emby 客户端的网络配置
   - 确认代理和负载均衡器设置

4. **白名单不生效**
   - 确认用户名大小写匹配
   - 检查配置文件中是否有空格

### 日志级别

项目支持以下日志级别：
- `INFO` - 一般信息记录
- `WARNING` - 警告信息
- `ERROR` - 错误信息

可以通过修改代码中的日志配置来调整输出级别。

## 开发信息

### 项目结构
```
Emby-IPLimit-main/
├── scripts/                  # Python 脚本
│   ├── main.py              # 主程序入口
│   ├── config_loader.py     # 配置加载器
│   ├── database.py          # 数据库管理
│   ├── emby_client.py       # Emby API 客户端
│   ├── monitor.py           # 监控核心
│   ├── security.py          # 安全操作
│   └── webhook_notifier.py  # Webhook 通知器
├── data/                    # 数据目录
│   └── config.yaml          # 配置文件
├── tests/                   # 测试文件（可选）
├── Dockerfile              # Docker 构建文件
├── requirements.txt        # Python 依赖
└── README.md              # 项目文档
```

### 核心模块

- **main.py** - 程序入口，负责初始化和启动服务
- **monitor.py** - 核心监控逻辑，处理会话检测和异常分析
- **emby_client.py** - Emby API 封装，提供用户和会话信息获取
- **security.py** - 安全操作封装，处理用户禁用/启用
- **webhook_notifier.py** - 通知系统，支持多种 Webhook 格式
- **database.py** - SQLite 数据库管理，存储会话记录
- **config_loader.py** - 配置文件加载和验证

### 技术栈

- **语言**: Python 3.9+
- **HTTP 客户端**: requests
- **配置解析**: PyYAML
- **数据库**: SQLite3
- **容器化**: Docker
- **网络**: IPv4/IPv6 双栈支持

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd Emby-IPLimit-main

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/
```

### 提交规范
- 遵循 PEP 8 代码规范
- 添加必要的注释和文档
- 确保新增功能有对应的测试用例
- 更新 README.md 相关内容

## 许可证

本项目采用 MIT 许可证，详情请查看 LICENSE 文件。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本会话监控
- 实现异常检测和自动禁用
- 添加 Webhook 通知功能
- 提供 Docker 部署支持

---

**注意**: 请确保在使用前仔细阅读配置说明，并根据实际环境调整相关参数。定期备份数据库和配置文件。
