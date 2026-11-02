import axios from 'axios'

const api = axios.create({
  baseURL: '/api',   // proxy do Vite encaminha para http://localhost:5000
  timeout: 8000
})

export default api
