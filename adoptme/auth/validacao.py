"""Validacao e formatacao de CPF/CNPJ, CEP, UF e email."""
import re

UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def so_digitos(valor) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _digito(numeros: str, pesos: list[int]) -> int:
    resto = sum(int(n) * p for n, p in zip(numeros, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    d = so_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    dv1 = _digito(d[:9], range(10, 1, -1))
    dv2 = _digito(d[:10], range(11, 1, -1))
    return d[9:] == f"{dv1}{dv2}"


def cnpj_valido(cnpj: str) -> bool:
    d = so_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False
    dv1 = _digito(d[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    dv2 = _digito(d[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return d[12:] == f"{dv1}{dv2}"


def formatar_documento(valor: str) -> str | None:
    """Devolve o CPF ou CNPJ no formato com pontuacao, ou None se for invalido.

    Guardar sempre no mesmo formato faz a regra de documento unico funcionar
    mesmo quando a pessoa digita sem pontuacao.
    """
    d = so_digitos(valor)
    if cpf_valido(d):
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if cnpj_valido(d):
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return None


def formatar_cep(valor: str) -> str | None:
    d = so_digitos(valor)
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else None


def email_valido(email: str) -> bool:
    return bool(EMAIL.match(email or "")) and len(email) <= 150
