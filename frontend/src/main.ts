import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/preview.css"
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册组件
app.component("MdPreview", MdPreview)

// 使用插件
app.use(ElementPlus)
app.use(createPinia())
app.use(router)

app.mount('#app')
