<script setup>
defineProps({
  produto: { type: Object, required: true },
  compacto: { type: Boolean, default: false }
})

const reais = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
</script>

<template>
  <a class="produto-card" :class="{ compacto }" :href="produto.link" target="_blank" rel="noopener noreferrer">
    <div class="produto-foto">
      <img v-if="produto.foto" :src="produto.foto" :alt="produto.nome" loading="lazy" />
      <span v-else>🛍️</span>
    </div>
    <div class="produto-info">
      <small v-if="produto.categoria">{{ produto.categoria }}</small>
      <p>{{ produto.nome }}</p>
      <!-- o preco é o menor entre os anuncios do produto no Mercado Livre -->
      <span v-if="produto.preco != null" class="produto-preco"><small>a partir de</small> {{ reais.format(produto.preco) }}</span>
      <span class="produto-link">Ver no Mercado Livre ↗</span>
    </div>
  </a>
</template>
