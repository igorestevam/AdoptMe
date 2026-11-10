<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mensagemDeErro } from '../services/api.js'
import { entrar } from '../services/auth.js'

const route = useRoute()
const router = useRouter()
const email = ref('')
const senha = ref('')
const erro = ref('')
const enviando = ref(false)

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    await entrar(email.value, senha.value)
    const voltar = String(route.query.voltar || '')
    router.push(voltar.startsWith('/') ? voltar : '/')
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível entrar.')
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="section conta">
    <div class="wrap conta-wrap">
      <form class="card form-card" @submit.prevent="enviar">
        <p class="eyebrow">Bem-vindo de volta</p>
        <h1>Entrar</h1>
        <label>E-mail<input v-model.trim="email" type="email" required autocomplete="email" /></label>
        <label>Senha<input v-model="senha" type="password" required autocomplete="current-password" /></label>
        <p v-if="erro" class="form-feedback error" role="alert">{{ erro }}</p>
        <button class="button button-dark full" type="submit" :disabled="enviando">{{ enviando ? 'Entrando...' : 'Entrar' }}</button>
        <p class="form-hint">
          Ainda não tem conta?
          <RouterLink class="text-link" :to="{ path: '/cadastro', query: route.query }">Cadastre-se</RouterLink>
        </p>
      </form>
    </div>
  </section>
</template>
