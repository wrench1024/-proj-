# RegDoc Frontend

RegDoc前端应用，基于Vue 3 + TypeScript + Element Plus开发的文档智能处理系统前端界面。

## 技术栈

- **Vue 3** - 现代响应式前端框架
- **TypeScript** - 类型安全的JavaScript超集
- **Element Plus** - 基于Vue 3的组件库
- **Vite** - 快速构建工具
- **Pinia** - Vue 3状态管理
- **Vue Router 4** - 路由管理
- **Axios** - HTTP客户端
- **MD Editor V3** - Markdown编辑器

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── ChatBox.vue     # 聊天对话框
│   │   ├── ChatCard.vue    # 聊天卡片
│   │   ├── InputBox.vue    # 输入框组件
│   │   ├── MainLayout.vue  # 主布局组件
│   │   └── WaitAnimation.vue # 等待动画
│   ├── views/              # 页面组件
│   │   ├── KnowledgeEntry.vue   # 知识录入页面
│   │   ├── KnowledgeManage.vue  # 知识管理页面
│   │   └── MainView.vue         # 主页面
│   ├── modules/            # 功能模块
│   │   └── water-resource-ai/   # 水资源AI模块
│   ├── router/             # 路由配置
│   ├── stores/             # 状态管理
│   ├── assets/             # 静态资源
│   └── App.vue             # 根组件
├── public/                 # 公共资源
├── docs/                   # 文档
├── dist/                   # 构建输出
└── package.json           # 依赖配置
```

## 快速开始

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产版本
```bash
npm run preview
```

### 代码检查
```bash
npm run lint
```

## 功能模块

### 主要功能
1. **智能对话** - 与AI助手进行实时对话
2. **知识管理** - 文档上传、分类、搜索
3. **文档处理** - 多格式文档解析和处理
4. **审查管理** - 文档审查流程管理

### 集成模块
- **water-resource-ai**: 水资源专业AI功能模块

## 配置说明

### API配置
在开发环境中，API请求会代理到后端服务：
- 后端地址: `http://10.21.22.107:8443`
- API路径: `/api/*`

### 环境变量
可以通过`.env`文件配置环境变量：
```env
VITE_API_BASE_URL=http://10.21.22.107:8443
VITE_APP_TITLE=RegDoc
```

## 开发指南

### 组件开发
- 使用Vue 3 Composition API
- 遵循TypeScript类型约束
- 使用Element Plus组件库
- 保持组件的可复用性

### 状态管理
使用Pinia进行状态管理：
```typescript
import { defineStore } from 'pinia'

export const useMainStore = defineStore('main', {
  state: () => ({
    // 状态定义
  }),
  actions: {
    // 操作方法
  }
})
```

### 路由配置
在`src/router/index.ts`中配置路由：
```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 路由配置
  ]
})
```

## 部署说明

### 构建
```bash
npm run build
```

### 部署到Nginx
将`dist`目录内容部署到Nginx服务器，并配置反向代理：
```nginx
location /api {
    proxy_pass http://10.21.22.107:8443;
}
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 许可证

私有项目许可证
