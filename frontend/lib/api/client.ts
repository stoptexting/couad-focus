import axios from 'axios'

const apiClient = axios.create({
  // Use relative URL for nginx proxy compatibility
  // Local: http://localhost:3000/api → nginx → backend
  // Remote: https://xyz.ngrok.io/api → nginx → backend
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
