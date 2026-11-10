import axios from 'axios'

const api = axios.create({
  baseURL: '/api',   // proxy do Vite encaminha para http://localhost:5000
  timeout: 8000
})

export function mensagemDeErro(e, padrao = 'Algo deu errado. Tente novamente.') {
  return e.response?.data?.erro || padrao
}

export default api
