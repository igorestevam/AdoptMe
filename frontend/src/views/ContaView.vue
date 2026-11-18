<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api, { mensagemDeErro } from '../services/api.js'
import { auth } from '../services/auth.js'
import { buscarCep } from '../services/consultas.js'

const ENDERECO_VAZIO = { cep: '', rua: '', numero: '', complemento: '', bairro: '', cidade: '', estado: '' }

const conta = ref(null)
const form = reactive({ nome: '', telefone: '', data_nascimento: '', endereco: { ...ENDERECO_VAZIO } })
const divulgar = ref(false)
const descricao = ref('')

const carregando = ref(true)
const erroCarga = ref('')
const editando = ref(false)
const salvando = ref(false)
const aviso = ref('')
const erro = ref('')
const sucesso = ref('')

const senhaAberta = ref(false)
const senha = reactive({ atual: '', nova: '', confirmacao: '' })
const trocando = ref(false)
const erroSenha = ref('')
const sucessoSenha = ref('')

const ehOrganizacao = computed(() => conta.value?.cpf_cnpj.length > 14)
const iniciais = computed(() => {
  const partes = (conta.value?.nome || '').trim().split(/\s+/)
  return ((partes[0]?.[0] || '') + (partes.length > 1 ? partes.at(-1)[0] : '')).toUpperCase()
})
const perfil = computed(() => {
  const a = conta.value?.anunciante
  if (!a) return 'Adotante'
  return a.tipo === 'organizacao' ? 'Anunciante · Organização' : 'Anunciante · Pessoa física'
})
const nascimentoFormatado = computed(() =>
  form.data_nascimento ? form.data_nascimento.split('-').reverse().join('/') : '')

function preencher(dados) {
  conta.value = dados
  const endereco = Object.fromEntries(Object.entries(dados.endereco || {}).map(([k, v]) => [k, v ?? '']))
  Object.assign(form, {
    nome: dados.nome,
    telefone: dados.telefone,
    data_nascimento: dados.data_nascimento || '',
    endereco: { ...ENDERECO_VAZIO, ...endereco }
  })
  divulgar.value = Boolean(dados.anunciante)
  descricao.value = dados.anunciante?.descricao || ''
}

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/conta')
    preencher(data)
  } catch (e) {
    erroCarga.value = mensagemDeErro(e, 'Não foi possível carregar seus dados.')
  } finally {
    carregando.value = false
  }
})

function editar() {
  sucesso.value = ''
  editando.value = true
}

function cancelar() {
  preencher(conta.value)
  erro.value = ''
  aviso.value = ''
  editando.value = false
}

async function preencherCep() {
  aviso.value = ''
  if (!editando.value || form.endereco.cep.replace(/\D/g, '').length !== 8) return
  try {
    Object.assign(form.endereco, await buscarCep(form.endereco.cep))
  } catch (e) {
    aviso.value = e.message || 'Não foi possível consultar o CEP. Preencha o endereço manualmente.'
  }
}

async function salvar() {
  erro.value = ''
  salvando.value = true
  try {
    const dados = { ...form, data_nascimento: form.data_nascimento || null }
    if (divulgar.value) dados.anunciante = { descricao: descricao.value }
    const { data } = await api.put('/auth/conta', dados)
    const virouAnunciante = !conta.value.anunciante && data.anunciante
    preencher(data)
    auth.usuario = { ...auth.usuario, nome: data.nome, telefone: data.telefone, anunciante_id: data.anunciante_id }
    editando.value = false
    aviso.value = ''
    sucesso.value = virouAnunciante
      ? 'Dados salvos. Agora você já pode cadastrar animais em "Meus animais".'
      : 'Dados salvos.'
  } catch (e) {
    erro.value = mensagemDeErro(e, 'Não foi possível salvar os dados.')
  } finally {
    salvando.value = false
  }
}

function fecharSenha() {
  Object.assign(senha, { atual: '', nova: '', confirmacao: '' })
  erroSenha.value = ''
  senhaAberta.value = false
}

async function trocarSenha() {
  erroSenha.value = ''
  if (senha.nova !== senha.confirmacao) {
    erroSenha.value = 'A confirmação não confere com a nova senha.'
    return
  }
  trocando.value = true
  try {
    await api.put('/auth/senha', { senha_atual: senha.atual, nova_senha: senha.nova })
    fecharSenha()
    sucessoSenha.value = 'Senha alterada.'
  } catch (e) {
    erroSenha.value = mensagemDeErro(e, 'Não foi possível trocar a senha.')
  } finally {
    trocando.value = false
  }
}
</script>

<template>
  <section class="section conta">
    <div class="wrap conta-wrap largo">
      <p v-if="carregando" class="notice">Carregando...</p>
      <p v-else-if="erroCarga" class="form-feedback error" role="alert">{{ erroCarga }}</p>

      <template v-else>
        <div class="card conta-topo">
          <span class="conta-avatar" aria-hidden="true">{{ iniciais }}</span>
          <div class="conta-quem">
            <p class="eyebrow">Minha conta</p>
            <h1>{{ conta.nome }}</h1>
            <span class="selo">{{ perfil }}</span>
          </div>
          <button v-if="!editando" class="button button-dark" type="button" @click="editar">
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm17.7-10.2a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
            Editar dados
          </button>
        </div>

        <p v-if="sucesso" class="form-feedback success conta-msg" role="status">{{ sucesso }}</p>

        <form class="card form-card conta-form" :class="{ lendo: !editando }" @submit.prevent="salvar">
          <fieldset>
            <legend>Dados pessoais</legend>
            <div class="form-row">
              <label class="bloqueado">
                <span>E-mail <small>não pode ser alterado</small></span>
                <input :value="conta.email" readonly tabindex="-1" />
              </label>
              <label class="bloqueado">
                <span>{{ ehOrganizacao ? 'CNPJ' : 'CPF' }} <small>não pode ser alterado</small></span>
                <input :value="conta.cpf_cnpj" readonly tabindex="-1" />
              </label>
            </div>
            <div class="form-row">
              <label>{{ ehOrganizacao ? 'Nome da organização' : 'Nome completo' }}<input v-model.trim="form.nome" :readonly="!editando" required maxlength="150" autocomplete="name" /></label>
              <label>Telefone<input v-model.trim="form.telefone" :readonly="!editando" required maxlength="20" type="tel" autocomplete="tel" /></label>
            </div>
            <label v-if="editando">Data de nascimento (opcional)<input v-model="form.data_nascimento" type="date" /></label>
            <label v-else>Data de nascimento<input :value="nascimentoFormatado" readonly placeholder="Não informada" /></label>
          </fieldset>

          <fieldset>
            <legend>Endereço</legend>
            <div class="form-row tres">
              <label>CEP<input v-model.trim="form.endereco.cep" :readonly="!editando" required maxlength="9" placeholder="00000-000" @blur="preencherCep" /></label>
              <label class="dobro">Rua<input v-model.trim="form.endereco.rua" :readonly="!editando" required maxlength="150" /></label>
            </div>
            <div class="form-row tres">
              <label>Número<input v-model.trim="form.endereco.numero" :readonly="!editando" required maxlength="10" /></label>
              <label class="dobro">Complemento<input v-model.trim="form.endereco.complemento" :readonly="!editando" maxlength="100" :placeholder="editando ? 'Opcional' : 'Não informado'" /></label>
            </div>
            <div class="form-row tres">
              <label>Bairro<input v-model.trim="form.endereco.bairro" :readonly="!editando" required maxlength="100" /></label>
              <label>Cidade<input v-model.trim="form.endereco.cidade" :readonly="!editando" required maxlength="100" /></label>
              <label>UF<input v-model.trim="form.endereco.estado" :readonly="!editando" required maxlength="2" /></label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Divulgação de animais</legend>
            <label v-if="!conta.anunciante && editando" class="check">
              <input v-model="divulgar" type="checkbox" />
              Quero divulgar animais para adoção
            </label>
            <template v-if="conta.anunciante || divulgar">
              <label>
                Apresentação
                <textarea v-model.trim="descricao" :readonly="!editando" rows="3" maxlength="500"
                  :placeholder="editando ? 'Conte quem você é e como cuida dos animais...' : 'Sem apresentação.'"></textarea>
              </label>
            </template>
            <p v-if="!conta.anunciante && !editando" class="conta-dica">
              Você ainda não divulga animais. Clique em <strong>Editar dados</strong> se quiser começar.
            </p>
          </fieldset>

          <template v-if="editando">
            <p v-if="aviso" class="form-feedback info" role="status">{{ aviso }}</p>
            <p v-if="erro" class="form-feedback error" role="alert">{{ erro }}</p>
            <div class="conta-botoes">
              <button class="button button-outline" type="button" :disabled="salvando" @click="cancelar">Cancelar</button>
              <button class="button button-orange" type="submit" :disabled="salvando">{{ salvando ? 'Salvando...' : 'Salvar alterações' }}</button>
            </div>
          </template>
        </form>

        <div class="card form-card conta-senha">
          <div class="conta-senha-topo">
            <div>
              <h2>Senha</h2>
              <p v-if="!senhaAberta">••••••••</p>
            </div>
            <button v-if="!senhaAberta" class="button button-outline" type="button" @click="senhaAberta = true; sucessoSenha = ''">Trocar senha</button>
          </div>
          <p v-if="sucessoSenha" class="form-feedback success" role="status">{{ sucessoSenha }}</p>

          <form v-if="senhaAberta" @submit.prevent="trocarSenha">
            <label>Senha atual<input v-model="senha.atual" required type="password" autocomplete="current-password" /></label>
            <div class="form-row">
              <label>Nova senha<input v-model="senha.nova" required type="password" minlength="6" autocomplete="new-password" placeholder="Mínimo de 6 caracteres" /></label>
              <label>Confirme a nova senha<input v-model="senha.confirmacao" required type="password" minlength="6" autocomplete="new-password" /></label>
            </div>
            <p v-if="erroSenha" class="form-feedback error" role="alert">{{ erroSenha }}</p>
            <div class="conta-botoes">
              <button class="button button-outline" type="button" :disabled="trocando" @click="fecharSenha">Cancelar</button>
              <button class="button button-orange" type="submit" :disabled="trocando">{{ trocando ? 'Trocando...' : 'Salvar nova senha' }}</button>
            </div>
          </form>
        </div>
      </template>
    </div>
  </section>
</template>
