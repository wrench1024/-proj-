<template>
  <div :class="['message-row', role === 'user' ? 'right' : 'left']">
    <!-- 消息展示，分为上下，上面是头像，下面是消息 -->
      <!-- 发送的消息或者回复的消息 -->
      <div class="message">
        <!-- 预览模式，用来展示markdown格式的消息 -->
        <MdPreview
            :id="'preview-only'"
            :preview-theme="'smart-blue'"
            :model-value="content"
            :style="{
            backgroundColor:
              role === 'user' ? 'rgb(231, 248, 255)' : '#f4f4f5',
          }"
            v-if="content"
        ></MdPreview>
        <!-- 如果消息的内容为空则显示加载动画 -->
        <TextLoading v-else></TextLoading>
      </div>
    </div>
</template>

<script lang="ts" setup>
const props = defineProps({
  // 消息的角色，值可以是 'user' 或 'assistant'
  role: {
    type: String,
    required: true,
    validator: (value: string) => {
      return ['user', 'assistant'].includes(value);
    }
  },
  // 消息的具体内容
  content: {
    type: String,
    default: ''
  }
});
</script>

<style lang="scss" scoped>
  .message-row {
    display: flex;

    &.right {
      // 消息显示在右侧
      justify-content: flex-end;

      .row {
        // 头像也要靠右侧
        .avatar-wrapper {
          display: flex;
          justify-content: flex-end;
        }

        // 用户回复的消息和ChatGPT回复的消息背景颜色做区分
        .message {
          background-color: rgb(231, 248, 255);
        }
      }
    }
    .row {
      .avatar-wrapper {
        .avatar {
          box-shadow: 20px 20px 20px 3px rgba(0, 0, 0, 0.03);
          margin-bottom: 20px;
        }
      }

      .message {
        font-size: 15px;
        padding: 1.5px;
        max-width: 500px;
        border-radius: 7px;
        border: 1px solid rgba(black, 0.1);
        box-shadow: 20px 20px 20px 1px rgba(0, 0, 0, 0.01);
      }
    }
  }
  :deep(.md-editor-preview-wrapper) {
    padding: 0 10px;

    .smart-blue-theme p {
      line-height: unset;
    }
  }
</style>
