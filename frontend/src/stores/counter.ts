import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})

// 聊天会话管理
export const useChatStore = defineStore('chat', () => {
  const currentSession = ref<any>(null)
  const sessions = ref<any[]>([])
  
  function setCurrentSession(session: any) {
    currentSession.value = session
  }
  
  function addSession(session: any) {
    sessions.value.push(session)
  }
  
  return {
    currentSession,
    sessions,
    setCurrentSession,
    addSession
  }
})

// 知识库管理
export const useKnowledgeStore = defineStore('knowledge', () => {
  const knowledgeBases = ref<string[]>([
    '贵州省行政区划',
    '水资源论证技术要求',
    '建设项目管理办法'
  ])
  
  const documents = ref<any[]>([])
  
  function addDocument(doc: any) {
    documents.value.push(doc)
  }
  
  function removeDocument(id: string) {
    const index = documents.value.findIndex(doc => doc.id === id)
    if (index > -1) {
      documents.value.splice(index, 1)
    }
  }
  
  return {
    knowledgeBases,
    documents,
    addDocument,
    removeDocument
  }
})
