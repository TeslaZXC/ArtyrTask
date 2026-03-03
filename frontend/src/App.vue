<template>
  <el-config-provider>
    <div class="app-wrapper">
      <header v-if="authStore.isAuthenticated" class="app-header glass-panel">
        <div class="logo">
          <el-icon :size="24" color="var(--primary-color)"><Monitor /></el-icon>
          <h2>ArtyrTask</h2>
        </div>
        <nav class="nav-links">
          <router-link to="/workspaces">Рабочие пространства</router-link>
        </nav>
        <div class="user-actions">
          <span class="user-name">{{ authStore.user?.full_name || authStore.user?.email }}</span>
          <el-button @click="logout" type="danger" text>Выйти</el-button>
        </div>
      </header>
      
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  document.documentElement.classList.add('dark')
  authStore.init()
})

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--glass-border);
  border-radius: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
}

.logo h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  font-weight: 500;
  color: var(--text-secondary);
}

.nav-links a.router-link-active {
  color: var(--primary-color);
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-name {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
