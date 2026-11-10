<script setup>
import { ref, onMounted } from 'vue'
import api, { mensagemDeErro } from '../services/api.js'
import { especie, idade, FOTO_PADRAO } from '../services/formatos.js'

const animais = ref([])
const carregando = ref(true)
const erro = ref('')
const aviso = ref('')
const interessados = ref({}) // id do animal -> lista (ou null enquanto carrega)

async function carregar() {
  try {
    const { data } = await api.get('/animais/meus')
    animais.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível carregar seus animais.')
  } finally {
    carregando.value = false
  }
}

async function alternarSituacao(animal) {
  const situacao = animal.situacao === 'disponivel' ? 'adotado' : 'disponivel'
  try {
    const { data } = await api.patch(`/animais/${animal.id}/situacao`, { situacao })
    animal.situacao = data.situacao
    aviso.value = situacao === 'adotado' ? `${animal.nome} foi marcado como adotado. 🎉` : `${animal.nome} voltou a ficar disponível.`
  } catch (e) {
    aviso.value = mensagemDeErro(e)
  }
}

async function remover(animal) {
  if (!confirm(`Remover ${animal.nome}? As fotos e os interesses recebidos também serão apagados.`)) return
  try {
    await api.delete(`/animais/${animal.id}`)
    animais.value = animais.value.filter((a) => a.id !== animal.id)
    aviso.value = `${animal.nome} foi removido.`
  } catch (e) {
    aviso.value = mensagemDeErro(e)
  }
}

async function verInteressados(animal) {
  if (animal.id in interessados.value) {
    delete interessados.value[animal.id]
    return
  }
  interessados.value[animal.id] = null
  try {
    const { data } = await api.get(`/animais/${animal.id}/interesses`)
    interessados.value[animal.id] = data
  } catch (e) {
    delete interessados.value[animal.id]
    aviso.value = mensagemDeErro(e)
  }
}

const dataHora = (iso) => new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

onMounted(carregar)
</script>

<template>
  <section class="section painel">
    <div class="wrap">
      <div class="painel-topo">
        <div>
          <p class="eyebrow">Painel do anunciante</p>
          <h1>Meus animais</h1>
        </div>
        <RouterLink class="button button-orange" to="/painel/animais/novo">+ Cadastrar animal</RouterLink>
      </div>

      <p v-if="aviso" class="form-feedback info" role="status">{{ aviso }}</p>
      <p v-if="erro" class="notice error">{{ erro }}</p>
      <p v-else-if="carregando" class="notice">Carregando...</p>
      <div v-else-if="!animais.length" class="notice">
        Você ainda não cadastrou nenhum animal.
        <RouterLink class="text-link" to="/painel/animais/novo">Cadastrar o primeiro</RouterLink>
      </div>

      <ul v-else class="painel-lista">
        <li v-for="a in animais" :key="a.id" class="card painel-item">
          <div class="painel-linha">
            <img :src="a.fotos[0] || FOTO_PADRAO" :alt="`Foto de ${a.nome}`" />
            <div class="painel-dados">
              <RouterLink :to="`/animais/${a.id}`"><h2>{{ a.nome }}</h2></RouterLink>
              <p>{{ especie(a.especie) }} · {{ idade(a.idade) }}</p>
              <span class="selo" :class="a.situacao">{{ a.situacao === 'adotado' ? 'Adotado' : 'Disponível' }}</span>
            </div>
            <div class="painel-acoes">
              <button class="button button-outline" type="button" @click="verInteressados(a)">
                {{ a.interesses }} {{ a.interesses === 1 ? 'interessado' : 'interessados' }}
              </button>
              <button class="button button-outline" type="button" @click="alternarSituacao(a)">
                {{ a.situacao === 'disponivel' ? 'Marcar como adotado' : 'Marcar como disponível' }}
              </button>
              <RouterLink class="button button-outline" :to="`/painel/animais/${a.id}/editar`">Editar</RouterLink>
              <button class="button button-perigo" type="button" @click="remover(a)">Remover</button>
            </div>
          </div>

          <div v-if="a.id in interessados" class="interessados">
            <p v-if="interessados[a.id] === null">Carregando...</p>
            <p v-else-if="!interessados[a.id].length">Ninguém manifestou interesse ainda.</p>
            <ul v-else>
              <li v-for="i in interessados[a.id]" :key="i.id">
                <b>{{ i.nome }}</b> <small>{{ dataHora(i.data_hora) }}</small>
                <p v-if="i.mensagem">“{{ i.mensagem }}”</p>
                <span class="contatos">
                  <a class="text-link" :href="`mailto:${i.email}`">{{ i.email }}</a>
                  <span>{{ i.telefone }}</span>
                </span>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>
