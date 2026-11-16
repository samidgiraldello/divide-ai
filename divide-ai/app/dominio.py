"""Regras de negócio do DIVIDE AI, sem dependências externas.

Decisões importantes:
- Todo dinheiro é guardado em CENTAVOS (int). Nunca usamos float.
- Saldo positivo = a pessoa tem a receber. Saldo negativo = a pessoa deve.
- A soma de todos os saldos de um grupo é sempre zero.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Gasto:
    id: int
    descricao: str
    valor_centavos: int
    pago_por: str
    participantes: tuple[str, ...]


@dataclass(frozen=True)
class Pagamento:
    """Acerto feito de verdade: `de` pagou `valor` a `para`."""

    id: int
    de: str
    para: str
    valor_centavos: int


@dataclass(frozen=True)
class Transferencia:
    de: str
    para: str
    valor_centavos: int


def reais_para_centavos(valor: Decimal) -> int:
    """Converte reais (Decimal com no máximo 2 casas) para centavos inteiros."""
    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError("O valor deve ter no máximo 2 casas decimais.")
    return int((valor * 100).to_integral_exact())


def formatar_reais(centavos: int) -> str:
    """Ex.: 1234 -> '12.34' e -50 -> '-0.50'."""
    sinal = "-" if centavos < 0 else ""
    centavos = abs(centavos)
    return f"{sinal}{centavos // 100}.{centavos % 100:02d}"


def dividir_igualmente(valor_centavos: int, participantes, deslocamento: int = 0) -> dict[str, int]:
    """Divide o valor em partes iguais, sem perder nem criar centavos.

    Quando a divisão não é exata, os centavos que sobram vão um a um para os primeiros
    participantes (em ordem alfabética). O `deslocamento` gira essa ordem, para que o
    mesmo participante não fique sempre com o centavo extra.
    """
    participantes = list(participantes)
    if valor_centavos <= 0:
        raise ValueError("O valor do gasto deve ser maior que zero.")
    if not participantes:
        raise ValueError("O gasto precisa de pelo menos um participante.")
    if len(set(participantes)) != len(participantes):
        raise ValueError("Há participantes repetidos.")

    ordenados = sorted(participantes)
    n = len(ordenados)
    base, resto = divmod(valor_centavos, n)
    partes = {nome: base for nome in ordenados}
    for i in range(resto):
        partes[ordenados[(i + deslocamento) % n]] += 1
    return partes


def calcular_saldos(gastos, pagamentos=(), membros=()) -> dict[str, int]:
    """Saldo de cada pessoa em centavos (positivo = tem a receber)."""
    saldos = {nome: 0 for nome in membros}

    for gasto in gastos:
        saldos[gasto.pago_por] = saldos.get(gasto.pago_por, 0) + gasto.valor_centavos
        partes = dividir_igualmente(gasto.valor_centavos, gasto.participantes, gasto.id)
        for nome, parte in partes.items():
            saldos[nome] = saldos.get(nome, 0) - parte

    for pagamento in pagamentos:
        saldos[pagamento.de] = saldos.get(pagamento.de, 0) + pagamento.valor_centavos
        saldos[pagamento.para] = saldos.get(pagamento.para, 0) - pagamento.valor_centavos

    return saldos


def simplificar(saldos: dict[str, int]) -> list[Transferencia]:
    """Resume as dívidas no menor número razoável de transferências.

    1. Casa primeiro devedor e credor com valores exatamente iguais (uma transferência
       resolve duas pessoas de uma vez).
    2. No que sobrar, casa o maior devedor com o maior credor, repetidamente.

    Garante no máximo (pessoas com saldo diferente de zero - 1) transferências. Achar o
    mínimo absoluto é um problema difícil (NP-difícil), então isto é uma boa heurística.
    """
    if sum(saldos.values()) != 0:
        raise ValueError("Os saldos devem somar zero.")

    ordem = lambda item: (-item[1], item[0])  # noqa: E731 - maior valor primeiro, desempate por nome
    devedores = sorted(([n, -v] for n, v in saldos.items() if v < 0), key=ordem)
    credores = sorted(([n, v] for n, v in saldos.items() if v > 0), key=ordem)
    transferencias: list[Transferencia] = []

    # Passo 1: valores exatamente iguais.
    for devedor in devedores:
        for credor in credores:
            if devedor[1] > 0 and devedor[1] == credor[1]:
                transferencias.append(Transferencia(devedor[0], credor[0], devedor[1]))
                devedor[1] = 0
                credor[1] = 0
                break

    devedores = [d for d in devedores if d[1] > 0]
    credores = [c for c in credores if c[1] > 0]

    # Passo 2: guloso, maior com maior.
    i = j = 0
    while i < len(devedores) and j < len(credores):
        valor = min(devedores[i][1], credores[j][1])
        transferencias.append(Transferencia(devedores[i][0], credores[j][0], valor))
        devedores[i][1] -= valor
        credores[j][1] -= valor
        if devedores[i][1] == 0:
            i += 1
        if credores[j][1] == 0:
            j += 1

    return transferencias
