import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import KnowledgeEntry from '../views/KnowledgeEntry.vue'
import KnowledgeManage from '../views/KnowledgeManage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          redirect: '/knowledge-entry',
        },
        {
          path: 'knowledge-entry',
          name: 'knowledge-entry',
          component: KnowledgeEntry,
        },
        {
          path: 'knowledge-manage',
          name: 'knowledge-manage',
          component: KnowledgeManage,
        }
      ]
    },

  ],
})

export default router
