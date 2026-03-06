<template>
  <div class="page-container members-page">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="router.back()" :icon="ArrowLeft" class="back-btn">
          Назад к доскам
        </el-button>
        <h1 class="page-title">Участники пространства</h1>
      </div>
    </div>

    <!-- Add member form (owner only) -->
    <div v-if="isOwner" class="add-member-card glass-panel">
      <h3>Добавить участника</h3>
      <div class="add-member-form">
        <el-input
          v-model="inviteEmail"
          placeholder="Email пользователя"
          class="email-input"
          @keyup.enter="handleAddMember"
        />
        <el-select v-model="inviteRole" style="width: 160px">
          <el-option label="Редактор" value="editor" />
          <el-option label="Участник" value="member" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="handleAddMember" :loading="adding">
          Добавить
        </el-button>
      </div>
      <div class="role-description">
        <span v-if="inviteRole === 'editor'">
          <strong>Редактор</strong> — может создавать доски, списки и задачи
        </span>
        <span v-else>
          <strong>Участник</strong> — может только отмечать задачи как выполненные
        </span>
      </div>
    </div>

    <!-- Members list -->
    <div v-loading="loading" class="members-list">
      <!-- Owner row -->
      <div class="member-row glass-panel owner-row">
        <div class="member-avatar" style="background: rgba(99,102,241,0.3)">
          <el-icon :size="22"><UserFilled /></el-icon>
        </div>
        <div class="member-info">
          <span class="member-name">{{ ownerWorkspace?.owner_email || 'Вы (владелец)' }}</span>
          <span class="member-email">{{ currentUserEmail }}</span>
        </div>
        <el-tag type="warning" round>Владелец</el-tag>
      </div>

      <!-- Regular members -->
      <div
        v-for="member in workspaceStore.members"
        :key="member.user_id"
        class="member-row glass-panel"
      >
        <div class="member-avatar">
          <el-icon :size="22"><User /></el-icon>
        </div>
        <div class="member-info">
          <span class="member-name">{{ member.full_name || member.email }}</span>
          <span class="member-email">{{ member.email }}</span>
        </div>

        <el-select
          v-if="isOwner"
          :model-value="member.role"
          @change="val => handleRoleChange(member.user_id, val)"
          style="width: 140px"
          size="small"
        >
          <el-option label="Редактор" value="editor" />
          <el-option label="Участник" value="member" />
        </el-select>
        <el-tag v-else :type="member.role === 'editor' ? 'success' : 'info'" round>
          {{ member.role === 'editor' ? 'Редактор' : 'Участник' }}
        </el-tag>

        <el-button
          v-if="isOwner"
          type="danger"
          text
          :icon="Delete"
          @click="handleRemove(member)"
          size="small"
        />
      </div>

      <div v-if="!loading && workspaceStore.members.length === 0" class="empty-members">
        <el-icon :size="40"><UserFilled /></el-icon>
        <p>В этом пространстве пока только вы</p>
        <p class="hint">Добавьте участников выше, чтобы совместно работать</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkspaceStore } from '../stores/workspace'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Delete, User, UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const workspaceStore = useWorkspaceStore()
const authStore = useAuthStore()
const workspaceId = Number(route.params.id)

const inviteEmail = ref('')
const inviteRole = ref('member')
const loading = ref(false)
const adding = ref(false)

const currentUserEmail = computed(() => authStore.user?.email)
const isOwner = computed(() => {
  const ws = workspaceStore.workspaces.find(w => w.id === workspaceId)
  return ws?.member_role === 'owner'
})

onMounted(async () => {
  if (workspaceStore.workspaces.length === 0) {
    await workspaceStore.fetchWorkspaces()
  }
  loading.value = true
  try {
    await workspaceStore.fetchMembers(workspaceId)
  } finally {
    loading.value = false
  }
})

const handleAddMember = async () => {
  if (!inviteEmail.value.trim()) return
  adding.value = true
  try {
    await workspaceStore.addMember(workspaceId, inviteEmail.value.trim(), inviteRole.value)
    inviteEmail.value = ''
    ElMessage.success('Участник добавлен')
  } catch (e) {
    const detail = e.response?.data?.detail || 'Ошибка добавления участника'
    ElMessage.error(detail)
  } finally {
    adding.value = false
  }
}

const handleRoleChange = async (userId, newRole) => {
  try {
    await workspaceStore.updateMember(workspaceId, userId, newRole)
    ElMessage.success('Роль обновлена')
  } catch {
    ElMessage.error('Ошибка обновления роли')
  }
}

const handleRemove = (member) => {
  ElMessageBox.confirm(
    `Удалить ${member.full_name || member.email} из пространства?`,
    'Подтверждение',
    { confirmButtonText: 'Удалить', cancelButtonText: 'Отмена', type: 'warning' }
  ).then(async () => {
    try {
      await workspaceStore.removeMember(workspaceId, member.user_id)
      ElMessage.success('Участник удалён')
    } catch {
      ElMessage.error('Ошибка удаления участника')
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

.add-member-card {
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.add-member-card h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.add-member-form {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.email-input {
  flex: 1;
}

.role-description {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: 10px;
}

.owner-row {
  border-color: rgba(99, 102, 241, 0.3);
}

.member-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.member-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.member-email {
  font-size: 0.825rem;
  color: var(--text-secondary);
}

.empty-members {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 2rem;
  color: var(--text-secondary);
  background: var(--glass-bg);
  border-radius: 12px;
  border: 1px dashed var(--border-color);
  gap: 0.5rem;
}

.empty-members p {
  margin: 0;
  font-size: 1rem;
}

.hint {
  font-size: 0.85rem !important;
  opacity: 0.7;
}
</style>
