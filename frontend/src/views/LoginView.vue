<template>
  <div class="auth-page flex-center page-container">
    <div class="auth-card glass-panel">
      <h1 class="auth-title">С возвращением</h1>
      <p class="auth-subtitle">Войдите, чтобы управлять вашими задачами</p>
      
      <el-form :model="form" @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="Email">
          <el-input v-model="form.email" type="email" placeholder="ivan@example.com" />
        </el-form-item>
        
        <el-form-item label="Пароль">
          <el-input v-model="form.password" type="password" show-password placeholder="Введите ваш пароль" />
        </el-form-item>
        
        <el-button type="primary" native-type="submit" :loading="loading" class="submit-btn">
          Войти
        </el-button>
      </el-form>
      
      <div class="auth-footer">
        Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
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

const form = reactive({
  email: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  if (!form.email || !form.password) return
  
  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    ElMessage.success('Успешный вход')
    router.push('/workspaces')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Ошибка при входе')
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

:deep(.el-form-item__label) {
  color: var(--text-primary);
  font-weight: 500;
}
</style>
