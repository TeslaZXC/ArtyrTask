<template>
  <div class="page-container workspaces-page">
    <div class="page-header">
      <h1 class="page-title">Ваши Рабочие Пространства</h1>
      <el-button type="primary" @click="createDialogVisible = true" :icon="Plus">
        Новое Пространство
      </el-button>
    </div>

    <div v-loading="workspaceStore.loading" class="workspaces-grid">
      <div 
        v-for="workspace in workspaceStore.workspaces" 
        :key="workspace.id" 
        class="workspace-card glass-panel"
        @click="goToWorkspace(workspace.id)"
      >
        <div class="workspace-icon">
          <el-icon :size="32"><Platform /></el-icon>
        </div>
        <div class="workspace-info">
          <h3>{{ workspace.name }}</h3>
          <p class="workspace-date">Создано {{ new Date(workspace.created_at).toLocaleDateString('ru-RU') }}</p>
        </div>
        <div class="workspace-actions">
          <el-button 
            type="danger" 
            text 
            @click.stop="confirmDelete(workspace)"
            :icon="Delete"
          />
        </div>
      </div>
      
      <div v-if="!workspaceStore.loading && workspaceStore.workspaces.length === 0" class="empty-state">
        <el-icon :size="48"><FolderOpened /></el-icon>
        <p>Пока нет рабочих пространств</p>
        <el-button type="primary" @click="createDialogVisible = true">Создайте первое сейчас</el-button>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="createDialogVisible" title="Новое Рабочее Пространство" width="400px" custom-class="glass-dialog">
      <el-form @submit.prevent="handleCreate">
        <el-form-item label="Название">
          <el-input v-model="newWorkspaceName" placeholder="например, Команда Разработки" autofocus />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">Отмена</el-button>
          <el-button type="primary" @click="handleCreate" :disabled="!newWorkspaceName.trim()">
            Создать
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '../stores/workspace'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Platform, Delete, FolderOpened } from '@element-plus/icons-vue'

const router = useRouter()
const workspaceStore = useWorkspaceStore()

const createDialogVisible = ref(false)
const newWorkspaceName = ref('')

onMounted(async () => {
  await workspaceStore.fetchWorkspaces()
})

const goToWorkspace = (id) => {
  router.push(`/workspaces/${id}/boards`)
}

const handleCreate = async () => {
  if (!newWorkspaceName.value.trim()) return
  try {
    await workspaceStore.createWorkspace(newWorkspaceName.value.trim())
    createDialogVisible.value = false
    newWorkspaceName.value = ''
    ElMessage.success('Рабочее пространство создано')
  } catch (e) {
    ElMessage.error('Ошибка создания пространства')
  }
}

const confirmDelete = (workspace) => {
  ElMessageBox.confirm(
    `Вы уверены, что хотите удалить "${workspace.name}"? Это удалит все доски, списки и задачи внутри.`,
    'Внимание',
    {
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await workspaceStore.deleteWorkspace(workspace.id)
      ElMessage.success('Рабочее пространство удалено')
    } catch(e) {
      ElMessage.error('Ошибка при удалении пространства')
    }
  }).catch(() => {})
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
}

.workspaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.workspace-card {
  padding: 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  position: relative;
}

.workspace-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
  background: var(--surface-hover);
}

.workspace-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  display: flex;
  justify-content: center;
  align-items: center;
}

.workspace-info {
  flex: 1;
}

.workspace-info h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.workspace-date {
  margin: 0.2rem 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.workspace-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.workspace-card:hover .workspace-actions {
  opacity: 1;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
  background: var(--glass-bg);
  border-radius: 12px;
  border: 1px dashed var(--border-color);
}

.empty-state p {
  margin: 1rem 0 1.5rem;
  font-size: 1.1rem;
}
</style>
