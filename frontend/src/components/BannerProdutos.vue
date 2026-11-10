<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api.js'
import ProdutoCard from './ProdutoCard.vue'

const produtos = ref([])
const estado = ref('carregando') // carregando | ok | erro

onMounted(async () => {
  try {
    const { data } = await api.get('/mercadolivre/destaques')
    produtos.value = data
    estado.value = data.length ? 'ok' : 'erro'
  } catch {
    estado.value = 'erro'
  }
})
</script>

<template>
  <section class="ml-banner" aria-label="Produtos para o seu pet">
    <div class="wrap">
      <div class="ml-banner-head">
        <p><b>O básico para o seu pet</b> <small>Ração, banho, cama e mais no Mercado Livre</small></p>
        <RouterLink class="text-link" to="/sugestoes">Ver todas as sugestões →</RouterLink>
      </div>

      <div v-if="estado === 'carregando'" class="ml-banner-grid">
        <div v-for="n in 4" :key="n" class="produto-card esqueleto"></div>
      </div>
      <div v-else-if="estado === 'ok'" class="ml-banner-grid">
        <ProdutoCard v-for="p in produtos" :key="p.id" :produto="p" compacto />
      </div>
      <p v-else class="ml-banner-vazio">As sugestões de compras não estão disponíveis no momento.</p>
    </div>
  </section>
</template>
