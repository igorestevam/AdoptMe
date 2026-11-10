const ESPECIES = { cachorro: 'Cão', gato: 'Gato' }
const SEXOS = { macho: 'Macho', femea: 'Fêmea' }
const PORTES = { pequeno: 'Pequeno', medio: 'Médio', grande: 'Grande' }

// opcoes dos selects do formulario de animal, na ordem em que aparecem
export const opcoes = (mapa) => Object.entries(mapa).map(([valor, rotulo]) => ({ valor, rotulo }))
export const OPCOES = { especie: opcoes(ESPECIES), sexo: opcoes(SEXOS), porte: opcoes(PORTES) }

export const especie = (v) => ESPECIES[v] || v
export const sexo = (v) => SEXOS[v] || v
export const porte = (v) => PORTES[v] || v

export function idade(anos) {
  if (anos === null || anos === undefined) return 'Idade não informada'
  return anos === 1 ? '1 ano' : `${anos} anos`
}

export const tipoResponsavel = (tipo) => (tipo === 'organizacao' ? 'Organização' : 'Pessoa física')

// usada quando o animal ainda nao tem foto
export const FOTO_PADRAO =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"><rect width="4" height="3" fill="#e6e9df"/><text x="2" y="1.9" font-size="1" text-anchor="middle">🐾</text></svg>')
