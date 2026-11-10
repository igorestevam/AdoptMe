import { reactive } from 'vue'
import api from './api.js'

// usuario logado, compartilhado entre as telas
export const auth = reactive({
  usuario: null,
  carregado: false
})

export async function carregarUsuario() {
  try {
    const { data } = await api.get('/auth/me')
    auth.usuario = data
  } catch {
    auth.usuario = null
  } finally {
    auth.carregado = true
  }
}

export async function entrar(email, senha) {
  const { data } = await api.post('/auth/login', { email, senha })
  auth.usuario = data
}

export async function cadastrar(dados) {
  const { data } = await api.post('/auth/register', dados)
  auth.usuario = data
}

export async function sair() {
  await api.post('/auth/logout')
  auth.usuario = null
}
