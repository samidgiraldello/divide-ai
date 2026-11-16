"""API do DIVIDE AI: divida gastos e descubra quem deve para quem."""
from fastapi import FastAPI, HTTPException

from . import dominio
from .armazenamento import Grupo, Repositorio
from .schemas import (
    GastoCriar,
    GastoOut,
    GrupoCriar,
    GrupoOut,
    PagamentoCriar,
    PagamentoOut,
    SaldoOut,
    TransferenciaOut,
)

DESCRICAO = (
    "API para dividir gastos entre pessoas. Lance gastos e pagamentos e consulte os saldos "
    "e o menor conjunto de transferências para zerar as dívidas."
)


def _grupo_ou_404(repo: Repositorio, grupo_id: int) -> Grupo:
    grupo = repo.obter(grupo_id)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return grupo


def _exigir_membros(grupo: Grupo, nomes: list[str]) -> None:
    desconhecidos = [nome for nome in nomes if nome not in grupo.membros]
    if desconhecidos:
        raise HTTPException(
            status_code=422,
            detail=f"Não fazem parte do grupo: {', '.join(desconhecidos)}.",
        )


def criar_app(repo: Repositorio | None = None) -> FastAPI:
    repo = repo or Repositorio()
    app = FastAPI(title="DIVIDE AI", description=DESCRICAO, version="0.1.0")

    @app.get("/saude", tags=["Geral"])
    def saude():
        return {"status": "ok"}

    @app.post("/grupos", response_model=GrupoOut, status_code=201, tags=["Grupos"])
    def criar_grupo(dados: GrupoCriar):
        grupo = repo.criar_grupo(dados.nome, dados.membros)
        return GrupoOut(id=grupo.id, nome=grupo.nome, membros=list(grupo.membros))

    @app.get("/grupos/{grupo_id}", response_model=GrupoOut, tags=["Grupos"])
    def obter_grupo(grupo_id: int):
        grupo = _grupo_ou_404(repo, grupo_id)
        return GrupoOut(id=grupo.id, nome=grupo.nome, membros=list(grupo.membros))

    @app.post("/grupos/{grupo_id}/gastos", response_model=GastoOut, status_code=201, tags=["Gastos"])
    def adicionar_gasto(grupo_id: int, dados: GastoCriar):
        grupo = _grupo_ou_404(repo, grupo_id)
        participantes = dados.participantes or list(grupo.membros)
        _exigir_membros(grupo, [dados.pago_por, *participantes])
        try:
            gasto = repo.adicionar_gasto(
                grupo,
                dados.descricao,
                dominio.reais_para_centavos(dados.valor),
                dados.pago_por,
                tuple(participantes),
            )
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        return GastoOut(
            id=gasto.id,
            descricao=gasto.descricao,
            valor=dominio.formatar_reais(gasto.valor_centavos),
            pago_por=gasto.pago_por,
            participantes=list(gasto.participantes),
        )

    @app.get("/grupos/{grupo_id}/gastos", response_model=list[GastoOut], tags=["Gastos"])
    def listar_gastos(grupo_id: int):
        grupo = _grupo_ou_404(repo, grupo_id)
        return [
            GastoOut(
                id=g.id,
                descricao=g.descricao,
                valor=dominio.formatar_reais(g.valor_centavos),
                pago_por=g.pago_por,
                participantes=list(g.participantes),
            )
            for g in grupo.gastos
        ]

    @app.post("/grupos/{grupo_id}/pagamentos", response_model=PagamentoOut, status_code=201, tags=["Pagamentos"])
    def registrar_pagamento(grupo_id: int, dados: PagamentoCriar):
        grupo = _grupo_ou_404(repo, grupo_id)
        _exigir_membros(grupo, [dados.de, dados.para])
        try:
            pagamento = repo.adicionar_pagamento(
                grupo, dados.de, dados.para, dominio.reais_para_centavos(dados.valor)
            )
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        return PagamentoOut(
            id=pagamento.id,
            de=pagamento.de,
            para=pagamento.para,
            valor=dominio.formatar_reais(pagamento.valor_centavos),
        )

    @app.get("/grupos/{grupo_id}/saldos", response_model=list[SaldoOut], tags=["Contas"])
    def saldos(grupo_id: int):
        grupo = _grupo_ou_404(repo, grupo_id)
        calculados = dominio.calcular_saldos(grupo.gastos, grupo.pagamentos, grupo.membros)
        return [
            SaldoOut(
                membro=nome,
                saldo=dominio.formatar_reais(valor),
                situacao="recebe" if valor > 0 else "deve" if valor < 0 else "quite",
            )
            for nome, valor in calculados.items()
        ]

    @app.get("/grupos/{grupo_id}/acertos", response_model=list[TransferenciaOut], tags=["Contas"])
    def acertos(grupo_id: int):
        """Menor conjunto de transferências para zerar todas as dívidas do grupo."""
        grupo = _grupo_ou_404(repo, grupo_id)
        calculados = dominio.calcular_saldos(grupo.gastos, grupo.pagamentos, grupo.membros)
        return [
            TransferenciaOut(de=t.de, para=t.para, valor=dominio.formatar_reais(t.valor_centavos))
            for t in dominio.simplificar(calculados)
        ]

    return app


app = criar_app()
