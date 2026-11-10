<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api, { mensagemDeErro } from '../services/api.js'
import { especie, tipoResponsavel, FOTO_PADRAO } from '../services/formatos.js'

const route = useRoute()
const perfil = ref(null)
const erro = ref('')

const disponiveis = computed(() => perfil.value?.animais.filter((a) => a.situacao === 'disponivel') || [])
const adotados = computed(() => perfil.value?.animais.filter((a) => a.situacao === 'adotado') || [])

watch(() => route.params.id, async (id) => {
  perfil.value = null
  erro.value = ''
  try {
    const { data } = await api.get(`/anunciantes/${id}`)
    perfil.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível carregar este perfil.')
  }
}, { immediate: true })
</script>

<template>
  <section class="section detalhe">
    <div class="wrap">
      <RouterLink class="text-link voltar" to="/">← Voltar para os animais</RouterLink>

      <p v-if="erro" class="notice error">{{ erro }}</p>
      <p v-else-if="!perfil" class="notice">Carregando...</p>

      <template v-else>
        <div class="card perfil-topo">
          <p class="eyebrow">{{ tipoResponsavel(perfil.tipo) }}</p>
          <h1>{{ perfil.nome }}</h1>
          <p v-if="perfil.cidade" class="responsavel-meta">{{ perfil.cidade }}/{{ perfil.estado }}</p>
          <p class="detalhe-descricao">{{ perfil.descricao || 'Sem apresentação.' }}</p>
          <div class="contatos">
            <span>📞 {{ perfil.telefone }}</span>
            <a class="text-link" :href="`mailto:${perfil.email}`">✉ {{ perfil.email }}</a>
          </div>
        </div>

        <h2 class="subtitulo">Disponíveis para adoção ({{ disponiveis.length }})</h2>
        <p v-if="!disponiveis.length" class="notice">Nenhum animal disponível no momento.</p>
        <div v-else class="mini-grid">
          <RouterLink v-for="a in disponiveis" :key="a.id" class="mini-card" :to="`/animais/${a.id}`">
            <img :src="a.foto || FOTO_PADRAO" :alt="`Foto de ${a.nome}`" loading="lazy" />
            <b>{{ a.nome }}</b><small>{{ especie(a.especie) }}</small>
          </RouterLink>
        </div>

        <template v-if="adotados.length">
          <h2 class="subtitulo">Já adotados ({{ adotados.length }})</h2>
          <div class="mini-grid">
            <RouterLink v-for="a in adotados" :key="a.id" class="mini-card adotado" :to="`/animais/${a.id}`">
              <img :src="a.foto || FOTO_PADRAO" :alt="`Foto de ${a.nome}`" loading="lazy" />
              <b>{{ a.nome }}</b><small>{{ especie(a.especie) }}</small>
            </RouterLink>
          </div>
        </template>
      </template>
    </div>
  </section>
</template>
