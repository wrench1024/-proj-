<template>
  <el-container class="main-entry">
    <!--————————————————————————标题———————————————————————————-->
    <el-header>
      <h1 class="header-title">水资源论证智能审查AI助手</h1>
      <div class="d1">
        <el-button type="primary" class="sys-button">系统设置</el-button>
        <span>用户名：管理员</span>
      </div>
      <h2>
      </h2>
    </el-header>
    <el-container class="chat-panel">
      <!--————————————————————————左侧历史记录———————————————————————————-->
      <div class="session-panel">
        <div class="title">历史对话</div>
        <div class="session-list">
          <chatCard class="session" v-for="session in ChatSessionList" :key="session.id" :active="session.active"
            :id="session.id" :chattopic="session.chattopic" :chatnum="session.chatnum" :chattime="session.chattime"
            @clickSession="SwitchSessions" />
        </div>
        <div class="button-wrapper">
          <div class="new-session">
            <el-button>
              <el-icon :size="15">
                <CirclePlus />
              </el-icon>
              新的聊天
            </el-button>
          </div>
        </div>
      </div>
      <!--————————————————————————聊天内容———————————————————————————-->
      <div class="message-panel">
        <div class="header">
          <div class="front">
            <div v-if="isEdit" class="title">
              <el-input v-model="sessionTopic" @keydown.enter="handleUpdateSession"></el-input>
            </div>
            <div v-else class="title">{{ currentSession?.chattopic }}</div>
            <div class="description">
              {{ currentSession?.chatnum }}条对话
            </div>
          </div>
          <div class="rear">
            <el-icon :size="20">
              <EditPen @click="isEdit = true" v-if="!isEdit" />
              <Close @click="isEdit = false" v-else></Close>
            </el-icon>
          </div>
        </div>
        <el-divider :border-style="'solid'" />
        <div class="message-list">
         <chatBox class="chatBox" v-for="(msg, index) in currentSession?.chatHistory || []" :key="index" :role="msg.role" :content="msg.content" />
          <chatBox class="chatBox" v-for="(msg, index) in messages" :key="index" :role="msg.role"
            :content="msg.content" />
        </div>
        <div class="inputBox">
          <inputBox @send="handleMessageSend" />
        </div>
      </div>
    </el-container>
  </el-container>

</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { CirclePlus, Close, EditPen } from "@element-plus/icons-vue";
import chatCard from "./ChatCard.vue"
import waitAnimation from "./WaitAnimation.vue"
import chatBox from "./ChatBox.vue"
import inputBox from "./InputBox.vue";

const isEdit = ref(false);
const sessionTopic = ref('');
const currentSession = ref<{
  id: number;
  active: boolean;
  chattopic: string;
  chatnum: number;
  chattime: string;
      chatHistory: { role: string; content: string }[]; 
} | null>(null);
const ChatSessionList = ref([
  {
    id: 1,
    active: true,
    chattopic: '贵州省行政区划',
    chatnum: 4,
    chattime: '2025-06-18 10:47',
    chatHistory:  [
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
])
function SwitchSessions(id: number) {
  ChatSessionList.value.forEach(session => {
    session.active = session.id === id;
    if (session.active) {
      currentSession.value = session;
    }
  });
}
const handleUpdateSession = () => {
  if (currentSession.value) {
    currentSession.value.chattopic = sessionTopic.value;
  }
  isEdit.value = false;
};
const messages = ref<{ role: string; content: string }[]>([]);//用户发送的信息
const handleMessageSend = (message: string) => {
  if (message.trim()) {
    // 将消息添加到消息列表中
    messages.value.push({ role: 'user', content: message });
    // 更新当前会话的消息数量
    if (currentSession.value) {
      currentSession.value.chatnum++;
    }
  }
};
</script>

<style lang="scss" scoped>
.main-entry {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
  font-family: 'Microsoft YaHei', sans-serif;
  width: 100vw;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;


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
      position: fixed;
      font-size: 24px;
      font-weight: 600;
    }

    .d1 {
      min-width: 100%;
      height: 40px;
      position: relative;
      display: flex;
      justify-content: flex-end;
    }

    .sys-button {
      display: flex;
      position: relative;
    }
  }

  .chat-panel {
    display: flex;
    border-radius: 20px;
    background-color: white;
    box-shadow: 0 0 20px 20px rgba(black, 0.05);

    /* 左侧聊天会话面板*/
    .session-panel {
      background-color: rgb(231, 248, 255);
      width: 300px;
      border-top-left-radius: 20px;
      border-bottom-left-radius: 20px;
      padding: 20px;
      position: relative;
      border-right: 1px solid rgba(black, 0.07);

      .title {
        margin-top: 20px;
        font-size: 20px;
        color: rgba(black, 0.7);
      }
    }

    .session-list {
      .session {
        margin-top: 20px;
      }
    }

    .button-wrapper {
      position: absolute;
      bottom: 20px;
      left: 0;
      display: flex;
      justify-content: flex-end;
      width: 100%;

      .new-session {
        margin-right: 20px;
      }
    }
  }

  .message-panel {
    width: 1200px;

  }

  .header {
    padding: 20px 20px 0 20px;
    display: flex;
    justify-content: space-between;

    .front {
      height: 40px;
      margin-top: -10px;

      .title {
        margin-top: -5px;
        color: rgba(black, 0.7);
        font-size: 20px;
      }

      .description {
        margin-top: 10px;
        color: rgba(black, 0.5);
      }
    }

    .rear {
      display: flex;
      align-items: center;
      color: black;
    }
  }

  .inputBox {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }

  .message-list {
    height: 420px;
    padding: 15px;
    overflow-y: scroll;

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

}
</style>