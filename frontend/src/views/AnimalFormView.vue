<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { mensagemDeErro } from '../services/api.js'
import { auth } from '../services/auth.js'
import { OPCOES } from '../services/formatos.js'

const MAX_FOTOS = 5
const MAX_BYTES = 5 * 1024 * 1024

const route = useRoute()
const router = useRouter()
const editando = computed(() => Boolean(route.params.id))

const form = reactive({ nome: '', especie: 'cachorro', idade: '', sexo: 'femea', porte: 'medio', descricao: '', fotos: [] })
const carregando = ref(false)
const enviando = ref(false)
const erro = ref('')

const seletor = ref(null)
const subindo = ref(0)
const erroFoto = ref('')

async function escolherFotos(evento) {
  erroFoto.value = ''
  const arquivos = [...evento.target.files].slice(0, MAX_FOTOS - form.fotos.length)
  evento.target.value = ''
  for (const arquivo of arquivos) {
    if (arquivo.size > MAX_BYTES) {
      erroFoto.value = `${arquivo.name} tem mais de 5 MB.`
      continue
    }
    subindo.value++
    try {
      const corpo = new FormData()
      corpo.append('foto', arquivo)
      const { data } = await api.post('/animais/fotos', corpo, { timeout: 60000 })
      form.fotos.push(data.url)
    } catch (e) {
      erroFoto.value = mensagemDeErro(e, `Não foi possível enviar ${arquivo.name}.`)
    } finally {
      subindo.value--
    }
  }
}

function tornarPrincipal(i) {
  form.fotos.unshift(...form.fotos.splice(i, 1))
}

onMounted(async () => {
  if (!editando.value) return
  carregando.value = true
  try {
    const { data } = await api.get(`/animais/${route.params.id}`)
    if (data.anunciante_id !== auth.usuario.anunciante_id) {
      router.replace('/painel')
      return
    }
    Object.assign(form, {
      nome: data.nome, especie: data.especie, idade: data.idade ?? '', sexo: data.sexo,
      porte: data.porte, descricao: data.descricao || '', fotos: [...data.fotos]
    })
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível carregar o animal.')
  } finally {
    carregando.value = false
  }
})

async function salvar() {
  erro.value = ''
  enviando.value = true
  const dados = { ...form }
  try {
    if (editando.value) await api.put(`/animais/${route.params.id}`, dados)
    else await api.post('/animais', dados)
    router.push('/painel')
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível salvar.')
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="section conta">
    <div class="wrap conta-wrap largo">
      <RouterLink class="text-link voltar" to="/painel">← Voltar para meus animais</RouterLink>
      <p v-if="carregando" class="notice">Carregando...</p>

      <form v-else class="card form-card" @submit.prevent="salvar">
        <p class="eyebrow">Painel do anunciante</p>
        <h1>{{ editando ? `Editar ${form.nome || 'animal'}` : 'Cadastrar animal' }}</h1>

        <div class="form-row">
          <label>Nome<input v-model.trim="form.nome" required maxlength="100" /></label>
          <label>Idade em anos (opcional)<input v-model="form.idade" type="number" min="0" max="40" /></label>
        </div>
        <div class="form-row tres">
          <label>Espécie
            <select v-model="form.especie"><option v-for="o in OPCOES.especie" :key="o.valor" :value="o.valor">{{ o.rotulo }}</option></select>
          </label>
          <label>Sexo
            <select v-model="form.sexo"><option v-for="o in OPCOES.sexo" :key="o.valor" :value="o.valor">{{ o.rotulo }}</option></select>
          </label>
          <label>Porte
            <select v-model="form.porte"><option v-for="o in OPCOES.porte" :key="o.valor" :value="o.valor">{{ o.rotulo }}</option></select>
          </label>
        </div>
        <label>
          Descrição (opcional)
          <textarea v-model.trim="form.descricao" rows="4" maxlength="1000" placeholder="Personalidade, cuidados, se é vacinado ou castrado..."></textarea>
        </label>

        <fieldset>
          <legend>Fotos</legend>
          <p class="form-hint esquerda">Até {{ MAX_FOTOS }} fotos (JPG, PNG, WEBP ou GIF, com até 5 MB cada). A principal aparece na lista de animais.</p>

          <div class="fotos-grade">
            <figure v-for="(f, i) in form.fotos" :key="f" class="foto-item">
              <img :src="f" :alt="`Foto ${i + 1}`" />
              <span v-if="i === 0" class="foto-principal">Principal</span>
              <figcaption>
                <button v-if="i > 0" class="link-button" type="button" @click="tornarPrincipal(i)">Tornar principal</button>
                <button class="link-button remover" type="button" @click="form.fotos.splice(i, 1)" :aria-label="`Remover foto ${i + 1}`">Remover</button>
              </figcaption>
            </figure>

            <div v-for="n in subindo" :key="`subindo-${n}`" class="foto-item foto-subindo">Enviando...</div>

            <button v-if="form.fotos.length + subindo < MAX_FOTOS" class="foto-item foto-adicionar" type="button" @click="seletor.click()">
              <span>＋</span>Adicionar foto
            </button>
          </div>
          <input ref="seletor" class="escondido" type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple @change="escolherFotos" />
          <p v-if="erroFoto" class="form-feedback error" role="alert">{{ erroFoto }}</p>
        </fieldset>

        <p v-if="erro" class="form-feedback error" role="alert">{{ erro }}</p>
        <button class="button button-orange full" type="submit" :disabled="enviando || subindo > 0">
          {{ enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Cadastrar animal' }}
        </button>
      </form>
    </div>
  </section>
</template>
