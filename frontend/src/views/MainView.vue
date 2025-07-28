<template>
  <el-container class="main-entry">
    
    
    <!-- 主体内容区域 -->
    <el-container class="chat-panel">
      <!-- 左侧历史对话面板 -->
      <el-aside class="session-panel">
        <div class="title">历史对话</div>
        <div class="session-list">
          <div class="session" v-for="session in ChatSessionList" :key="session.id">
            <ChatCard 
              :active="session.active"
              :id="session.id" 
              :chattopic="session.chattopic" 
              :chatnum="session.chatnum" 
              :chattime="session.chattime"
              @clickSession="SwitchSessions" 
            />
          </div>
        </div>
        <div class="button-wrapper">
          <el-button type="primary" class="new-session" @click="createNewSession">
            <el-icon style="margin-right: 8px;"><CirclePlus /></el-icon>
            新的聊天
          </el-button>
        </div>
      </el-aside>
      
      <!-- 右侧聊天内容面板 -->
      <el-main class="message-panel">
        <!-- 消息列表 -->
        <div class="message-list">
          <div class="chatBox" v-for="(msg, index) in currentSession?.chatHistory || []" :key="`history-${index}`">
            <ChatBox 
              :role="msg.role" 
              :content="msg.content" 
            />
          </div>
          <div class="chatBox" v-for="(msg, index) in messages" :key="`new-${index}`">
            <ChatBox 
              :role="msg.role"
              :content="msg.content" 
            />
          </div>
        </div>
        
        <!-- 输入框 -->
        <div class="inputBox">
          <InputBox @send="handleMessageSend" />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { CirclePlus } from "@element-plus/icons-vue";
import ChatCard from "../components/ChatCard.vue";
import ChatBox from "../components/ChatBox.vue";
import InputBox from "../components/InputBox.vue";

// 界面控制的全局状态
const currentChatSessionId = ref<number>(1);

// 当前选中的会话
const currentSession = ref<{
  id: number;
  active: boolean;
  chattopic: string;
  chatnum: number;
  chattime: string;
  chatHistory: { role: string; content: string }[];
} | null>(null);

// 会话列表
const ChatSessionList = ref([
  {
    id: 1,
    active: true,
    chattopic: '贵州省行政区划',
    chatnum: 4,
    chattime: '2025-06-18 10:47',
    chatHistory: [
      { role: 'user', content: '贵州省有哪些地级市？' },
      { role: 'assistant', content: '贵州省有贵阳市、遵义市、六盘水市等地级市。' }
    ]
  },
  {
    id: 2,
    active: false,
    chattopic: '河北',
    chatnum: 6,
    chattime: '2025-06-18 10:47',
    chatHistory: [
      { role: 'user', content: '河北的省会是哪里？' },
      { role: 'assistant', content: '河北的省会是石家庄。' }
    ]
  },
  {
    id: 3,
    active: false,
    chattopic: '北京',
    chatnum: 5,
    chattime: '2025-06-18 10:47',
    chatHistory: [
      { role: 'user', content: '北京有哪些著名景点？' },
      { role: 'assistant', content: '北京有故宫、长城、颐和园等著名景点。' }
    ]
  }
]);

// 设置初始选中的会话
currentSession.value = ChatSessionList.value.find(s => s.active) || null;

// 新消息
const messages = ref<{ role: string; content: string }[]>([]);

// 切换会话
function SwitchSessions(id: number) {
  ChatSessionList.value.forEach(session => {
    session.active = session.id === id;
    if (session.active) {
      currentSession.value = session;
    }
  });
}

// 发送消息
const handleMessageSend = (message: string) => {
  if (message.trim()) {
    messages.value.push({ role: 'user', content: message });
    if (currentSession.value) {
      currentSession.value.chatnum++;
    }
  }
};

// 创建新会话
const createNewSession = () => {
  const newId = Math.max(...ChatSessionList.value.map(s => s.id)) + 1;
  const newSession = {
    id: newId,
    active: true,
    chattopic: '新的对话',
    chatnum: 0,
    chattime: new Date().toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    }).replace(',', ''),
    chatHistory: []
  };
  
  // 将所有会话设为非活跃状态
  ChatSessionList.value.forEach(session => {
    session.active = false;
  });
  
  // 添加新会话到列表开头
  ChatSessionList.value.unshift(newSession);
  
  // 设置为当前会话
  currentSession.value = newSession;
  
  // 清空当前消息
  messages.value = [];
};
</script>

<style lang="scss" scoped>
.main-entry {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
  font-family: 'Microsoft YaHei', sans-serif;
  width: 100vw;
  overflow: hidden;

  .el-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 10px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    height: 60px;
    flex-shrink: 0;

    .header-title {
      font-size: 24px;
      font-weight: 600;
      margin: 0;
    }

    .header-right {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 15px;
      
      .user-name {
        color: white;
        font-size: 14px;
      }
    }

    .sys-button {
      display: flex;
    }
  }

  .chat-panel {
    flex: 1;
    min-height: 0;
    margin: 10px;
    border-radius: 20px;
    background-color: white;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    height: calc(100vh - 40px);
    max-height: calc(96vh - 55px);

    /* 左侧聊天会话面板*/
    .session-panel {
      background-color: rgb(231, 248, 255);
      width: 320px !important;
      min-width: 320px;
      border-top-left-radius: 20px;
      border-bottom-left-radius: 20px;
      padding: 15px 20px 10px 20px !important;
      display: flex;
      flex-direction: column;
      border-right: 1px solid rgba(0, 0, 0, 0.07);
      height: 100%;
      max-height: 100%;
      overflow: hidden;

      .title {
        font-size: 20px;
        color: rgba(0, 0, 0, 0.7);
        margin: 0 0 15px 0;
        flex-shrink: 0;
      }

      .session-list {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 15px;
        min-height: 0;
        max-height: calc(100vh - 300px);
        padding-right: 5px;

        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.1);
          border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.5);
        }

        .session {
          margin-bottom: 12px;
          
          &:last-child {
            margin-bottom: 0;
          }
        }
      }

      .button-wrapper {
        flex-shrink: 0;
        margin-top: auto;
        display: flex;
        justify-content: center;
        padding: 10px 0 5px 0;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        min-height: 80px;
        background-color: rgb(231, 248, 255);

        .new-session {
          width: 100%;
          height: 50px;
          font-size: 16px;
          font-weight: 500;
          border-radius: 12px;
        }
      }
    }

    .message-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      padding: 0 !important;
      height: 100%;

      .message-list {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        min-height: 0;
        max-height: calc(100vh - 140px);

        .chatBox {
          margin-bottom: 20px;
        }

        // 当切换聊天会话时，消息记录也随之切换的过渡效果
        .list-enter-active,
        .list-leave-active {
          transition: all 0.5s ease;
        }

        .list-enter-from,
        .list-leave-to {
          opacity: 0;
          transform: translateX(30px);
        }
      }

      .inputBox {
        flex-shrink: 0;
        padding: 20px;
        margin-bottom: 10px;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
      }
    }
  }
}
</style>