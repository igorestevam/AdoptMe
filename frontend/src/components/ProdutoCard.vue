<script setup>
defineProps({
  produto: { type: Object, required: true },
  compacto: { type: Boolean, default: false }
})
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
      <span class="produto-link">Ver no Mercado Livre ↗</span>
    </div>
  </a>
</template>
