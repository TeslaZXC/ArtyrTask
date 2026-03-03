<template>
  <div class="board-list glass-panel">
    <div class="list-header list-drag-handle">
      <div v-if="!isEditingName" class="list-title" @click="startEditingName">
        <h3>{{ list.name }}</h3>
      </div>
      <el-input
        v-else
        v-model="editName"
        class="title-edit"
        size="small"
        autofocus
        @blur="saveName"
        @keyup.enter="saveName"
        @keyup.esc="cancelEditingName"
      />
      
      <div class="list-actions">
        <!-- More actions dropdown could go here -->
        <el-button text size="small" :icon="Delete" @click="confirmDeleteList" />
      </div>
    </div>
    
    <div class="list-cards">
      <draggable
        v-model="listTasks"
        group="tasks"
        item-key="id"
        class="task-draggable-area"
        ghost-class="ghost-task"
        :animation="200"
        @change="onTaskChange"
      >
        <template #item="{ element: task }">
          <TaskCard :task="task" @click="openTaskModal(task)" />
        </template>
      </draggable>
    </div>
    
    <div class="list-footer">
      <div v-if="!isAddingTask" class="add-task-btn" @click="isAddingTask = true">
        <el-icon><Plus /></el-icon> Добавить карточку
      </div>
      <div v-else class="add-task-form">
        <el-input
          v-model="newTaskTitle"
          type="textarea"
          :rows="2"
          placeholder="Ввести заголовок для карточки..."
          autofocus
          class="task-textarea"
          @keyup.enter.prevent="handleAddTask"
          @keyup.esc="isAddingTask = false"
        />
        <div class="add-task-actions">
          <el-button type="primary" size="small" @click="handleAddTask">Добавить карточку</el-button>
          <el-button text size="small" @click="isAddingTask = false" :icon="Close" />
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import draggable from 'vuedraggable'
import { Plus, Delete, Close } from '@element-plus/icons-vue'
import { useBoardStore } from '../stores/board'
import TaskCard from './TaskCard.vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const props = defineProps({
  list: {
    type: Object,
    required: true
  }
})

const boardStore = useBoardStore()
const router = useRouter()

const isAddingTask = ref(false)
const newTaskTitle = ref('')

const isEditingName = ref(false)
const editName = ref(props.list.name)

const listTasks = computed({
  get: () => boardStore.tasks[props.list.id] || [],
  set: (val) => {
    // Handled by change event primarily
  }
})

const startEditingName = () => {
  editName.value = props.list.name
  isEditingName.value = true
}

const saveName = async () => {
  // Update name logic here
  isEditingName.value = false
}

const cancelEditingName = () => {
  isEditingName.value = false
}

const confirmDeleteList = () => {
  ElMessageBox.confirm(
    'Вы уверены, что хотите удалить этот список? Все задачи будут удалены.',
    'Внимание',
    { type: 'warning' }
  ).then(() => {
    boardStore.deleteList(props.list.id)
  }).catch(() => {})
}

const handleAddTask = async () => {
  if (!newTaskTitle.value.trim()) return
  try {
    await boardStore.createTask(props.list.id, newTaskTitle.value.trim())
    newTaskTitle.value = ''
  } catch (e) {
    ElMessage.error('Ошибка добавления задачи')
  }
}

const onTaskChange = async (evt) => {
  if (evt.added) {
    await boardStore.moveTaskBetweenLists(
      evt.added.element.id,
      evt.added.element.list_id,
      props.list.id,
      evt.added.newIndex
    )
  } else if (evt.moved) {
    const newArray = [...boardStore.tasks[props.list.id]]
    const element = newArray.splice(evt.moved.oldIndex, 1)[0]
    newArray.splice(evt.moved.newIndex, 0, element)
    await boardStore.updateTaskOrder(props.list.id, newArray)
  }
}

const openTaskModal = (task) => {
  // Navigate to task detail route
  router.push(`/task/${task.id}`)
}
</script>

<style scoped>
.board-list {
  background: var(--surface-color);
  border-radius: 12px;
  width: 280px;
  min-width: 280px;
  max-height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: grab;
  color: var(--text-primary);
}

.list-header:active {
  cursor: grabbing;
}

.list-title h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.title-edit {
  width: 100%;
  margin-right: 0.5rem;
}

.list-cards {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem;
  min-height: 20px;
}

.task-draggable-area {
  min-height: 10px;
  padding-bottom: 0.5rem;
}

.list-footer {
  padding: 0.5rem 1rem 1rem;
}

.add-task-btn {
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s, color 0.2s;
}

.add-task-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.add-task-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-textarea {
  font-size: 0.9rem;
}

.add-task-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ghost-task {
  opacity: 0.4;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}
</style>
