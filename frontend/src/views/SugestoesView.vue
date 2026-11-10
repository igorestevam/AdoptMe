<script setup>
import { ref, computed, onMounted } from 'vue'
import api, { mensagemDeErro } from '../services/api.js'
import ProdutoCard from '../components/ProdutoCard.vue'

const grupos = ref([])
const carregando = ref(true)
const erro = ref('')
const categoria = ref('')

const busca = ref('')
const resultados = ref(null)
const buscando = ref(false)

const visiveis = computed(() => grupos.value.filter((g) => !categoria.value || g.categoria === categoria.value))

onMounted(async () => {
  try {
    const { data } = await api.get('/mercadolivre/sugestoes')
    grupos.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e, 'As sugestões de compras não estão disponíveis no momento.')
  } finally {
    carregando.value = false
  }
})

async function buscar() {
  if (!busca.value) {
    resultados.value = null
    return
  }
  buscando.value = true
  try {
    const { data } = await api.get('/mercadolivre/produtos', { params: { q: busca.value, limit: 12 } })
    resultados.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e)
  } finally {
    buscando.value = false
  }
}
</script>

<template>
  <section class="section sugestoes">
    <div class="wrap">
      <div class="section-heading">
        <p class="eyebrow">Sugestões de compras</p>
        <h2>Tudo para o seu pet, <em>no Mercado Livre.</em></h2>
        <p class="section-lead">Escolha um produto e finalize a compra direto no Mercado Livre. O AdoptMe não processa pagamentos.</p>
      </div>

      <form class="pet-controls" @submit.prevent="buscar">
        <label class="search-box">
          <span aria-hidden="true">⌕</span>
          <input v-model.trim="busca" type="search" placeholder="Buscar produto (ex.: arranhador)" aria-label="Buscar produtos" @search="buscar" />
        </label>
        <div class="filter-pills" role="group" aria-label="Filtrar por categoria">
          <button type="button" :class="{ active: !categoria }" @click="categoria = ''">Todas</button>
          <button v-for="g in grupos" :key="g.categoria" type="button" :class="{ active: categoria === g.categoria }" @click="categoria = g.categoria">
            {{ g.nome }}
          </button>
        </div>
      </form>

      <p v-if="erro" class="notice error">{{ erro }}</p>
      <p v-else-if="carregando || buscando" class="notice">Carregando produtos...</p>

      <template v-else-if="resultados">
        <div class="grupo-head">
          <h3>Resultados para “{{ busca }}”</h3>
          <button class="text-link link-button" type="button" @click="busca = ''; resultados = null">Limpar busca</button>
        </div>
        <p v-if="!resultados.length" class="notice">Nenhum produto encontrado.</p>
        <div v-else class="produto-grid">
          <ProdutoCard v-for="p in resultados" :key="p.id" :produto="p" />
        </div>
      </template>

      <template v-else>
        <div v-for="g in visiveis" :key="g.categoria" class="grupo">
          <div class="grupo-head"><h3>{{ g.nome }}</h3></div>
          <p v-if="!g.produtos.length" class="notice">Nenhum produto nesta categoria agora.</p>
          <div v-else class="produto-grid">
            <ProdutoCard v-for="p in g.produtos" :key="p.id" :produto="p" />
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
