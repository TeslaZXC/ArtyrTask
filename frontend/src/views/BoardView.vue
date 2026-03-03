<template>
  <div class="board-page">
    <div class="board-header glass-panel">
      <div class="header-left">
        <el-button text @click="goBack" :icon="ArrowLeft" class="back-btn">
          Назад
        </el-button>
        <h1 class="board-title">{{ currentBoard?.name || 'Доска' }}</h1>
      </div>
    </div>

    <div class="board-canvas" v-loading="boardStore.loading">
      <draggable
        v-model="boardLists"
        group="lists"
        item-key="id"
        class="lists-container"
        handle=".list-drag-handle"
        @end="onListDragEnd"
        ghost-class="ghost-list"
        :animation="200"
      >
        <template #item="{ element: list }">
          <BoardList :list="list" />
        </template>
        
        <template #footer>
          <div class="add-list-wrapper">
            <div v-if="!isAddingList" class="add-list-btn glass-panel" @click="isAddingList = true">
              <el-icon><Plus /></el-icon> Добавить список
            </div>
            <div v-else class="add-list-form glass-panel">
              <el-input
                v-model="newListTitle"
                placeholder="Ввести заголовок списка..."
                autofocus
                @keyup.enter="handleAddList"
                @keyup.esc="isAddingList = false"
              />
              <div class="add-list-actions">
                <el-button type="primary" size="small" @click="handleAddList">Добавить список</el-button>
                <el-button text size="small" @click="isAddingList = false" :icon="Close" />
              </div>
            </div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useBoardStore } from '../stores/board'
import { useWorkspaceStore } from '../stores/workspace'
import draggable from 'vuedraggable'
import BoardList from '../components/BoardList.vue'
import { ArrowLeft, Plus, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const boardStore = useBoardStore()
const workspaceStore = useWorkspaceStore()
const boardId = Number(route.params.id)

const isAddingList = ref(false)
const newListTitle = ref('')

const currentBoard = computed(() => boardStore.currentBoard)

const boardLists = computed({
  get: () => boardStore.lists,
  set: (val) => {
    boardStore.lists = val
  }
})

onMounted(async () => {
  await boardStore.fetchBoardData(boardId)
})

const goBack = () => {
  if (currentBoard.value) {
    router.push(`/workspaces/${currentBoard.value.workspace_id}/boards`)
  } else {
    router.push('/workspaces')
  }
}

const handleAddList = async () => {
  if (!newListTitle.value.trim()) return
  try {
    await boardStore.createList(boardId, newListTitle.value.trim())
    newListTitle.value = ''
    isAddingList.value = false
  } catch (e) {
    ElMessage.error('Ошибка создания списка')
  }
}

const onListDragEnd = async () => {
  try {
    await boardStore.updateListOrder(boardStore.lists)
  } catch (e) {
    ElMessage.error('Ошибка сохранения порядка списков')
  }
}
</script>

<style scoped>
.board-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  background: var(--board-bg);
}

.board-header {
  height: 50px;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(8px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  color: var(--text-secondary);
}

.board-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.board-canvas {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 1rem;
}

.lists-container {
  display: flex;
  align-items: flex-start;
  height: 100%;
  gap: 1rem;
  padding-bottom: 1rem; /* for scrollbar */
}

/* Add List */
.add-list-wrapper {
  min-width: 280px;
  width: 280px;
  flex-shrink: 0;
}

.add-list-btn {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.2s;
}

.add-list-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.add-list-form {
  padding: 0.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.add-list-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ghost-list {
  opacity: 0.4;
  background: rgba(255,255,255,0.05);
}
</style>
