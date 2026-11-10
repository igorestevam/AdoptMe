<script setup>
import { especie, sexo, porte, idade, FOTO_PADRAO } from '../services/formatos.js'

defineProps({
  animal: { type: Object, required: true }
})
</script>

<template>
  <article class="pet-card">
    <RouterLink :to="`/animais/${animal.id}`" class="pet-photo">
      <img :src="animal.fotos[0] || FOTO_PADRAO" :alt="`Foto de ${animal.nome}`" loading="lazy" />
      <span class="pet-tag">{{ especie(animal.especie) }}</span>
    </RouterLink>
    <div class="pet-info">
      <div class="pet-title">
        <h3>{{ animal.nome }}</h3>
        <span class="pet-age">{{ idade(animal.idade) }}</span>
      </div>
      <p class="pet-meta">{{ sexo(animal.sexo) }} · Porte {{ porte(animal.porte).toLowerCase() }}</p>
      <p class="pet-description">{{ animal.descricao || 'Sem descrição.' }}</p>
      <RouterLink class="button button-outline full" :to="`/animais/${animal.id}`">Conhecer {{ animal.nome }} <span>→</span></RouterLink>
    </div>
  </article>
</template>
