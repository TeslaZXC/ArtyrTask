<template>
  <div class="page-container boards-page">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="router.push('/workspaces')" :icon="ArrowLeft" class="back-btn">
          Назад к пространствам
        </el-button>
        <h1 class="page-title">{{ currentWorkspace?.name || 'Доски пространства' }}</h1>
      </div>
      <el-button type="primary" @click="createDialogVisible = true" :icon="Plus">
        Новая доска
      </el-button>
    </div>

    <div v-loading="workspaceStore.loading" class="boards-grid">
      <div 
        v-for="board in workspaceStore.currentWorkspaceBoards" 
        :key="board.id" 
        class="board-card glass-panel"
        @click="goToBoard(board.id)"
      >
        <div class="board-info">
          <h3>{{ board.name }}</h3>
        </div>
        <div class="board-actions">
          <el-button 
            type="danger" 
            text 
            @click.stop="confirmDelete(board)"
            :icon="Delete"
          />
        </div>
      </div>
      
      <div v-if="!workspaceStore.loading && workspaceStore.currentWorkspaceBoards.length === 0" class="empty-state">
        <el-icon :size="48"><Files /></el-icon>
        <p>В этом пространстве нет досок</p>
        <el-button type="primary" @click="createDialogVisible = true">Создайте первую доску</el-button>
      </div>
    </div>

    <!-- Create Form -->
    <el-dialog v-model="createDialogVisible" title="Новая доска" width="400px">
      <el-form @submit.prevent="handleCreate">
        <el-form-item label="Название доски">
          <el-input v-model="newBoardName" placeholder="например, Проект Альфа" autofocus />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">Отмена</el-button>
          <el-button type="primary" @click="handleCreate" :disabled="!newBoardName.trim()">
            Создать
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkspaceStore } from '../stores/workspace'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft, Delete, Files } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const workspaceStore = useWorkspaceStore()
const workspaceId = Number(route.params.id)

const createDialogVisible = ref(false)
const newBoardName = ref('')

const currentWorkspace = computed(() => {
  return workspaceStore.workspaces.find(w => w.id === workspaceId)
})

onMounted(async () => {
  if (workspaceStore.workspaces.length === 0) {
    await workspaceStore.fetchWorkspaces()
  }
  await workspaceStore.fetchWorkspaceBoards(workspaceId)
})

const goToBoard = (id) => {
  router.push(`/board/${id}`)
}

const handleCreate = async () => {
  if (!newBoardName.value.trim()) return
  try {
    await workspaceStore.createBoard(workspaceId, newBoardName.value.trim())
    createDialogVisible.value = false
    newBoardName.value = ''
    ElMessage.success('Доска создана')
  } catch (e) {
    ElMessage.error('Ошибка создания доски')
  }
}

const confirmDelete = (board) => {
  ElMessageBox.confirm(
    `Вы уверены, что хотите удалить доску "${board.name}"?`,
    'Внимание',
    {
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await workspaceStore.deleteBoard(board.id)
      ElMessage.success('Доска удалена')
    } catch(e) {
      ElMessage.error('Ошибка при удалении доски')
    }
  }).catch(() => {})
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.back-btn {
  padding: 0;
  justify-content: flex-start;
  color: var(--text-secondary);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.boards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.board-card {
  height: 120px;
  padding: 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  background: var(--board-bg);
}

.board-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}

.board-info h3 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
}

.board-actions {
  align-self: flex-end;
  opacity: 0;
  transition: opacity 0.2s;
}

.board-card:hover .board-actions {
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
