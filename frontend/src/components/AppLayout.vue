<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <h1 class="header-title">水资源论证智能审查AI助手</h1>
      <div class="header-actions">
        <el-button type="primary" @click="goToSettings">系统设置</el-button>
        <span class="user-info">用户名：管理员</span>
        <el-button type="text" @click="logout">退出</el-button>
      </div>
    </el-header>

    <el-container class="main-container">
      <!-- 左侧导航栏 -->
      <el-aside class="app-sidebar" width="200px">
        <el-menu
          :default-active="activeRoute"
          class="sidebar-menu"
          @select="handleMenuSelect"
          background-color="#f5f5f5"
          text-color="#333"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能对话</span>
          </el-menu-item>
          
          <el-sub-menu index="knowledge">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>知识管理</span>
            </template>
            <el-menu-item index="/knowledge-entry">
              <el-icon><Upload /></el-icon>
              <span>知识入库</span>
            </el-menu-item>
            <el-menu-item index="/knowledge-manage">
              <el-icon><Management /></el-icon>
              <span>知识管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  ChatDotRound, 
  Document, 
  Upload, 
  Management
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeRoute = computed(() => route.path)

const handleMenuSelect = (key: string) => {
  router.push(key)
}

const goToSettings = () => {
  console.log('跳转到系统设置')
}

const logout = () => {
  console.log('用户退出')
}
</script>

<style lang="scss" scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow: hidden;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  height: 60px !important;
  flex-shrink: 0;
  z-index: 1000;

  .header-title {
    font-size: 20px;
    font-weight: 600;
    margin: 0;
    white-space: nowrap;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    flex-shrink: 0;

    .user-info {
      color: rgba(255, 255, 255, 0.9);
      white-space: nowrap;
      font-size: 14px;
    }

    .el-button--text {
      color: rgba(255, 255, 255, 0.8);
      
      &:hover {
        color: white;
      }
    }
  }

  // 响应式处理
  @media (max-width: 768px) {
    padding: 0 10px;
    height: 50px !important;
    
    .header-title {
      font-size: 14px;
    }
    
    .header-actions {
      gap: 8px;
      
      .user-info {
        display: none; // 小屏幕隐藏用户信息
      }
      
      .el-button {
        padding: 5px 8px;
        font-size: 12px;
      }
    }
  }
}

.main-container {
  flex: 1;
  height: calc(100vh - 60px);
  overflow: hidden;
  display: flex;

  @media (max-width: 768px) {
    height: calc(100vh - 50px);
    flex-direction: column;
  }
}

.app-sidebar {
  background-color: #f5f5f5;
  border-right: 1px solid #e6e6e6;
  flex-shrink: 0;
  overflow: hidden;

  .sidebar-menu {
    border: none;
    height: 100%;
    overflow-y: auto;

    .el-menu-item, .el-sub-menu__title {
      height: 48px;
      line-height: 48px;
      
      &:hover {
        background-color: #e6f7ff;
      }
    }

    .el-menu-item.is-active {
      background-color: #e6f7ff;
      color: #409EFF;
      font-weight: 600;
    }

    .el-sub-menu .el-menu-item {
      height: 40px;
      line-height: 40px;
      padding-left: 50px !important;
    }
  }

  // 响应式处理
  @media (max-width: 768px) {
    width: 100% !important;
    height: 60px;
    border-right: none;
    border-bottom: 1px solid #e6e6e6;
    flex-shrink: 0;
    
    .sidebar-menu {
      height: 60px;
      display: flex;
      flex-direction: row;
      overflow-x: auto;
      overflow-y: hidden;
      
      .el-menu-item, .el-sub-menu {
        height: 60px;
        line-height: 60px;
        font-size: 12px;
        min-width: 80px;
        flex-shrink: 0;
        text-align: center;
      }
      
      .el-sub-menu .el-menu {
        position: absolute;
        top: 60px;
        left: 0;
        width: 100vw;
        background: white;
        border: 1px solid #e6e6e6;
        z-index: 1000;
      }
    }
  }

  @media (min-width: 769px) {
    width: 200px;
  }
}

.app-main {
  background-color: #f5f5f5;
  padding: 0;
  overflow: auto;
  flex: 1;
  height: 100%;

  @media (max-width: 768px) {
    height: calc(100vh - 50px - 60px); // 减去header和sidebar高度
    overflow: auto;
  }
}
</style>
