import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
    state: () => ({
        currentTheme: localStorage.getItem('app-theme') || 'light',
        themes: [
            { id: 'dark', name: 'Тёмная' },
            { id: 'light', name: 'Светлая' },
            { id: 'neon', name: 'Неоновая' },
            { id: 'summer', name: 'Летняя' },
            { id: 'ocean', name: 'Океан' },
            { id: 'sunset', name: 'Закат' }
        ]
    }),

    actions: {
        initTheme() {
            this.applyTheme(this.currentTheme)
        },

        setTheme(themeId) {
            this.currentTheme = themeId
            localStorage.setItem('app-theme', themeId)
            this.applyTheme(themeId)
        },

        applyTheme(themeId) {
            // Remove dark class mapping if it exists, use data-theme instead
            document.documentElement.classList.remove('dark')
            document.documentElement.setAttribute('data-theme', themeId)

            // For older Element Plus components or tailwind standard that looks for class="dark"
            if (themeId === 'dark') {
                document.documentElement.classList.add('dark')
            }
        }
    }
})
