<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import api, { mensagemDeErro } from '../services/api.js'
import { auth } from '../services/auth.js'
import { especie, sexo, porte, idade, tipoResponsavel, FOTO_PADRAO } from '../services/formatos.js'

const route = useRoute()
const animal = ref(null)
const erro = ref('')
const fotoAtual = ref(0)

const mensagem = ref('')
const enviando = ref(false)
const retorno = ref({ tipo: '', texto: '' })

const ehDono = computed(() => Boolean(auth.usuario?.anunciante_id) && auth.usuario.anunciante_id === animal.value?.anunciante_id)
const fotos = computed(() => (animal.value?.fotos.length ? animal.value.fotos : [FOTO_PADRAO]))
const whatsapp = computed(() => {
  const numero = animal.value?.responsavel.telefone.replace(/\D/g, '')
  return numero ? `https://wa.me/55${numero}` : null
})

async function carregar() {
  animal.value = null
  erro.value = ''
  fotoAtual.value = 0
  try {
    const { data } = await api.get(`/animais/${route.params.id}`)
    animal.value = data
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível carregar este animal.')
  }
}

async function enviarInteresse() {
  enviando.value = true
  retorno.value = { tipo: '', texto: '' }
  try {
    await api.post(`/animais/${animal.value.id}/interesses`, { mensagem: mensagem.value })
    mensagem.value = ''
    retorno.value = { tipo: 'success', texto: `Interesse enviado! ${animal.value.responsavel.nome} vai receber seus dados de contato.` }
  } catch (e) {
    retorno.value = { tipo: 'error', texto: mensagemDeErro(e) }
  } finally {
    enviando.value = false
  }
}

watch(() => route.params.id, carregar, { immediate: true })
</script>

<template>
  <section class="section detalhe">
    <div class="wrap">
      <RouterLink class="text-link voltar" to="/">← Voltar para os animais</RouterLink>

      <p v-if="erro" class="notice error">{{ erro }}</p>
      <p v-else-if="!animal" class="notice">Carregando...</p>

      <div v-else class="detalhe-grid">
        <div class="galeria">
          <img class="galeria-principal" :src="fotos[fotoAtual]" :alt="`Foto de ${animal.nome}`" />
          <div v-if="fotos.length > 1" class="galeria-miniaturas">
            <button v-for="(f, i) in fotos" :key="f" type="button" :class="{ ativa: i === fotoAtual }" @click="fotoAtual = i">
              <img :src="f" :alt="`Foto ${i + 1} de ${animal.nome}`" />
            </button>
          </div>
        </div>

        <div class="detalhe-info">
          <p class="eyebrow">{{ especie(animal.especie) }} · {{ animal.situacao === 'adotado' ? 'Já adotado' : 'Disponível para adoção' }}</p>
          <h1>{{ animal.nome }}</h1>
          <ul class="ficha">
            <li><small>Idade</small><b>{{ idade(animal.idade) }}</b></li>
            <li><small>Sexo</small><b>{{ sexo(animal.sexo) }}</b></li>
            <li><small>Porte</small><b>{{ porte(animal.porte) }}</b></li>
          </ul>
          <p class="detalhe-descricao">{{ animal.descricao || 'O responsável ainda não escreveu uma descrição.' }}</p>

          <div class="card responsavel">
            <p class="eyebrow">Quem cuida de {{ animal.nome }}</p>
            <h2>{{ animal.responsavel.nome }}</h2>
            <p class="responsavel-meta">
              {{ tipoResponsavel(animal.responsavel.tipo) }}
              <template v-if="animal.responsavel.cidade"> · {{ animal.responsavel.cidade }}/{{ animal.responsavel.estado }}</template>
            </p>
            <div class="contatos">
              <a v-if="whatsapp" class="button button-dark" :href="whatsapp" target="_blank" rel="noopener">WhatsApp</a>
              <a class="button button-outline" :href="`mailto:${animal.responsavel.email}`">E-mail</a>
              <RouterLink class="text-link" :to="`/responsaveis/${animal.responsavel.id}`">Ver perfil →</RouterLink>
            </div>
          </div>

          <div v-if="ehDono" class="card">
            <p class="form-hint esquerda">Este animal é seu.
              <RouterLink class="text-link" :to="`/painel/animais/${animal.id}/editar`">Editar</RouterLink> ou
              <RouterLink class="text-link" to="/painel">ver no painel</RouterLink>.
            </p>
          </div>
          <form v-else-if="animal.situacao === 'disponivel'" class="card form-card" @submit.prevent="enviarInteresse">
            <h2>Quero adotar {{ animal.nome }}</h2>
            <template v-if="auth.usuario">
              <label>
                Mensagem para o responsável (opcional)
                <textarea v-model.trim="mensagem" rows="3" maxlength="500" placeholder="Conte um pouco sobre você e sua rotina..."></textarea>
              </label>
              <p v-if="retorno.texto" class="form-feedback" :class="retorno.tipo" role="status">{{ retorno.texto }}</p>
              <button class="button button-orange full" type="submit" :disabled="enviando">
                {{ enviando ? 'Enviando...' : 'Manifestar interesse' }}
              </button>
            </template>
            <p v-else class="form-hint">
              <RouterLink class="text-link" :to="{ path: '/entrar', query: { voltar: route.fullPath } }">Entre</RouterLink> ou
              <RouterLink class="text-link" :to="{ path: '/cadastro', query: { voltar: route.fullPath } }">crie uma conta</RouterLink>
              para manifestar interesse.
            </p>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>
