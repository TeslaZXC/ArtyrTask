<template>
  <div class="auth-page flex-center page-container">
    <div class="auth-card glass-panel">
      <h1 class="auth-title">Сброс пароля</h1>
      <p class="auth-subtitle">Восстановите доступ к аккаунту с помощью почты</p>
      
      <el-form :model="form" @submit.prevent="step === 1 ? handleRequestResetCode() : handleResetPassword()" label-position="top">
        
        <!-- Step 1: Request Code -->
        <template v-if="step === 1">
          <el-form-item label="Email">
            <el-input v-model="form.email" type="email" placeholder="ivan@example.com" />
          </el-form-item>

          <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn" :disabled="!form.email">
            Отправить код
          </el-button>
        </template>

        <!-- Step 2: Code and New Password -->
        <template v-else>
          <div class="email-info">
            Код отправлен на <strong>{{ form.email }}</strong>
            <el-button type="primary" link @click="step = 1" class="edit-link">Изменить</el-button>
          </div>

          <el-form-item label="Код подтверждения">
            <el-input v-model="form.code" placeholder="123456" />
          </el-form-item>
          
          <el-form-item label="Новый пароль">
            <el-input v-model="form.newPassword" type="password" show-password placeholder="Введите новый пароль" />
          </el-form-item>
          
          <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn" :disabled="!form.code || !form.newPassword">
            Сбросить пароль
          </el-button>
        </template>
      </el-form>
      
      <div class="auth-footer">
        Вспомнили пароль? <router-link to="/login">Вернуться ко входу</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const step = ref(1)
const loading = ref(false)

const form = reactive({
  email: '',
  code: '',
  newPassword: ''
})

const handleRequestResetCode = async () => {
  if (!form.email) return
  
  loading.value = true
  try {
    await authStore.requestResetCode(form.email)
    ElMessage.success('Код для сброса отправлен на почту')
    step.value = 2
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Произошла ошибка')
  } finally {
    loading.value = false
  }
}

const handleResetPassword = async () => {
  if (!form.email || !form.code || !form.newPassword) return
  
  loading.value = true
  try {
    await authStore.resetPassword(form.email, form.code, form.newPassword)
    ElMessage.success('Пароль успешно изменён! Теперь вы можете войти.')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Неверный код или ошибка сервера')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 60px);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 3rem 2.5rem;
  border-radius: 16px;
  text-align: center;
}

.auth-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.auth-subtitle {
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.submit-btn {
  width: 100%;
  margin-top: 1rem;
  height: 44px;
  font-size: 1rem;
  font-weight: 500;
}

.auth-footer {
  margin-top: 2rem;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.email-info {
  margin-bottom: 1.5rem;
  text-align: left;
  font-size: 0.9rem;
  color: var(--text-primary);
  background: rgba(var(--el-color-primary-rgb), 0.1);
  padding: 12px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.edit-link {
  font-size: 0.85rem;
}

:deep(.el-form-item__label) {
  color: var(--text-primary);
  font-weight: 500;
}
</style>
