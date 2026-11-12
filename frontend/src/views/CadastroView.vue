<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mensagemDeErro } from '../services/api.js'
import { cadastrar } from '../services/auth.js'
import { buscarCep, buscarCnpj } from '../services/consultas.js'

const route = useRoute()
const router = useRouter()

const form = reactive({
  nome: '', cpf_cnpj: '', telefone: '', data_nascimento: '', email: '', senha: '',
  endereco: { cep: '', rua: '', numero: '', complemento: '', bairro: '', cidade: '', estado: '' }
})
// quem chega pelo link "Quero divulgar um animal" ja vem com a opcao marcada
const divulgar = ref(Boolean(route.query.divulgar))
const anunciante = reactive({ tipo: 'pessoa_fisica', descricao: '' })

const aviso = ref('')
const erro = ref('')
const enviando = ref(false)

async function preencherCep() {
  aviso.value = ''
  if (form.endereco.cep.replace(/\D/g, '').length !== 8) return
  try {
    Object.assign(form.endereco, await buscarCep(form.endereco.cep))
  } catch (e) {
    aviso.value = e.message || 'Não foi possível consultar o CEP. Preencha o endereço manualmente.'
  }
}

async function preencherCnpj() {
  aviso.value = ''
  try {
    const dados = await buscarCnpj(form.cpf_cnpj)
    form.nome = dados.nome
    form.telefone = dados.telefone || form.telefone
    Object.assign(form.endereco, Object.fromEntries(Object.entries(dados.endereco).filter(([, v]) => v)))
    aviso.value = 'Dados preenchidos pelo CNPJ. Confira antes de enviar.'
  } catch {
    aviso.value = 'CNPJ não encontrado. Preencha os dados manualmente.'
  }
}

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    const dados = { ...form, data_nascimento: form.data_nascimento || null }
    if (divulgar.value) dados.anunciante = { ...anunciante }
    await cadastrar(dados)
    const voltar = String(route.query.voltar || '')
    router.push(voltar.startsWith('/') ? voltar : '/')
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível concluir o cadastro.')
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="section conta">
    <div class="wrap conta-wrap largo">
      <form class="card form-card" @submit.prevent="enviar">
        <p class="eyebrow">Crie sua conta</p>
        <h1>Cadastro</h1>

        <label class="check">
          <input v-model="divulgar" type="checkbox" />
          Quero divulgar animais para adoção
        </label>

        <div v-if="divulgar" class="tipo-anunciante" role="radiogroup" aria-label="Tipo de anunciante">
          <label class="radio"><input v-model="anunciante.tipo" type="radio" value="pessoa_fisica" /> Sou pessoa física (tutor ou protetor)</label>
          <label class="radio"><input v-model="anunciante.tipo" type="radio" value="organizacao" /> Sou uma organização (ONG, abrigo, instituição)</label>
        </div>

        <fieldset>
          <legend>Dados pessoais</legend>
          <div class="form-row">
            <label>
              {{ divulgar && anunciante.tipo === 'organizacao' ? 'CNPJ' : 'CPF' }}
              <span class="com-botao">
                <input v-model.trim="form.cpf_cnpj" required maxlength="18" />
                <button v-if="divulgar && anunciante.tipo === 'organizacao'" class="button button-outline" type="button" @click="preencherCnpj">Buscar</button>
              </span>
            </label>
            <label>{{ divulgar && anunciante.tipo === 'organizacao' ? 'Nome da organização' : 'Nome completo' }}<input v-model.trim="form.nome" required maxlength="150" autocomplete="name" /></label>
          </div>
          <div class="form-row">
            <label>Telefone<input v-model.trim="form.telefone" required maxlength="20" type="tel" autocomplete="tel" placeholder="(27) 99999-9999" /></label>
            <label>Data de nascimento (opcional)<input v-model="form.data_nascimento" type="date" /></label>
          </div>
          <label v-if="divulgar">
            Apresentação (opcional)
            <textarea v-model.trim="anunciante.descricao" rows="2" maxlength="500" placeholder="Conte quem você é e como cuida dos animais..."></textarea>
          </label>
        </fieldset>

        <fieldset>
          <legend>Endereço</legend>
          <div class="form-row tres">
            <label>CEP<input v-model.trim="form.endereco.cep" required maxlength="9" placeholder="00000-000" @blur="preencherCep" /></label>
            <label class="dobro">Rua<input v-model.trim="form.endereco.rua" required maxlength="150" /></label>
          </div>
          <div class="form-row tres">
            <label>Número<input v-model.trim="form.endereco.numero" required maxlength="10" placeholder="ou s/n" /></label>
            <label class="dobro">Complemento (opcional)<input v-model.trim="form.endereco.complemento" maxlength="100" /></label>
          </div>
          <div class="form-row tres">
            <label>Bairro<input v-model.trim="form.endereco.bairro" required maxlength="100" /></label>
            <label>Cidade<input v-model.trim="form.endereco.cidade" required maxlength="100" /></label>
            <label>UF<input v-model.trim="form.endereco.estado" required maxlength="2" /></label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Acesso</legend>
          <div class="form-row">
            <label>E-mail<input v-model.trim="form.email" required type="email" maxlength="150" autocomplete="email" /></label>
            <label>Senha<input v-model="form.senha" required type="password" minlength="6" autocomplete="new-password" /></label>
          </div>
        </fieldset>

        <p v-if="aviso" class="form-feedback info" role="status">{{ aviso }}</p>
        <p v-if="erro" class="form-feedback error" role="alert">{{ erro }}</p>
        <button class="button button-orange full" type="submit" :disabled="enviando">{{ enviando ? 'Enviando...' : 'Criar conta' }}</button>
        <p class="form-hint">Já tem conta? <RouterLink class="text-link" :to="{ path: '/entrar', query: route.query }">Entrar</RouterLink></p>
      </form>
    </div>
  </section>
</template>
