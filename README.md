# RegDoc - 文档智能处理系统

RegDoc是一个集成了前端Vue3应用和后端FastAPI服务的文档智能处理系统，专门用于水资源管理相关的文档处理和知识库管理。

## 项目结构

```
RegDoc/
├── frontend/               # Vue3前端应用
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   │   ├── ChatBox.vue
│   │   │   ├── ChatCard.vue
│   │   │   ├── InputBox.vue
│   │   │   ├── MainLayout.vue
│   │   │   └── WaitAnimation.vue
│   │   ├── views/          # Vue页面
│   │   │   ├── KnowledgeEntry.vue
│   │   │   ├── KnowledgeManage.vue
│   │   │   └── MainView.vue
│   │   ├── modules/        # 功能模块
│   │   │   └── water-resource-ai/  # 水资源AI模块
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia状态管理
│   │   └── assets/         # 静态资源
│   ├── public/             # 公共资源
│   ├── docs/               # 前端文档
│   └── package.json        # 前端依赖配置
├── backend/                # FastAPI后端服务
│   ├── app/
│   │   ├── core/           # 核心配置
│   │   ├── models/         # AI模型文件
│   │   ├── routers/        # API路由
│   │   ├── schemas/        # 数据模型
│   │   ├── services/       # 业务服务
│   │   └── storage/        # 文件存储
│   ├── main.py             # 应用入口
│   └── requirements.txt    # Python依赖
├── uploads/                # 上传文件存储
├── knowledge_base/         # 知识库文件
├── file/                   # 处理后的文件
└── logs.log               # 系统日志
```

## 功能特性

### 前端功能
- 📊 知识库管理界面
- 💬 智能聊天对话
- 📁 文件上传和管理
- 🎨 现代化UI设计（基于Element Plus）
- 📱 响应式布局

### 后端功能
- 🚀 高性能FastAPI框架
- 📄 多格式文档处理（PDF、Word、Excel等）
- 🧠 AI模型集成（BGE-M3、BGE-Reranker）
- 🔍 智能文档检索和问答
- 📊 文档分类和数据抽取
- 💾 向量数据库支持（Milvus）

## 快速开始

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 后端开发

```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

## 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios

### 后端
- **框架**: FastAPI
- **数据库**: Milvus (向量数据库)
- **AI模型**: BGE-M3, BGE-Reranker-Large
- **文档处理**: MinerU, PyPDF2, python-docx
- **配置管理**: Pydantic Settings

## API接口

主要API端点：

- `POST /upload/*` - 文件上传
- `POST /knowledge_base/*` - 知识库管理
- `POST /llm_chat/*` - 大模型对话
- `POST /knowledge_base_chat/*` - 知识库问答
- `POST /intelligent_chat/*` - 智能对话
- `POST /review_report/*` - 报告审查
- `POST /extract_data/*` - 数据抽取
- `POST /classify/*` - 文档分类

## 开发指南

### 环境要求
- Node.js 18+
- Python 3.9+
- 足够的存储空间用于AI模型文件

### 配置说明
1. 后端配置在 `backend/app/core/config.py`
2. 前端配置在 `vite.config.ts`
3. 确保AI模型文件正确放置在 `backend/app/models/` 目录

### 部署说明
1. 前端构建: `cd frontend && npm run build`
2. 后端启动: `cd backend && python main.py`
3. 确保端口8443可访问

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用私有许可证。
- **Element Plus**: 企业级UI组件库
- **Vue Router**: 单页应用路由管理
- **Pinia**: 现代状态管理库
- **Sass**: CSS预处理器

#### 开发工具
- **Vite**: 快速的构建工具和开发服务器
- **ESLint**: 代码质量检查
- **Vue DevTools**: Vue.js开发调试工具

## 📁 项目结构

```
src/
├── components/          # 公共组件
│   ├── icons/          # 图标组件
│   ├── AppLayout.vue   # 应用布局组件
│   ├── ChatBox.vue     # 聊天消息组件
│   ├── ChatCard.vue    # 聊天会话卡片
│   ├── InputBox.vue    # 消息输入组件
│   ├── WaitAnimation.vue # 加载动画
│   ├── HelloWorld.vue  # 欢迎组件
│   ├── TheWelcome.vue  # 欢迎页面
│   └── WelcomeItem.vue # 欢迎项组件
├── views/              # 页面组件
│   ├── MainView.vue    # 主对话页面
│   ├── HomeView.vue    # 欢迎首页
│   ├── AboutView.vue   # 关于页面
│   ├── KnowledgeEntry.vue # 知识入库页面
│   └── KnowledgeManage.vue # 知识管理页面
├── router/             # 路由配置
├── stores/             # 状态管理
│   └── counter.ts      # 应用状态store
├── assets/             # 静态资源
└── main.ts             # 应用入口
```

## 🛠️ 开发指南

### 环境要求
- Node.js >= 18.0.0
- npm >= 8.0.0

### 安装依赖
```bash
npm install
```

### 开发运行
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 类型检查
```bash
npm run type-check
```

### 代码检查
```bash
npm run lint
```

## 🌟 页面导航

### 主要页面
- **/** - 智能对话主页面
- **/welcome** - 系统欢迎页面
- **/about** - 关于系统信息
- **/knowledge-entry** - 知识文档入库
- **/knowledge-manage** - 知识库管理

### 功能模块

#### 智能对话 (/)
- 支持多轮对话交互
- 历史会话管理
- 会话主题编辑
- 消息搜索和筛选

#### 知识入库 (/knowledge-entry)
- 文档上传和解析
- 知识库选择
- 相似文档检测
- 批量入库操作

#### 知识管理 (/knowledge-manage)
- 知识库浏览
- 文档搜索和筛选
- 文档编辑和删除
- 知识库统计

## 🎨 UI/UX 特性

### 现代化设计
- 响应式布局适配各种屏幕尺寸
- 简洁优雅的界面设计
- 一致的视觉语言
- 流畅的交互动画

### 用户体验
- 直观的导航结构
- 快速的页面加载
- 智能的操作提示
- 无障碍访问支持

## 📊 集成功能

本项目整合了以下功能模块：

1. **原ShuiKeYuan项目功能**:
   - 聊天对话系统
   - 消息组件库
   - 用户界面布局

2. **water-resource-ai项目功能**:
   - 欢迎页面和图标库
   - 系统导航结构
   - 知识管理界面

3. **新增集成功能**:
   - 统一的应用布局
   - 完整的路由导航
   - 状态管理集成
   - 响应式设计优化

## 🔧 配置说明

### 开发配置
- Vite配置: `vite.config.ts`
- TypeScript配置: `tsconfig.json`
- ESLint配置: `eslint.config.ts`

### 环境变量
支持通过`.env`文件配置环境变量

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 📝 更新日志

### v1.0.0 (2025-01-26)
- 完成项目整合
- 集成智能对话功能
- 添加知识管理模块
- 实现响应式布局设计
- 完善TypeScript类型支持

## 📞 支持

如有问题或建议，请联系开发团队。
