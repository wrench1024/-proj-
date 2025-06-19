<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="title">水资源论证智能审查AI助手</div>
      <div class="user-info">
        <span>用户</span>
        <button class="logout-btn">退出</button>
      </div>
    </header>

    <!-- 侧边导航栏 -->
    <aside class="side-nav">
      <nav>
        <div class="nav-item">系统设置</div>
        <router-link to="/knowledge-entry" custom v-slot="{ navigate, isActive }">
          <div 
            class="nav-item" 
            :class="{ active: isActive }"
            @click="navigate"
          >
            知识入库
          </div>
        </router-link>
        <div class="nav-item">审查管理</div>
        <router-link to="/knowledge-manage" custom v-slot="{ navigate, isActive }">
          <div 
            class="nav-item"
            :class="{ active: isActive }"
            @click="navigate"
          >
            知识库管理
          </div>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// 导航功能已通过router-link实现
</script>

<style scoped>
.main-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 60px 1fr;
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  background-color: #ffffff;
}

.top-nav {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.top-nav .title {
  font-size: 18px;
  font-weight: bold;
  color: white;
}

.top-nav .user-info {
  display: flex;
  align-items: center;
  gap: 15px;
  color: white;
}

.logout-btn {
  padding: 5px 10px;
  background: rgba(255,255,255,0.2);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.side-nav {
  grid-row: 2;
  background: linear-gradient(135deg, #2c3e50 0%, #1a1a2e 100%);
  padding: 15px 0;
}

.nav-item {
  padding: 12px 20px;
  cursor: pointer;
  color: #e0e0e0;
  transition: all 0.3s;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255,255,255,0.1);
  color: white;
}

.content {
  grid-row: 2;
  padding: 10px;
  overflow: hidden;
  height: calc(100vh - 60px);
  background-color: #ffffff;
  --compact-spacing: 10px;
}
</style>
