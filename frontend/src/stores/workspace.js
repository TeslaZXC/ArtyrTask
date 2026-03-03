import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useWorkspaceStore = defineStore('workspace', {
    state: () => ({
        workspaces: [],
        currentWorkspaceBoards: [],
        loading: false
    }),

    actions: {
        async fetchWorkspaces() {
            this.loading = true
            try {
                const response = await api.get('/workspaces/')
                this.workspaces = response.data
            } finally {
                this.loading = false
            }
        },

        async createWorkspace(name) {
            const response = await api.post('/workspaces/', { name })
            this.workspaces.push(response.data)
            return response.data
        },

        async deleteWorkspace(id) {
            await api.delete(`/workspaces/${id}`)
            this.workspaces = this.workspaces.filter(w => w.id !== id)
        },

        async fetchWorkspaceBoards(workspaceId) {
            this.loading = true
            try {
                const response = await api.get(`/workspaces/${workspaceId}/boards/`)
                this.currentWorkspaceBoards = response.data
            } finally {
                this.loading = false
            }
        },

        async createBoard(workspaceId, name) {
            const response = await api.post(`/workspaces/${workspaceId}/boards/`, { name })
            this.currentWorkspaceBoards.push(response.data)
            return response.data
        },

        async deleteBoard(id) {
            await api.delete(`/boards/${id}`)
            this.currentWorkspaceBoards = this.currentWorkspaceBoards.filter(b => b.id !== id)
        }
    }
})
