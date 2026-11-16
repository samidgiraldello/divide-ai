"""Armazenamento em memória. Próximo passo do projeto: trocar por SQLite/SQLAlchemy."""
from dataclasses import dataclass, field

from . import dominio


@dataclass
class Grupo:
    id: int
    nome: str
    membros: tuple[str, ...]
    gastos: list[dominio.Gasto] = field(default_factory=list)
    pagamentos: list[dominio.Pagamento] = field(default_factory=list)


class Repositorio:
    def __init__(self) -> None:
        self._grupos: dict[int, Grupo] = {}
        self._proximo_id = 1

    def criar_grupo(self, nome: str, membros: list[str]) -> Grupo:
        grupo = Grupo(id=self._proximo_id, nome=nome, membros=tuple(membros))
        self._grupos[grupo.id] = grupo
        self._proximo_id += 1
        return grupo

    def obter(self, grupo_id: int) -> Grupo | None:
        return self._grupos.get(grupo_id)

    def adicionar_gasto(self, grupo: Grupo, descricao: str, valor_centavos: int,
                        pago_por: str, participantes: tuple[str, ...]) -> dominio.Gasto:
        dominio.dividir_igualmente(valor_centavos, participantes)  # valida antes de salvar
        gasto = dominio.Gasto(
            id=len(grupo.gastos) + 1,
            descricao=descricao,
            valor_centavos=valor_centavos,
            pago_por=pago_por,
            participantes=participantes,
        )
        grupo.gastos.append(gasto)
        return gasto

    def adicionar_pagamento(self, grupo: Grupo, de: str, para: str, valor_centavos: int) -> dominio.Pagamento:
        if valor_centavos <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")
        pagamento = dominio.Pagamento(
            id=len(grupo.pagamentos) + 1, de=de, para=para, valor_centavos=valor_centavos
        )
        grupo.pagamentos.append(pagamento)
        return pagamento
