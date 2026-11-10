<script setup>
import { ref, onMounted } from 'vue'
import { sortearAnuncio } from '../services/anuncios.js'

defineProps({
  horizontal: { type: Boolean, default: false }
})

const anuncio = ref(null)

onMounted(async () => {
  anuncio.value = await sortearAnuncio()
})
</script>

<template>
  <aside v-if="anuncio" class="anuncio" :class="{ horizontal }" aria-label="Anúncio de empresa parceira">
    <div class="anuncio-texto">
      <small>Patrocinado · {{ anuncio.empresa }}</small>
      <p>{{ anuncio.conteudo }}</p>
    </div>
    <!-- o clique passa pelo backend, que registra para a cobranca e redireciona -->
    <a class="button button-orange" :href="`/api/parceiros/anuncios/${anuncio.id}/clique`" target="_blank" rel="noopener sponsored">
      Saiba mais ↗
    </a>
  </aside>
</template>
