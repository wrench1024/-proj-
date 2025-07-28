<template>
    <div :class="['session-item', active ? 'active' : '']" @click="handleClick">
        <div class="name">{{ chattopic }}</div>
        <div class="count-time">
            <div class="count">
                {{ chatnum }}条对话
            </div>
            <div class="time">{{ chattime }}</div>
        </div>
        <div class="mask"></div>
        <div class="btn-wrapper">
            <el-icon :size="15" class="close">
                <el-popconfirm title="是否确认永久删除该聊天会话？"
                @confirm="deletesession">
                    <template #reference>
                        <CircleClose />
                    </template>
                </el-popconfirm>
            </el-icon>
        </div>
    </div>
</template>

<script lang="ts">
export default {
  name: 'ChatCard'
}
</script>

<script setup lang="ts">
import { CircleClose } from "@element-plus/icons-vue";

const prop = defineProps<{ 
  // active：标记当前会话是否处于选中状态
  active: boolean; 
  id:number;
  chattopic:string;
  chatnum:number;
  chattime:string
 }>();
 
const emit = defineEmits<{
  (event: 'clickSession', id: number): void;
}>();

// 点击卡片后选中当前卡片，并修改active值
function handleClick() {
  emit('clickSession', prop.id);
}

function deletesession(){
    
}
</script>
<style lang="scss" scoped>
  .session-item {
    padding: 12px;
    background-color: white;
    border-radius: 10px;
    width: 250px;
    position: relative;
    cursor: grab;
    overflow: hidden;

    .name {
      font-size: 14px;
      font-weight: 700;
      width: 200px;
      color: rgba(black, 0.8);
    }

    .count-time {
      margin-top: 10px;
      font-size: 10px;
      color: rgba(black, 0.5);
      display: flex;
      justify-content: space-between;
    }

    &.active {
      transition: all 0.12s linear;
      border: 2px solid #1d93ab;
    }

    &:hover {
      .mask {
        opacity: 1;
        left: 0;
      }

      .btn-wrapper {
        &:hover {
          cursor: pointer;
        }
        opacity: 1;
        right: 20px;
      }
    }

    .mask {
      transition: all 0.2s ease-out;
      position: absolute;
      background-color: rgba(black, 0.05);
      width: 100%;
      height: 100%;
      top: 0;
      left: -100%;
      opacity: 0;
    }

    .btn-wrapper {
      color: rgba(black, 0.5);
      transition: all 0.2s ease-out;
      position: absolute;
      top: 10px;
      right: -20px;
      z-index: 10;
      opacity: 0;

      .edit {
        margin-right: 5px;
      }
    }
  }
</style>