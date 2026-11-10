import api from './api.js'

// a lista e buscada uma vez e reaproveitada pelas paginas
let lista = null

export async function sortearAnuncio() {
  lista ??= api.get('/parceiros/anuncios').then((r) => r.data)
  try {
    const anuncios = await lista
    return anuncios.length ? anuncios[Math.floor(Math.random() * anuncios.length)] : null
  } catch {
    lista = null
    return null
  }
}
