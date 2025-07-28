import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import MainView from '../views/MainView.vue'
import HomeView from '../views/HomeView.vue'
import AboutView from '../views/AboutView.vue'
import KnowledgeEntry from '../views/KnowledgeEntry.vue'
import KnowledgeManage from '../views/KnowledgeManage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: MainView
        },
        {
          path: 'welcome',
          name: 'welcome',
          component: HomeView
        },
        {
          path: 'about',
          name: 'about',
          component: AboutView
        },
        {
          path: 'knowledge-entry',
          name: 'knowledge-entry',  
          component: KnowledgeEntry
        },
        {
          path: 'knowledge-manage',
          name: 'knowledge-manage',
          component: KnowledgeManage
        }
      ]
    }
  ]
})

export default router
