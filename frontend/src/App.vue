<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth, carregarUsuario, sair } from './services/auth.js'

const route = useRoute()
const router = useRouter()
const menuAberto = ref(false)

onMounted(() => { if (!auth.carregado) carregarUsuario() })
watch(() => route.fullPath, () => { menuAberto.value = false })

async function fazerLogout() {
  await sair()
  router.push('/')
}
</script>

<template>
  <header class="site-header">
    <nav class="nav wrap" aria-label="Navegação principal">
      <RouterLink class="brand" to="/"><span class="brand-mark">🐾</span><span>Adopt<span>Me</span></span></RouterLink>
      <button class="menu-toggle" type="button" @click="menuAberto = !menuAberto" :aria-expanded="menuAberto" aria-label="Abrir menu">☰</button>

      <div class="nav-links" :class="{ open: menuAberto }">
        <RouterLink to="/">Animais</RouterLink>
        <RouterLink to="/sugestoes">Sugestões de compras</RouterLink>
        <template v-if="auth.usuario">
          <RouterLink v-if="auth.usuario.anunciante_id" to="/painel">Meus animais</RouterLink>
          <span class="nav-user">Olá, {{ auth.usuario.nome.split(' ')[0] }}</span>
          <button class="link-button" type="button" @click="fazerLogout">Sair</button>
        </template>
        <template v-else-if="auth.carregado">
          <RouterLink to="/entrar">Entrar</RouterLink>
          <RouterLink class="button button-orange nav-cta" to="/cadastro">Criar conta</RouterLink>
        </template>
      </div>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="footer">
    <div class="wrap footer-grid">
      <div>
        <RouterLink class="brand footer-brand" to="/"><span class="brand-mark">🐾</span><span>Adopt<span>Me</span></span></RouterLink>
        <p>Animais para adoção de ONGs, abrigos e protetores, reunidos num só lugar.</p>
      </div>
      <div>
        <h3>Navegue</h3>
        <RouterLink to="/">Animais para adoção</RouterLink>
        <RouterLink to="/sugestoes">Sugestões de compras</RouterLink>
        <RouterLink to="/cadastro">Divulgar um animal</RouterLink>
      </div>
      <div>
        <h3>Compras</h3>
        <p>Os produtos são vendidos no Mercado Livre. O AdoptMe não processa pagamentos.</p>
      </div>
    </div>
    <div class="footer-bottom"><div class="wrap">© {{ new Date().getFullYear() }} AdoptMe · Projeto acadêmico.</div></div>
  </footer>
</template>
