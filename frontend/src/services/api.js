import axios from 'axios'
import router from '../router'

export const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json'
    }
})

api.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            // In a real app we'd try to use refresh_token here,
            // but for simplicity we log the user out
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            if (router.currentRoute.value.path !== '/login') {
                router.push('/login')
            }
        }
        return Promise.reject(error)
    }
)
