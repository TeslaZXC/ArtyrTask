<template>
  <div class="task-card">
    <div class="task-header">
      <h4 :class="{ 'completed': task.is_completed }">{{ task.title }}</h4>
      <el-checkbox 
        v-model="isCompleted" 
        @click.stop 
        @change="toggleComplete"
        size="large"
      />
    </div>
    
    <div class="task-meta" v-if="hasMeta">
      <div v-if="task.description" class="meta-item" title="У этой задачи есть описание">
        <el-icon><Document /></el-icon>
      </div>
      <div v-if="task.attachments?.length" class="meta-item" title="Вложения">
        <el-icon><Paperclip /></el-icon> {{ task.attachments.length }}
      </div>
      <div v-if="task.links?.length" class="meta-item" title="Ссылки">
        <el-icon><Link /></el-icon> {{ task.links.length }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document, Paperclip, Link } from '@element-plus/icons-vue'
import { useBoardStore } from '../stores/board'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const boardStore = useBoardStore()

const hasMeta = computed(() => {
  return props.task.description || 
         (props.task.attachments && props.task.attachments.length > 0) || 
         (props.task.links && props.task.links.length > 0)
})

const isCompleted = computed({
  get: () => props.task.is_completed,
  set: (val) => {
    // toggleComplete handles API call
  }
})

const toggleComplete = async (checked) => {
  await boardStore.updateTask(props.task.id, { is_completed: checked })
}
</script>

<style scoped>
.task-card {
  background: var(--surface-hover);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
}

.task-card:hover {
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}

.task-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  word-break: break-word;
  line-height: 1.4;
}

.task-header h4.completed {
  text-decoration: line-through;
  color: var(--text-secondary);
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.75rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

:deep(.el-checkbox) {
  height: auto;
  margin-right: -4px;
}
</style>
