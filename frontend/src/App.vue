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
        <div class="header-actions">
          <el-dropdown trigger="click" @command="themeStore.setTheme">
            <span class="el-dropdown-link theme-selector">
              <el-icon><Brush /></el-icon>
              {{ themeStore.themes.find(t => t.id === themeStore.currentTheme)?.name }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="theme in themeStore.themes" 
                  :key="theme.id" 
                  :command="theme.id"
                  :disabled="themeStore.currentTheme === theme.id"
                >
                  {{ theme.name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <div class="user-actions">
            <span class="user-name">{{ authStore.user?.full_name || authStore.user?.email }}</span>
            <el-button @click="logout" type="danger" text>Выйти</el-button>
          </div>
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
import { useThemeStore } from './stores/theme'
import { Brush, ArrowDown, Monitor } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

onMounted(() => {
  themeStore.initTheme()
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.theme-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 0.9rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.theme-selector:hover {
  background: rgba(var(--primary-color-rgb), 0.1);
  color: var(--primary-color);
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  border-left: 1px solid var(--border-color);
  padding-left: 1.5rem;
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
