<template>
  <div class="knowledge-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar">
      <el-input v-model="searchQuery" placeholder="搜索知识库名称" clearable style="width: 300px" />
    <el-button type="primary" @click="handleSearch">
      <el-icon><search /></el-icon>
      搜索
    </el-button>
    <el-button type="success" @click="handleAdd">
      <el-icon><plus /></el-icon>
      新增知识库
    </el-button>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrapper">
      <el-table :data="displayData" border style="width: 100%; table-layout: fixed; overflow-x: hidden"
        :cell-style="{ padding: '12px 0' }">
        <el-table-column prop="index" label="序号" width="70" align="center" />
        <el-table-column prop="name" label="知识库名称" width="180" />
        <el-table-column prop="app" label="所属应用" width="120" />
        <el-table-column prop="fileCount" label="文件数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="creator" label="创建人" width="100" align="center" />
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="mini" @click="handleEdit(row)">
                <el-icon><edit /></el-icon>
                编辑
              </el-button>
              <el-button size="mini" type="primary" @click="handleImport(row)">
                <el-icon><upload /></el-icon>
                导入
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页控制 -->
    <div class="pagination-wrapper">
      <el-pagination 
        v-model:current-page="currentPage" 
        :page-size="pageSize" 
        :total="totalCount"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper" 
        background 
        @size-change="handleSizeChange"
      />
    </div>
  </div>

  <!-- 编辑对话框 -->
  <el-dialog v-model="dialogVisible" title="编辑知识库" width="600px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="所属应用">
        <el-input v-model="form.app" placeholder="请输入所属应用" />
      </el-form-item>
      <el-form-item label="知识库名称">
        <el-input v-model="form.name" placeholder="请输入知识库名称" />
      </el-form-item>
      <el-form-item label="知识库状态">
        <el-select v-model="form.status" placeholder="请选择状态">
          <el-option v-for="status in ['启用', '停用', '维护中']" :key="status" :label="status" :value="status" />
        </el-select>
      </el-form-item>
      <el-form-item label="排序">
        <el-input-number v-model="form.sort" :min="0" />
      </el-form-item>
      <el-form-item label="知识库描述">
        <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入知识库描述" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Search,
  Plus,
  Edit,
  Upload
} from '@element-plus/icons-vue'

// 常量定义
const PAGE_SIZE = 10
const STATUS_TYPES = {
  '启用': 'success',
  '停用': 'danger',
  '维护中': 'warning'
}

// 响应式数据
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}
const totalCount = ref(0)
const tableData = ref([])

// 计算属性
const displayData = computed(() => {
  return tableData.value.slice(
    (currentPage.value - 1) * pageSize.value,
    currentPage.value * pageSize.value
  )
})

const statusType = (status) => {
  return STATUS_TYPES[status] || ''
}

// 数据获取
const fetchData = async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      generateMockData()
    } else {
      const res = await axios.get('/api/knowledge-base', {
        params: {
          search: searchQuery.value
        }
      })
      tableData.value = res.data.list
      totalCount.value = res.data.total
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

// 模拟数据生成
const generateMockData = () => {
  const apps = ['XX系统', 'YY系统', 'ZZ系统', 'WW系统', 'AA系统']
  const statuses = ['启用', '停用', '维护中']
  const creators = ['张三', '李四', '王五', '赵六', '钱七']

  tableData.value = Array.from({ length: 100 }, (_, i) => ({
    index: i + 1,
    name: `知识库-${i + 1}`,
    app: apps[i % apps.length],
    fileCount: Math.floor(Math.random() * 100),
    status: statuses[i % statuses.length],
    remark: `这是第${i + 1}条测试数据`,
    creator: creators[i % creators.length],
    createTime: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleString()
  }))
  totalCount.value = tableData.value.length
}

// 事件处理
const handleSearch = () => {
  currentPage.value = 1
  if (process.env.NODE_ENV === 'development') {
    // 本地模拟搜索
    if (!searchQuery.value) {
      generateMockData()
      return
    }
    const query = searchQuery.value.toLowerCase()
    tableData.value = tableData.value.filter(item => 
      item.name.toLowerCase().includes(query) || 
      item.app.toLowerCase().includes(query) ||
      item.remark.toLowerCase().includes(query)
    )
    totalCount.value = tableData.value.length
  } else {
    // 实际API搜索
    fetchData()
  }
}

const handleAdd = () => {
  console.log('新增知识库')
}

const dialogVisible = ref(false)
const form = ref({
  app: '',
  name: '',
  status: '',
  sort: 0,
  description: ''
})

const handleEdit = (row) => {
  form.value = {
    app: row.app,
    name: row.name,
    status: row.status,
    sort: row.sort || 0,
    description: row.remark || ''
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!form.value.app || !form.value.name || !form.value.status) {
      ElMessage.error('请填写完整信息')
      return
    }

    if (process.env.NODE_ENV === 'development') {
      // 模拟保存
      const index = tableData.value.findIndex(item => item.id === form.value.id)
      if (index !== -1) {
        tableData.value[index] = {
          ...tableData.value[index],
          app: form.value.app,
          name: form.value.name,
          status: form.value.status,
          sort: form.value.sort,
          remark: form.value.description,
          // 保留原有字段
          id: tableData.value[index].id,
          fileCount: tableData.value[index].fileCount,
          creator: tableData.value[index].creator,
          createTime: tableData.value[index].createTime
        }
      }
      ElMessage.success('保存成功')
    } else {
      // 实际API调用
      await axios.put('/api/knowledge-base', form.value)
      ElMessage.success('保存成功')
      fetchData()
    }
    dialogVisible.value = false
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

import { useRouter } from 'vue-router'

const router = useRouter()

const handleImport = (row) => {
  console.log('导入:', row)
  router.push({
    path: '/knowledge-entry',
    query: { 
      knowledgeId: row.id,
      knowledgeName: row.name 
    }
  })
}

// 生命周期
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* 彻底禁用全局滚动 */
html, body, #app {
  overflow: hidden !important;
  height: 100% !important;
  position: relative !important;
}

/* 主容器设置 */


.knowledge-container {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background-color: #f5f7fa;
  overflow: hidden;
  position: relative;
}

/* 保留表格滚动 */
/* 表格滚动区域 */
.table-wrapper {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  max-height: calc(100vh - 225px);
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  align-items: center;
}

.el-table {
  --el-table-border-color: #ebeef5;
  --el-table-border: 1px solid var(--el-table-border-color);
  --el-table-header-bg-color: #f8fafc;
}

.el-icon {
  vertical-align: middle;
  margin-right: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
}

.action-buttons .el-button {
  height: 28px;
  line-height: 28px;
  padding: 0 12px;
  flex: 1;
  max-width: 80px;
}

.el-table__row:hover {
  background-color: #f5f7fa !important;
}

.el-table__row--striped {
  background-color: #fafafa;
}

.el-table__row--striped:hover {
  background-color: #f5f7fa !important;
}

.el-tag {
  font-weight: 500;
}

.el-tag--success {
  background-color: #f0f9eb;
  color: #67c23a;
}

.el-tag--danger {
  background-color: #fef0f0;
  color: #f56c6c;
}

.el-tag--warning {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.table-wrapper {
  flex: 1;
  margin-bottom: 10px;
  width: 100%;
  max-height: calc(100vh - 225px);
  overflow: auto;
}

.pagination-wrapper {
  margin: 0;
  display: flex;
  justify-content: flex-end;
  background: white;
  padding: 10px 0;
}
</style>
