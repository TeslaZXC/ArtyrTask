import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
    {
        path: '/',
        redirect: '/workspaces'
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/LoginView.vue'),
        meta: { guest: true }
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('../views/RegisterView.vue'),
        meta: { guest: true }
    },
    {
        path: '/workspaces',
        name: 'Workspaces',
        component: () => import('../views/WorkspacesView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/workspaces/:id/boards',
        name: 'WorkspaceBoards',
        component: () => import('../views/WorkspaceBoardsView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/board/:id',
        name: 'Board',
        component: () => import('../views/BoardView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/task/:id',
        name: 'Task',
        component: () => import('../views/TaskView.vue'),
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()
    // Wait, Pinia in component guard might need to be resolved lazily if store is initialized late. But we call it inside the navigation guard, so it works.
    const isAuthenticated = !!authStore.token

    if (to.meta.requiresAuth && !isAuthenticated) {
        next('/login')
    } else if (to.meta.guest && isAuthenticated) {
        next('/workspaces')
    } else {
        next()
    }
})

export default router
