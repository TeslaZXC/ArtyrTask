import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useBoardStore = defineStore('board', {
    state: () => ({
        currentBoard: null,
        lists: [],
        tasks: {}, // map of list_id to array of tasks
        loading: false
    }),

    actions: {
        async fetchBoardData(boardId) {
            this.loading = true
            try {
                const boardRes = await api.get(`/boards/${boardId}`)
                this.currentBoard = boardRes.data

                const listsRes = await api.get(`/boards/${boardId}/lists/`)
                this.lists = listsRes.data

                const tasksPromises = this.lists.map(list =>
                    api.get(`/lists/${list.id}/tasks/`)
                )
                const tasksResponses = await Promise.all(tasksPromises)

                this.tasks = {}
                this.lists.forEach((list, index) => {
                    this.tasks[list.id] = tasksResponses[index].data || []
                })
            } finally {
                this.loading = false
            }
        },

        async createList(boardId, name) {
            const response = await api.post(`/boards/${boardId}/lists/`, { name })
            this.lists.push(response.data)
            this.tasks[response.data.id] = []
            return response.data
        },

        async updateListOrder(orderedLists) {
            this.lists = orderedLists
            const items = orderedLists.map((list, index) => ({
                id: list.id,
                position: index
            }))
            await api.patch('/lists/order', items)
        },

        async deleteList(listId) {
            await api.delete(`/lists/${listId}`)
            this.lists = this.lists.filter(l => l.id !== listId)
            delete this.tasks[listId]
        },

        async createTask(listId, title, description = '') {
            const response = await api.post(`/lists/${listId}/tasks/`, {
                title,
                description,
                is_completed: false
            })
            if (!this.tasks[listId]) {
                this.tasks[listId] = []
            }
            this.tasks[listId].push(response.data)
            return response.data
        },

        async updateTaskOrder(listId, tasksInList) {
            this.tasks[listId] = tasksInList
            const items = tasksInList.map((task, index) => ({
                id: task.id,
                list_id: listId,
                position: index
            }))
            await api.patch('/tasks/order', items)
        },

        async moveTaskBetweenLists(taskId, fromListId, toListId, newIndex) {
            const fromTasks = this.tasks[fromListId] || []
            const taskIndex = fromTasks.findIndex(t => t.id === taskId)
            if (taskIndex === -1) return

            const [task] = fromTasks.splice(taskIndex, 1)

            task.list_id = toListId
            if (!this.tasks[toListId]) this.tasks[toListId] = []

            const toTasks = this.tasks[toListId]
            toTasks.splice(newIndex, 0, task)

            const items = [
                ...fromTasks.map((t, idx) => ({ id: t.id, list_id: fromListId, position: idx })),
                ...toTasks.map((t, idx) => ({ id: t.id, list_id: toListId, position: idx }))
            ]

            await api.patch('/tasks/order', items)
        },

        async updateTask(taskId, taskUpdate) {
            const response = await api.put(`/tasks/${taskId}`, taskUpdate)
            const updatedTask = response.data

            const listTasks = this.tasks[updatedTask.list_id]
            if (listTasks) {
                const index = listTasks.findIndex(t => t.id === taskId)
                if (index !== -1) {
                    listTasks[index] = updatedTask
                }
            }
            return updatedTask
        },

        async deleteTask(taskId, listId) {
            await api.delete(`/tasks/${taskId}`)
            if (this.tasks[listId]) {
                this.tasks[listId] = this.tasks[listId].filter(t => t.id !== taskId)
            }
        },

        async uploadAttachment(taskId, file) {
            const formData = new FormData()
            formData.append('file', file)
            const response = await api.post(`/tasks/${taskId}/attachments`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            // Update task in local store
            for (const [listId, tasks] of Object.entries(this.tasks)) {
                const t = tasks.find(t => t.id === taskId)
                if (t) {
                    if (!t.attachments) t.attachments = []
                    t.attachments.push(response.data)
                    break
                }
            }
            return response.data
        },

        async addLink(taskId, url, title) {
            const response = await api.post(`/tasks/${taskId}/links`, { url, title })
            // Update task in local store
            for (const [listId, tasks] of Object.entries(this.tasks)) {
                const t = tasks.find(t => t.id === taskId)
                if (t) {
                    if (!t.links) t.links = []
                    t.links.push(response.data)
                    break
                }
            }
            return response.data
        }
    }
})
