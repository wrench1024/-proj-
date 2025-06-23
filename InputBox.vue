<template>
  <div class="message-input">
    <div class="input-container">
      <!-- 按回车键发送，输入框高度三行 -->
      <el-input v-model="message" :autosize="false" :rows="3" class="input" resize="none" type="textarea"
        @keydown.enter="sendMessage">
      </el-input>
      <div class="button-container">
        <div class="left-buttons">
          <el-button type="primary">
            智能审查
          </el-button>
          <el-button type="primary">
            知识问答
          </el-button>
          <el-button type="primary">
            文档检索
          </el-button>
        </div>

        <el-button type="primary" class="right-buttons" @click="sendMessage">
          <el-icon>
            <Position />
          </el-icon>
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";


// 发送消息消息事件
const emit = defineEmits<{
  send: [message: string];
}>();
// 输入框内的消息
const message = ref("");
const sendMessage = () => {
  if (message.value.trim()) {
      emit("send", message.value);
  // 发送完清除
  message.value = "";
  }

};
</script>
<style lang="scss" scoped>
.message-input {
  width: 700px;
  padding: 20px;
  border-top: 1px solid rgba(black, 0.07);
  border-left: 1px solid rgba(black, 0.07);
  border-right: 1px solid rgba(black, 0.07);
  border-top-right-radius: 5px;
  border-top-left-radius: 5px;
}
.input-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.button-container {
  display: flex;
  justify-content: space-between;
  align-items: center;

}

.left-buttons,
.right-buttons {
  display: flex;
  gap: 5px;
}
</style>
