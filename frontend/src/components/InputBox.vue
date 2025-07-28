<template>
  <div class="message-input">
    <div class="input-container">
      <!-- 输入框 -->
      <el-input v-model="message" :autosize="false" :rows="3" class="input" resize="none" type="textarea"
        @keydown.enter="sendMessage" placeholder="请输入您的问题...">
      </el-input>
      
      <!-- 按钮区域 -->
      <div class="button-container">
        <div class="left-buttons">
          <el-button class="function-btn">智能审查</el-button>
          <el-button class="function-btn">知识问答</el-button>
          <el-button class="function-btn">文档检索</el-button>
          <div class="model-selector">
            <span class="model-label">模型：</span>
            <el-dropdown>
              <span class="model-dropdown">
                {{ getModelDisplayName(selectedModel) }}
                <el-icon class="el-icon--right">
                  <ArrowDown />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="selectModel('deepseek-v3')">DeepSeek V3</el-dropdown-item>
                  <el-dropdown-item @click="selectModel('gpt-4')">GPT-4</el-dropdown-item>
                  <el-dropdown-item @click="selectModel('claude-3')">Claude 3</el-dropdown-item>
                  <el-dropdown-item @click="selectModel('qwen-max')">通义千问 Max</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <el-button class="function-btn">更多工具</el-button>
        </div>
        <el-button type="primary" class="send-button" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'InputBox'
}
</script>

<script lang="ts" setup>
import { ref } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";

// 发送消息消息事件
const emit = defineEmits<{
  send: [message: string];
}>();

// 输入框内的消息
const message = ref("");
// 当前选择的模型
const selectedModel = ref("deepseek-v3");

const sendMessage = () => {
  if (message.value.trim()) {
      emit("send", message.value);
  // 发送完清除
  message.value = "";
  }
};

const selectModel = (model: string) => {
  selectedModel.value = model;
  console.log("选择的模型:", model);
  // 这里可以添加模型切换的逻辑
};

const getModelDisplayName = (model: string) => {
  const modelMap: Record<string, string> = {
    'deepseek-v3': 'DeepSeek V3',
    'gpt-4': 'GPT-4',
    'claude-3': 'Claude 3',
    'qwen-max': '通义千问 Max'
  };
  return modelMap[model] || 'DeepSeek V3';
};
</script>
<style lang="scss" scoped>
.message-input {
  width: 100%;
  background-color: white;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.input-container {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input {
  width: 100%;
  
  :deep(.el-textarea__inner) {
    border: none;
    border-radius: 8px;
    background-color: #f8f9fa;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    resize: none;
    min-height: 80px;
    
    &:focus {
      background-color: white;
      border: 1px solid #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
      outline: none;
    }
    
    &::placeholder {
      color: #c0c4cc;
    }
  }
}

.button-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 4px;
}

.model-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.model-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #409eff;
  padding: 2px 4px;
  border-radius: 4px;
  
  &:hover {
    background-color: #f0f9ff;
  }
  
  .el-icon {
    font-size: 12px;
  }
}

.function-btn {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  color: #606266;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  height: auto;
  min-height: 32px;
  
  &:hover {
    background-color: #ecf5ff;
    border-color: #b3d8ff;
    color: #409eff;
  }
  
  &:active {
    background-color: #d9ecff;
    border-color: #409eff;
  }
}

.send-button {
  background-color: #409eff;
  border-color: #409eff;
  color: white;
  border-radius: 8px;
  padding: 8px 24px;
  font-size: 14px;
  font-weight: 500;
  min-height: 36px;
  
  &:hover {
    background-color: #66b1ff;
    border-color: #66b1ff;
  }
  
  &:active {
    background-color: #3a8ee6;
    border-color: #3a8ee6;
  }
}
</style>
