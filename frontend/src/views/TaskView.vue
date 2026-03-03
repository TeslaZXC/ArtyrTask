<template>
  <div class="task-page page-container flex-center">
    <div class="task-modal-card glass-panel" v-loading="loading">
      <div v-if="task" class="task-content">
        <div class="task-header">
          <div class="header-left">
            <el-icon :size="20"><Monitor /></el-icon>
            <el-input
              v-if="isEditingTitle"
              v-model="editTitle"
              class="title-edit"
              @blur="saveTitle"
              @keyup.enter="saveTitle"
              @keyup.esc="isEditingTitle = false"
              autofocus
            />
            <h2 v-else @click="startEditingTitle" class="task-title">{{ task.title }}</h2>
          </div>
          <el-button text :icon="Close" @click="goBack" class="close-btn" />
        </div>

        <div class="task-body">
          <div class="main-column">
            <!-- Description section -->
            <div class="section">
              <div class="section-header">
                <el-icon :size="18"><Document /></el-icon>
                <h3>Описание</h3>
              </div>
              <div class="description-content">
                <div v-if="!isEditingDesc && !task.description" class="empty-desc" @click="startEditingDesc">
                  Добавить более подробное описание...
                </div>
                <div v-else-if="!isEditingDesc" class="desc-text" @click="startEditingDesc">
                  {{ task.description }}
                </div>
                <div v-else class="desc-editor">
                  <el-input
                    v-model="editDesc"
                    type="textarea"
                    :rows="4"
                    placeholder="Добавить более подробное описание..."
                    autofocus
                  />
                  <div class="editor-actions">
                    <el-button type="primary" @click="saveDesc">Сохранить</el-button>
                    <el-button text @click="isEditingDesc = false">Отмена</el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Attachments section -->
            <div class="section" v-if="task.attachments?.length">
              <div class="section-header">
                <el-icon :size="18"><Paperclip /></el-icon>
                <h3>Вложения</h3>
              </div>
              <div class="attachments-list">
                <div v-for="att in task.attachments" :key="att.id" class="attachment-item">
                  <div class="attachment-thumb">
                    <el-icon><Picture /></el-icon>
                  </div>
                  <div class="attachment-details">
                    <a :href="`http://localhost:8000${att.file_path}`" target="_blank">{{ att.file_name }}</a>
                    <span class="attachment-date">Добавлено {{ new Date(att.uploaded_at).toLocaleDateString('ru-RU') }}</span>
                  </div>
                  <el-button text type="danger" :icon="Delete" @click="deleteAttachment(att.id)" size="small" />
                </div>
              </div>
            </div>

            <!-- Links section -->
            <div class="section" v-if="task.links?.length">
              <div class="section-header">
                <el-icon :size="18"><Link /></el-icon>
                <h3>Ссылки</h3>
              </div>
              <div class="links-list">
                <div v-for="link in task.links" :key="link.id" class="link-item">
                  <a :href="link.url" target="_blank">{{ link.title || link.url }}</a>
                  <el-button text type="danger" :icon="Delete" @click="deleteLink(link.id)" size="small" />
                </div>
              </div>
            </div>
          </div>

          <!-- Sidebar actions -->
          <div class="sidebar-column">
            <div class="action-module">
              <h4>Добавить к карточке</h4>
              <el-upload
                class="upload-btn"
                action=""
                :http-request="uploadFile"
                :show-file-list="false"
              >
                <el-button class="full-width-btn" :icon="Paperclip">Вложение</el-button>
              </el-upload>
              <el-button class="full-width-btn" :icon="Link" @click="linkDialogVisible = true">Ссылка</el-button>
              <el-button 
                class="full-width-btn" 
                :type="task.is_completed ? 'success' : 'default'" 
                :icon="Check"
                @click="toggleComplete"
              >
                {{ task.is_completed ? 'Выполнено' : 'Отметить как выполненное' }}
              </el-button>
            </div>
            
            <div class="action-module action-danger">
              <h4>Действия</h4>
              <el-button class="full-width-btn" type="danger" text :icon="Delete" @click="confirmDeleteTask">
                Удалить задачу
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Link Dialog -->
    <el-dialog v-model="linkDialogVisible" title="Прикрепить ссылку" width="400px">
      <el-form @submit.prevent="handleAddLink" layout="vertical">
        <el-form-item label="URL">
          <el-input v-model="newLink.url" placeholder="https://..." autofocus />
        </el-form-item>
        <el-form-item label="Текст ссылки (необязательно)">
          <el-input v-model="newLink.title" placeholder="Отображаемый текст" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkDialogVisible = false">Отмена</el-button>
        <el-button type="primary" @click="handleAddLink" :disabled="!newLink.url">Прикрепить</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBoardStore } from '../stores/board'
import { api } from '../services/api'
import { Monitor, Close, Document, Paperclip, Link, Check, Delete, Picture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const boardStore = useBoardStore()
const taskId = Number(route.params.id)

const task = ref(null)
const loading = ref(true)

const isEditingTitle = ref(false)
const editTitle = ref('')

const isEditingDesc = ref(false)
const editDesc = ref('')

const linkDialogVisible = ref(false)
const newLink = ref({ url: '', title: '' })

onMounted(async () => {
  await fetchTask()
})

const fetchTask = async () => {
  loading.value = true
  try {
    const res = await api.get(`/tasks/${taskId}`)
    task.value = res.data
  } catch (e) {
    ElMessage.error('Не удалось загрузить детали задачи')
    goBack()
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const startEditingTitle = () => {
  editTitle.value = task.value.title
  isEditingTitle.value = true
}

const saveTitle = async () => {
  if (editTitle.value.trim() && editTitle.value !== task.value.title) {
    task.value = await boardStore.updateTask(taskId, { title: editTitle.value.trim() })
  }
  isEditingTitle.value = false
}

const startEditingDesc = () => {
  editDesc.value = task.value.description || ''
  isEditingDesc.value = true
}

const saveDesc = async () => {
  task.value = await boardStore.updateTask(taskId, { description: editDesc.value.trim() })
  isEditingDesc.value = false
}

const toggleComplete = async () => {
  task.value = await boardStore.updateTask(taskId, { is_completed: !task.value.is_completed })
}

const confirmDeleteTask = () => {
  ElMessageBox.confirm('Удалить эту задачу?', 'Внимание', { type: 'warning' }).then(async () => {
    await boardStore.deleteTask(taskId, task.value.list_id)
    goBack()
  }).catch(() => {})
}

const uploadFile = async (options) => {
  try {
    const file = options.file
    if (file.size / 1024 / 1024 > 5) {
      ElMessage.warning('Размер файла должен быть меньше 5МБ')
      return false
    }
    await boardStore.uploadAttachment(taskId, file)
    await fetchTask()
    ElMessage.success('Вложение добавлено')
  } catch(e) {
    ElMessage.error('Ошибка загрузки')
  }
}

const handleAddLink = async () => {
  if (!newLink.value.url.trim()) return
  try {
    await boardStore.addLink(taskId, newLink.value.url.trim(), newLink.value.title.trim() || undefined)
    linkDialogVisible.value = false
    newLink.value = { url: '', title: '' }
    await fetchTask()
    ElMessage.success('Ссылка добавлена')
  } catch(e) {
    ElMessage.error('Не удалось добавить ссылку')
  }
}

const deleteAttachment = async (id) => {
  await api.delete(`/tasks/attachments/${id}`)
  await fetchTask()
}

const deleteLink = async (id) => {
  await api.delete(`/tasks/links/${id}`)
  await fetchTask()
}
</script>

<style scoped>
.task-page {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  align-items: flex-start;
  padding-top: 4rem;
  overflow-y: auto;
}

.task-modal-card {
  width: 100%;
  max-width: 768px;
  background: var(--surface-color);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-bottom: 4rem;
  min-height: 400px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  color: var(--text-primary);
  flex: 1;
}

.header-left .el-icon {
  margin-top: 5px;
}

.task-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  cursor: pointer;
}

.title-edit {
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  font-size: 1.5rem;
  color: var(--text-secondary);
  padding: 0;
}

.task-body {
  display: flex;
  gap: 2rem;
}

.main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.sidebar-column {
  width: 180px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.section-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.empty-desc {
  background: rgba(255,255,255,0.05);
  padding: 1rem;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
}

.empty-desc:hover {
  background: rgba(255,255,255,0.08);
}

.desc-text {
  white-space: pre-wrap;
  cursor: pointer;
  line-height: 1.5;
}

.desc-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.editor-actions {
  display: flex;
  gap: 0.5rem;
}

.action-module h4 {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.full-width-btn {
  width: 100%;
  justify-content: flex-start;
  margin-bottom: 0.5rem;
  margin-left: 0 !important;
  background: rgba(255,255,255,0.05);
  border: none;
}

.full-width-btn:hover {
  background: rgba(255,255,255,0.1);
}

.action-danger .full-width-btn:hover {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

/* Attachments */
.attachment-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.attachment-thumb {
  width: 80px;
  height: 60px;
  background: rgba(255,255,255,0.05);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.attachment-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.attachment-details a {
  font-weight: 500;
  color: var(--text-primary);
  text-decoration: underline;
}

.attachment-date {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* Links */
.link-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.link-item a {
  color: var(--primary-color);
  text-decoration: underline;
}
</style>
