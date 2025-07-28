<template>
  <div class="content">
    <div class="content-header">
      <h2>知识入库</h2>
      <button class="close-btn">×</button>
    </div>



    <!-- 主要标签页 -->
    <div class="main-tabs">
      <div class="tab-headers">
        <button class="tab-header" :class="{ active: activeTab === 'document' }" @click="activeTab = 'document'">
          📄 文档入库
        </button>
        <button class="tab-header" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
          📋 历史记录
        </button>
      </div>

      <!-- 文档入库标签页 -->
      <div v-if="activeTab === 'document'" class="tab-content">
        <!-- 主要内容区域：左右布局 -->
        <div class="main-content-layout">
          <!-- 左侧：知识库选择 + 文件上传 -->
          <div class="left-section">
            <!-- 知识库选择：标签和下拉菜单在同一行 -->
            <div class="form-group knowledge-base-row">
              <label>知识库</label>
              <select v-model="selectedKnowledgeBase" class="knowledge-base-select">
                <option value="">请选择知识库</option>
                <option value="贵州省行政区划">贵州省行政区划</option>
                <option value="其他">其他</option>
              </select>
            </div>

            <!-- 文件上传区域 -->
            <div class="form-group">
              <div class="upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleFileDrop">
                <div class="upload-icon">📁</div>
                <p>将文件拖拽到此处，或点击上传</p>
                <p class="upload-hint">支持 .txt, .doc, .docx, .pdf, .xlsx 等格式文件</p>
                <input ref="fileInput" type="file" @change="handleFileSelect" accept=".txt,.doc,.docx,.pdf,.xlsx"
                  style="display: none;" />
              </div>
            </div>
          </div>

          <!-- 右侧：文档解析内容 -->
          <div class="right-section">
            <div class="form-group">
              <label>文档解析内容</label>
              <div class="parsed-content-area">
                <div class="parsed-content-display">
                  {{ parsedContent || '文件解析后的内容将显示在这里...' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部：相似文档表格 -->
        <div class="bottom-section">
          <div class="form-group">
            <label>相似文档</label>
            <div class="similar-docs-table">
              <table>
                <thead>
                  <tr>
                    <th>序号</th>
                    <th>文件名</th>
                    <th>得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(doc, index) in similarDocs" :key="index">
                    <td>{{ index + 1 }}</td>
                    <td>{{ doc.fileName }}</td>
                    <td>{{ doc.score }}</td>
                  </tr>
                  <tr v-if="similarDocs.length === 0">
                    <td colspan="3" class="no-data">暂无相似文档</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 确认入库按钮 -->
          <div class="form-group button-group">
            <button class="confirm-btn" @click="confirmUpload">确认入库</button>
          </div>
        </div>
      </div>

      <!-- 历史记录标签页 -->
      <div v-if="activeTab === 'history'" class="tab-content">
        <div class="history-content">
          <!-- 筛选条件区域 -->
          <div class="filter-section">
            <div class="filter-row">
              <div class="filter-item">
                <label>知识库</label>
                <select v-model="historyKnowledgeBase" class="filter-select">
                  <option value="">全部知识库</option>
                  <option value="贵州省行政区划">贵州省行政区划</option>
                  <option value="水资源论证技术要求">水资源论证技术要求</option>
                  <option value="建设项目管理办法">建设项目管理办法</option>
                </select>
              </div>

              <div class="filter-item">
                <label>入库状态</label>
                <div class="status-options">
                  <button class="status-btn" :class="{ active: historyStatus === 'all' }"
                    @click="historyStatus = 'all'">
                    所有
                  </button>
                  <button class="status-btn" :class="{ active: historyStatus === 'processing' }"
                    @click="historyStatus = 'processing'">
                    入库中
                  </button>
                  <button class="status-btn" :class="{ active: historyStatus === 'failed' }"
                    @click="historyStatus = 'failed'">
                    入库失败
                  </button>
                  <button class="status-btn" :class="{ active: historyStatus === 'success' }"
                    @click="historyStatus = 'success'">
                    入库成功
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 历史记录表格 -->
          <div class="history-table-container">
            <table class="history-table">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>文件名</th>
                  <th>所在知识库</th>
                  <th>入库状态</th>
                  <th>上传人</th>
                  <th>上传时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(record, index) in filteredHistoryRecords" :key="record.id">
                  <td>{{ index + 1 }}</td>
                  <td>{{ record.fileName }}</td>
                  <td>{{ record.knowledgeBase }}</td>
                  <td>
                    <span class="status-badge" :class="record.status">
                      {{ getStatusText(record.status) }}
                    </span>
                  </td>
                  <td>{{ record.uploader }}</td>
                  <td>{{ record.uploadTime }}</td>
                  <td>
                    <div class="action-buttons">
                      <button class="action-btn download-btn" @click="downloadFile(record)">
                        下载
                      </button>
                      <button class="action-btn delete-btn" @click="deleteRecord(record)">
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredHistoryRecords.length === 0">
                  <td colspan="7" class="no-data">暂无历史记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 响应式数据
const activeNav = ref('knowledge')
const activeTab = ref('document')
const selectedKnowledgeBase = ref('')
const parsedContent = ref('')
const uploadedFiles = ref<File[]>([])
const fileInput = ref<HTMLInputElement>()

// 相似文档数据
const similarDocs = ref([
  { fileName: '水资源论证技术要求.pdf', score: '95%' },
  { fileName: '建设项目水资源论证管理办法.doc', score: '87%' },
  { fileName: '水资源论证导则.pdf', score: '82%' }
])

// 历史记录相关数据
const historyKnowledgeBase = ref('')
const historyStatus = ref('all')

// 历史记录数据
const historyRecords = ref([
  {
    id: 1,
    fileName: '水工建筑物安全监测技术规范.pdf',
    knowledgeBase: '贵州省行政区划',
    status: 'success',
    uploader: '张三',
    uploadTime: '2025-06-18 10:47'
  },
  {
    id: 2,
    fileName: '建设项目水资源论证管理办法.docx',
    knowledgeBase: '贵州省行政区划',
    status: 'success',
    uploader: '李四',
    uploadTime: '2025-04-17 14:10'
  },
  {
    id: 3,
    fileName: '水资源论证技术要求.pdf',
    knowledgeBase: '水资源论证技术要求',
    status: 'processing',
    uploader: '王五',
    uploadTime: '2025-06-19 09:30'
  },
  {
    id: 4,
    fileName: '水利工程建设标准.doc',
    knowledgeBase: '建设项目管理办法',
    status: 'failed',
    uploader: '赵六',
    uploadTime: '2025-06-18 16:25'
  }
])

// 过滤后的历史记录
const filteredHistoryRecords = computed(() => {
  let filtered = historyRecords.value

  // 按知识库筛选
  if (historyKnowledgeBase.value) {
    filtered = filtered.filter(record => record.knowledgeBase === historyKnowledgeBase.value)
  }

  // 按状态筛选
  if (historyStatus.value !== 'all') {
    filtered = filtered.filter(record => record.status === historyStatus.value)
  }

  return filtered
})

// 文件上传相关方法
const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    uploadedFiles.value = [file]
    // 模拟文件解析
    simulateFileParsing(file)
  }
}

const handleFileDrop = (event: DragEvent) => {
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    uploadedFiles.value = [file]
    // 模拟文件解析
    simulateFileParsing(file)
  }
}

// 模拟文件解析
const simulateFileParsing = (file: File) => {
  // 模拟解析过程
  parsedContent.value = '正在解析文件...'

  setTimeout(() => {
    parsedContent.value = `文件名：${file.name}\n文件大小：${formatFileSize(file.size)}\n\n解析内容：\n这是一个关于水资源论证的文档，包含了相关的法规条文和技术要求。文档详细描述了水资源论证的基本原则、技术方法和管理要求。\n\n主要内容包括：\n1. 水资源论证的基本概念\n2. 论证的技术要求\n3. 相关法律法规依据\n4. 实施细则和操作规范`
  }, 1500)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 确认入库
const confirmUpload = () => {
  if (!selectedKnowledgeBase.value) {
    alert('请选择知识库')
    return
  }

  if (uploadedFiles.value.length === 0) {
    alert('请上传文件')
    return
  }

  // 这里可以添加实际的入库逻辑
  console.log('确认入库:', {
    knowledgeBase: selectedKnowledgeBase.value,
    files: uploadedFiles.value,
    parsedContent: parsedContent.value
  })

  alert('文档入库成功！')
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedKnowledgeBase.value = ''
  parsedContent.value = ''
  uploadedFiles.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 历史记录相关方法
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'success': '入库成功',
    'processing': '入库中',
    'failed': '入库失败'
  }
  return statusMap[status] || status
}

const downloadFile = (record: any) => {
  // 这里可以添加实际的下载逻辑
  console.log('下载文件:', record.fileName)
  alert(`正在下载文件: ${record.fileName}`)
}

const deleteRecord = (record: any) => {
  if (confirm(`确定要删除文件 "${record.fileName}" 吗？`)) {
    const index = historyRecords.value.findIndex(r => r.id === record.id)
    if (index > -1) {
      historyRecords.value.splice(index, 1)
      alert('删除成功！')
    }
  }
}
</script>

<style scoped>
.knowledge-entry {
  height: 100vh;
  background-color: #f5f5f5;
  font-family: 'Microsoft YaHei', sans-serif;
  width: 100vw;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
}

/* 顶部标题栏 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  height: 60px;
  flex-shrink: 0;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.user-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.user-info span:last-child {
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info span:last-child:hover {
  background-color: rgba(255,255,255,0.2);
}

/* 主容器 */
.main-container {
  display: flex;
  height: calc(100vh - 60px);
  width: 100vw;
  background-color: white;
  overflow: hidden;
}

/* 左侧导航栏 */
.sidebar {
  width: 240px;
  min-width: 240px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #4a5568 0%, #2d3748 100%);
  color: white;
  padding: 0;
}

.nav-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 4px solid transparent;
  font-size: 14px;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background-color: #4299e1;
  border-left-color: #3182ce;
  font-weight: 600;
}

.nav-item span {
  font-size: 16px;
}

/* 右侧内容区域 */
.content {
  flex: 1;
  min-width: 0;
  background-color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.content-header {
  background-color: #ecf0f1;
  padding: 10px 30px;
  border-bottom: 1px solid #bdc3c7;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  height: 50px;
}

.content-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  background-color: #e74c3c;
  color: white;
}



/* 主要标签页 */
.main-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tab-headers {
  display: flex;
  background-color: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  height: 45px;
}

.tab-header {
  flex: 1;
  padding: 10px 25px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #4a5568;
  transition: all 0.3s;
  border-bottom: 3px solid transparent;
}

.tab-header.active {
  background-color: white;
  color: #3182ce;
  font-weight: 600;
  border-bottom-color: #3182ce;
}

.tab-header:hover:not(.active) {
  background-color: #edf2f7;
}

.tab-content {
  flex: 1;
  padding: 10px 3%;
  overflow-y: auto;
  max-width: none;
  width: 100%;
  box-sizing: border-box;
  height: calc(100vh - 155px);
}

/* 表单组件 */
.form-group {
  margin-bottom: 10px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #2d3748;
  font-size: 14px;
}

/* 知识库选择下拉框 */
.knowledge-base-select {
  flex: 1;
  max-width: 250px;
  padding: 8px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
  transition: border-color 0.3s;
}

.knowledge-base-select:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
}

/* 单选按钮组 */
.radio-group {
  display: flex;
  gap: 20px;
}

.radio-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
}

.radio-item input[type="radio"] {
  margin-right: 8px;
  transform: scale(1.2);
}

/* 内容输入区域 */
.content-input-area {
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
}

.input-tabs {
  display: flex;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ddd;
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.tab-btn.active {
  background-color: white;
  color: #3498db;
  font-weight: 600;
}

.tab-btn:hover:not(.active) {
  background-color: #e9ecef;
}

/* 文本输入区域 */
.text-input-section {
  padding: 20px;
}

.knowledge-textarea {
  width: 100%;
  min-height: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
}

.knowledge-textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

/* 文件上传区域 */
.upload-area {
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  padding: 20px 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #f7fafc;
  margin-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}

.upload-area:hover {
  border-color: #3182ce;
  background-color: #ebf8ff;
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-area p {
  margin: 4px 0;
  color: #4a5568;
  font-size: 13px;
}

.upload-hint {
  font-size: 11px !important;
  color: #718096 !important;
}

/* 文档解析内容区域 */
.parsed-content-area {
  width: 100%;
  min-height: 160px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background-color: #f7fafc;
  box-sizing: border-box;
  margin: 0;
  overflow: hidden;
}

.parsed-content-display {
  width: 100%;
  height: 100%;
  padding: 20px 15px;
  font-size: 13px;
  line-height: 1.5;
  font-family: inherit;
  color: #2d3748;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  box-sizing: border-box;
}

/* 移除了textarea的focus样式，因为现在使用div */

/* 主要内容布局 */
.main-content-layout {
  display: flex;
  gap: 40px;
  margin-bottom: 15px;
  width: 100%;
  align-items: flex-start;
}

.left-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.right-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* 确保左右两侧的内容区域对齐 */
.left-section .form-group:last-child {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.right-section .form-group {
  display: flex;
  flex-direction: column;
}

/* 让上传区域和文本框的边界完全对齐 */
.left-section .form-group:last-child {
  margin-top: 0;
  margin-bottom: 0;
}

.right-section .form-group {
  margin-top: 0;
  margin-bottom: 0;
}

/* 确保标签高度一致 */
.left-section .form-group:last-child label {
  height: 20px;
  line-height: 20px;
  margin-bottom: 8px;
  display: block;
}

.right-section .form-group label {
  height: 20px;
  line-height: 20px;
  margin-bottom: 28px;
  display: block;
}

.left-section .form-group:last-child .upload-area {
  margin-top: 0;
  margin-bottom: 0;
  /* 确保两个区域的边界完全对齐 */
  border-width: 2px;
  border-radius: 8px;
  box-sizing: border-box;
  flex: 1;
}

.right-section .form-group .parsed-content-area {
  margin-top: 0;
  margin-bottom: 0;
  /* 确保两个区域的边界完全对齐 */
  border-width: 2px;
  border-radius: 8px;
  box-sizing: border-box;
}

/* 确保上传区域的内边距 */
.left-section .form-group:last-child .upload-area {
  padding: 20px 15px;
}

/* 文档解析内容区域不需要额外padding，因为内部div有padding */
.right-section .form-group .parsed-content-area {
  padding: 0;
}

/* 知识库选择行布局 */
.knowledge-base-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.knowledge-base-row label {
  margin-bottom: 0 !important;
  white-space: nowrap;
  min-width: 60px;
}

/* 底部区域 */
.bottom-section {
  width: 100%;
}

.button-group {
  text-align: center;
  margin-top: 10px;
}

/* 已上传文件列表 */
.uploaded-files {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.uploaded-files h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 16px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-name {
  flex: 1;
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  color: #7f8c8d;
  font-size: 12px;
  margin-right: 15px;
}

.remove-btn {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.remove-btn:hover {
  background-color: #c0392b;
}

/* 确认入库按钮 */
.confirm-btn {
  background-color: #3182ce;
  color: white;
  border: none;
  padding: 10px 30px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.confirm-btn:hover {
  background-color: #2c5aa0;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

/* 相似文档表格 */
.similar-docs-table {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  margin-top: 8px;
  height: 120px;
  overflow-y: auto;
}

.similar-docs-table table {
  width: 100%;
  border-collapse: collapse;
}

.similar-docs-table th {
  background-color: #f7fafc;
  padding: 10px 15px;
  text-align: left;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
}

.similar-docs-table td {
  padding: 10px 15px;
  border-bottom: 1px solid #e2e8f0;
  color: #4a5568;
  font-size: 13px;
}

.similar-docs-table th:first-child,
.similar-docs-table td:first-child {
  width: 80px;
  text-align: center;
}

.similar-docs-table th:last-child,
.similar-docs-table td:last-child {
  width: 100px;
  text-align: center;
}

.similar-docs-table tbody tr:hover {
  background-color: #f7fafc;
}

.similar-docs-table tbody tr:last-child td {
  border-bottom: none;
}

.no-data {
  text-align: center;
  color: #a0aec0;
  font-style: italic;
}

/* 历史记录内容 */
.history-content {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 筛选条件区域 */
.filter-section {
  background-color: #f7fafc;
  padding: 15px 20px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 40px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-item label {
  font-weight: 600;
  color: #2d3748;
  font-size: 14px;
  margin-bottom: 0;
  white-space: nowrap;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  min-width: 150px;
}

.filter-select:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.1);
}

.status-options {
  display: flex;
  gap: 8px;
}

.status-btn {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  background-color: white;
  color: #4a5568;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.status-btn:hover {
  background-color: #f7fafc;
  border-color: #cbd5e0;
}

.status-btn.active {
  background-color: #3182ce;
  color: white;
  border-color: #3182ce;
}

/* 历史记录表格容器 */
.history-table-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.history-table th {
  background-color: #f7fafc;
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  font-size: 14px;
}

.history-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e2e8f0;
  color: #4a5568;
  font-size: 13px;
}

.history-table tbody tr:hover {
  background-color: #f7fafc;
}

.history-table tbody tr:last-child td {
  border-bottom: none;
}

/* 表格列宽设置 */
.history-table th:nth-child(1),
.history-table td:nth-child(1) {
  width: 60px;
  text-align: center;
}

.history-table th:nth-child(2),
.history-table td:nth-child(2) {
  width: 25%;
}

.history-table th:nth-child(3),
.history-table td:nth-child(3) {
  width: 15%;
}

.history-table th:nth-child(4),
.history-table td:nth-child(4) {
  width: 10%;
  text-align: center;
}

.history-table th:nth-child(5),
.history-table td:nth-child(5) {
  width: 10%;
  text-align: center;
}

.history-table th:nth-child(6),
.history-table td:nth-child(6) {
  width: 15%;
  text-align: center;
}

.history-table th:nth-child(7),
.history-table td:nth-child(7) {
  width: 15%;
  text-align: center;
}

/* 状态标签 */
.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.status-badge.success {
  background-color: #c6f6d5;
  color: #22543d;
}

.status-badge.processing {
  background-color: #bee3f8;
  color: #2a4365;
}

.status-badge.failed {
  background-color: #fed7d7;
  color: #742a2a;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s;
}

.download-btn {
  background-color: #3182ce;
  color: white;
}

.download-btn:hover {
  background-color: #2c5aa0;
  transform: translateY(-1px);
}

.delete-btn {
  background-color: #e53e3e;
  color: white;
}

.delete-btn:hover {
  background-color: #c53030;
  transform: translateY(-1px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
  }

  .nav-item {
    display: inline-block;
    margin-right: 10px;
    padding: 12px 20px;
  }

  .content {
    margin: 10px;
  }

  .knowledge-type-section {
    padding: 15px 20px;
  }

  .tab-content {
    padding: 20px;
  }

  .radio-group {
    flex-direction: column;
    gap: 10px;
  }

  .tab-headers {
    flex-direction: column;
  }

  .tab-header {
    border-bottom: 1px solid #e2e8f0;
    border-right: none;
  }

  .tab-header.active {
    border-bottom-color: #3182ce;
    border-right: none;
  }

  .upload-area {
    padding: 30px 15px;
  }

  .similar-docs-table {
    font-size: 14px;
  }

  .similar-docs-table th,
  .similar-docs-table td {
    padding: 8px 12px;
  }

  .main-content-layout {
    flex-direction: column;
    gap: 15px;
  }

  .left-section,
  .right-section {
    flex: none;
  }

  .knowledge-base-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .knowledge-base-row label {
    margin-bottom: 6px !important;
  }

  .knowledge-base-select {
    max-width: 100%;
  }

  .similar-docs-table {
    height: auto;
    max-height: 200px;
  }
}

</style>
