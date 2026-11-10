import { createRouter, createWebHistory } from 'vue-router'
import InicioView from './views/InicioView.vue'
import { auth, carregarUsuario } from './services/auth.js'

const routes = [
  { path: '/', name: 'inicio', component: InicioView },
  { path: '/animais/:id', name: 'animal', component: () => import('./views/AnimalView.vue') },
  { path: '/responsaveis/:id', name: 'responsavel', component: () => import('./views/ResponsavelView.vue') },
  { path: '/sugestoes', name: 'sugestoes', component: () => import('./views/SugestoesView.vue') },
  { path: '/entrar', name: 'entrar', component: () => import('./views/EntrarView.vue') },
  { path: '/cadastro', name: 'cadastro', component: () => import('./views/CadastroView.vue') },
  { path: '/painel', name: 'painel', component: () => import('./views/PainelView.vue'), meta: { anunciante: true } },
  { path: '/painel/animais/novo', name: 'novo-animal', component: () => import('./views/AnimalFormView.vue'), meta: { anunciante: true } },
  { path: '/painel/animais/:id/editar', name: 'editar-animal', component: () => import('./views/AnimalFormView.vue'), meta: { anunciante: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, salvo) {
    return salvo || { top: 0 }
  }
})

// o painel so abre para quem entrou com perfil de anunciante
router.beforeEach(async (to) => {
  if (!to.meta.anunciante) return true
  if (!auth.carregado) await carregarUsuario()
  if (!auth.usuario) return { path: '/entrar', query: { voltar: to.fullPath } }
  if (!auth.usuario.anunciante_id) return '/'
  return true
})

export default router
