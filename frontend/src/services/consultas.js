// Consultas publicas usadas para preencher o cadastro (ViaCEP e BrasilAPI)
import axios from 'axios'

const soDigitos = (v) => (v || '').replace(/\D/g, '')

export async function buscarCep(cep) {
  const { data } = await axios.get(`https://viacep.com.br/ws/${soDigitos(cep)}/json/`, { timeout: 8000 })
  if (data.erro) throw new Error('CEP não encontrado.')
  return { rua: data.logradouro, bairro: data.bairro, cidade: data.localidade, estado: data.uf }
}

export async function buscarCnpj(cnpj) {
  const { data } = await axios.get(`https://brasilapi.com.br/api/cnpj/v1/${soDigitos(cnpj)}`, { timeout: 10000 })
  return {
    nome: data.nome_fantasia || data.razao_social,
    telefone: data.ddd_telefone_1 || '',
    endereco: {
      cep: data.cep ? `${String(data.cep).slice(0, 5)}-${String(data.cep).slice(5)}` : '',
      rua: data.logradouro,
      numero: data.numero,
      complemento: data.complemento,
      bairro: data.bairro,
      cidade: data.municipio,
      estado: data.uf
    }
  }
}
