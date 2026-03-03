import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('access_token') || null,
        refreshToken: localStorage.getItem('refresh_token') || null,
        user: JSON.parse(localStorage.getItem('user')) || null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token
    },

    actions: {
        init() {
            // Initialization logic logic if required
        },

        async login(email, password) {
            const formData = new URLSearchParams()
            formData.append('username', email)
            formData.append('password', password)

            const response = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            })

            this.token = response.data.access_token
            this.refreshToken = response.data.refresh_token
            localStorage.setItem('access_token', this.token)
            localStorage.setItem('refresh_token', this.refreshToken)

            this.user = { email }
            localStorage.setItem('user', JSON.stringify(this.user))
        },

        async register(email, password, fullName) {
            await api.post('/auth/register', {
                email,
                password,
                full_name: fullName
            })

            await this.login(email, password)
        },

        logout() {
            this.token = null
            this.refreshToken = null
            this.user = null
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
        }
    }
})
