# RegDoc 部署指南

## 系统要求

### 硬件要求
- CPU: 推荐8核心以上
- 内存: 推荐16GB以上
- 存储: 推荐100GB以上可用空间
- GPU: 可选，用于加速AI模型推理

### 软件要求
- Windows 10/11 或 Linux
- Node.js 18.0+
- Python 3.9+
- Git

## 安装步骤

### 1. 环境准备

#### Node.js安装
```bash
# 从官网下载并安装 Node.js 18+
# https://nodejs.org/

# 验证安装
node --version
npm --version
```

#### Python环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 项目部署

#### 克隆项目
```bash
git clone <repository-url>
cd RegDoc
```

#### 前端部署
```bash
# 安装依赖
npm install

# 构建生产版本
npm run build

# 部署到Web服务器
# 将dist目录部署到Nginx或其他Web服务器
```

#### 后端部署
```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库连接等

# 启动服务
python main.py
```

## 配置说明

### 前端配置

#### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/RegDoc/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 后端配置

#### 环境变量(.env)
```env
# 应用配置
APP_NAME=RegDoc
APP_VERSION=1.0.0
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8443

# 数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# AI模型配置
MODEL_PATH=./app/models
```

#### 系统服务配置(systemd)
```ini
[Unit]
Description=RegDoc Backend Service
After=network.target

[Service]
Type=simple
User=regdoc
WorkingDirectory=/path/to/RegDoc/backend
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 数据库设置

### Milvus数据库
```bash
# 使用Docker安装Milvus
docker pull milvusdb/milvus:latest
docker run -d --name milvus_cpu \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

## 监控和日志

### 日志配置
- 前端日志: 浏览器控制台
- 后端日志: `logs.log` 文件
- 系统日志: `/var/log/regdoc/`

### 监控指标
- API响应时间
- 内存使用情况
- 磁盘空间使用
- AI模型推理性能

## 备份策略

### 数据备份
```bash
# 备份知识库
tar -czf knowledge_base_backup_$(date +%Y%m%d).tar.gz knowledge_base/

# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# 备份数据库
# Milvus备份方案
```

### 配置备份
```bash
# 备份配置文件
cp backend/.env backend/.env.backup
cp nginx.conf nginx.conf.backup
```

## 故障排除

### 常见问题

#### 前端无法访问后端
1. 检查后端服务是否启动
2. 检查端口是否被占用
3. 检查防火墙设置
4. 检查CORS配置

#### AI模型加载失败
1. 检查模型文件是否完整
2. 检查内存是否足够
3. 检查模型路径配置
4. 查看详细错误日志

#### 文件上传失败
1. 检查上传目录权限
2. 检查磁盘空间
3. 检查文件大小限制
4. 检查文件格式支持

### 日志查看
```bash
# 查看后端日志
tail -f logs.log

# 查看系统服务日志
journalctl -u regdoc -f

# 查看Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## 安全配置

### HTTPS配置
1. 获取SSL证书
2. 配置Nginx HTTPS
3. 强制HTTPS重定向

### 防火墙配置
```bash
# 开放必要端口
ufw allow 80
ufw allow 443
ufw allow 8443
```

### 定期更新
1. 定期更新依赖包
2. 监控安全漏洞
3. 备份重要数据

## 性能优化

### 前端优化
1. 启用Gzip压缩
2. 使用CDN加速
3. 优化图片资源
4. 启用浏览器缓存

### 后端优化
1. 配置数据库连接池
2. 启用API缓存
3. 优化AI模型推理
4. 使用负载均衡

## 联系支持

如有问题，请联系技术支持：
- 邮箱: support@regdoc.com
- 电话: +86-xxx-xxxx-xxxx
