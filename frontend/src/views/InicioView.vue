<script setup>
import { ref, watch, onMounted } from 'vue'
import api, { mensagemDeErro } from '../services/api.js'
import BannerProdutos from '../components/BannerProdutos.vue'
import AnimalCard from '../components/AnimalCard.vue'

const animais = ref([])
const carregando = ref(true)
const erro = ref('')
const busca = ref('')
const especie = ref('')

const FILTROS = [
  { valor: '', rotulo: 'Todos' },
  { valor: 'cachorro', rotulo: '🐶 Cães' },
  { valor: 'gato', rotulo: '🐱 Gatos' }
]

async function carregar() {
  carregando.value = true
  erro.value = ''
  try {
    const params = { situacao: 'disponivel', q: busca.value || undefined, especie: especie.value || undefined }
    const { data } = await api.get('/animais', { params })
    animais.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível carregar os animais. O backend está rodando?')
  } finally {
    carregando.value = false
  }
}

// espera a pessoa parar de digitar antes de buscar
let espera
watch(busca, () => {
  clearTimeout(espera)
  espera = setTimeout(carregar, 300)
})
watch(especie, carregar)
onMounted(carregar)
</script>

<template>
  <BannerProdutos />

  <section class="hero">
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">Adoção responsável de cães e gatos</p>
        <h1>Adote e mude <em>duas vidas.</em></h1>
        <p class="hero-lead">
          Animais de ONGs, abrigos e protetores reunidos num só lugar. Conheça cada um, veja quem cuida dele
          e fale direto com o responsável.
        </p>
        <div class="hero-actions">
          <a class="button button-orange" href="#animais">Conhecer os animais <span>→</span></a>
          <RouterLink class="text-link" to="/cadastro">Quero divulgar um animal</RouterLink>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-image-frame">
          <img src="https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=900&q=80" alt="Cachorro olhando com carinho" />
        </div>
      </div>
    </div>
  </section>

  <section id="animais" class="section section-pets">
    <div class="wrap">
      <div class="section-heading">
        <p class="eyebrow">Esperando por um lar</p>
        <h2>Animais <em>disponíveis</em> para adoção</h2>
      </div>

      <div class="pet-controls">
        <label class="search-box">
          <span aria-hidden="true">⌕</span>
          <input v-model.trim="busca" type="search" placeholder="Buscar por nome ou característica..." aria-label="Buscar animais" />
        </label>
        <div class="filter-pills" role="group" aria-label="Filtrar por espécie">
          <button v-for="f in FILTROS" :key="f.valor" type="button" :class="{ active: especie === f.valor }" @click="especie = f.valor">
            {{ f.rotulo }}
          </button>
        </div>
      </div>

      <p v-if="erro" class="notice error">{{ erro }}</p>
      <p v-else-if="carregando && !animais.length" class="notice">Carregando os animais...</p>
      <p v-else-if="!animais.length" class="notice">Nenhum animal encontrado com esse filtro. 🐾</p>
      <div v-else class="pet-grid">
        <AnimalCard v-for="a in animais" :key="a.id" :animal="a" />
      </div>
    </div>
  </section>
</template>
