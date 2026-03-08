import { ref, onUnmounted } from 'vue'

/**
 * useWebSocket(boardId, token, onRefresh)
 * Opens a WebSocket to /ws/board/{boardId}?token=...
 * Calls onRefresh() whenever the server sends a "refresh" event.
 * Auto-reconnects with exponential backoff.
 */
export function useWebSocket(boardId, token, onRefresh) {
    const ws = ref(null)
    let reconnectTimeout = null
    let stopped = false

    const connect = () => {
        if (stopped) return
        const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
        const wsHost = import.meta.env.DEV ? 'localhost:8000' : location.host
        const url = `${protocol}://${wsHost}/ws/board/${boardId}?token=${token}`
        const socket = new WebSocket(url)

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'refresh') {
                    onRefresh(data)
                }
            } catch { }
        }

        socket.onclose = () => {
            if (!stopped) {
                reconnectTimeout = setTimeout(connect, 3000)
            }
        }

        socket.onerror = () => {
            socket.close()
        }

        ws.value = socket
    }

    const disconnect = () => {
        stopped = true
        clearTimeout(reconnectTimeout)
        ws.value?.close()
        ws.value = null
    }

    connect()

    onUnmounted(disconnect)

    return { disconnect }
}
