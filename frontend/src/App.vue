<script setup>
// SCAFFOLD INICIAL - a interface definitiva sera baseada no codigo anterior do time.
// Lista os animais disponiveis so para validar a conexao com a API.
import { ref, onMounted } from 'vue'
import api from './services/api.js'

const animais = ref([])
const erro = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/animais')
    animais.value = data
  } catch (e) {
    erro.value = 'Nao foi possivel carregar os animais. O backend esta rodando?'
  }
})
</script>

<template>
  <main style="max-width: 900px; margin: 0 auto; padding: 24px; font-family: system-ui, sans-serif;">
    <h1>AdoptMe</h1>
    <p>Animais disponiveis para adocao</p>

    <p v-if="erro" style="color: #b00;">{{ erro }}</p>
    <p v-else-if="animais.length === 0">Nenhum animal cadastrado ainda.</p>

    <ul>
      <li v-for="a in animais" :key="a.id">
        <strong>{{ a.nome }}</strong> - {{ a.especie }} ({{ a.situacao }})
      </li>
    </ul>
  </main>
</template>
