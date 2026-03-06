import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useWorkspaceStore = defineStore('workspace', {
    state: () => ({
        workspaces: [],
        currentWorkspaceBoards: [],
        members: [],
        currentRole: null,   // 'owner' | 'editor' | 'member'
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
                // Set current role from workspace data
                const ws = this.workspaces.find(w => w.id === workspaceId)
                this.currentRole = ws?.member_role || null
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
        },

        // Member management
        async fetchMembers(workspaceId) {
            const response = await api.get(`/workspaces/${workspaceId}/members/`)
            this.members = response.data
            return response.data
        },

        async addMember(workspaceId, email, role) {
            const response = await api.post(`/workspaces/${workspaceId}/members/`, { email, role })
            this.members.push(response.data)
            return response.data
        },

        async updateMember(workspaceId, userId, role) {
            const response = await api.put(`/workspaces/${workspaceId}/members/${userId}`, { email: '', role })
            const idx = this.members.findIndex(m => m.user_id === userId)
            if (idx !== -1) this.members[idx] = response.data
            return response.data
        },

        async removeMember(workspaceId, userId) {
            await api.delete(`/workspaces/${workspaceId}/members/${userId}`)
            this.members = this.members.filter(m => m.user_id !== userId)
        }
    }
})
