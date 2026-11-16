"""Modelos de entrada e saída da API (validação com Pydantic)."""
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


def _limpar_nomes(nomes: list[str]) -> list[str]:
    limpos = [nome.strip() for nome in nomes]
    if any(not nome for nome in limpos):
        raise ValueError("Os nomes não podem ser vazios.")
    if len(set(limpos)) != len(limpos):
        raise ValueError("Há nomes repetidos.")
    return limpos


class GrupoCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=80, examples=["Apartamento"])
    membros: list[str] = Field(min_length=2, examples=[["Ana", "Bruno"]])

    @field_validator("membros")
    @classmethod
    def _validar_membros(cls, v):
        return _limpar_nomes(v)


class GastoCriar(BaseModel):
    descricao: str = Field(min_length=1, max_length=120, examples=["Mercado"])
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["120.00"])
    pago_por: str = Field(examples=["Ana"])
    participantes: list[str] | None = Field(
        default=None,
        description="Quem divide o gasto. Se omitido, divide entre todos os membros.",
        examples=[["Ana", "Bruno"]],
    )

    @field_validator("participantes")
    @classmethod
    def _validar_participantes(cls, v):
        return None if v is None else _limpar_nomes(v)


class PagamentoCriar(BaseModel):
    de: str = Field(examples=["Bruno"])
    para: str = Field(examples=["Ana"])
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["60.00"])

    @model_validator(mode="after")
    def _pessoas_diferentes(self):
        if self.de == self.para:
            raise ValueError("Quem paga e quem recebe devem ser pessoas diferentes.")
        return self


class GrupoOut(BaseModel):
    id: int
    nome: str
    membros: list[str]


class GastoOut(BaseModel):
    id: int
    descricao: str
    valor: str
    pago_por: str
    participantes: list[str]


class PagamentoOut(BaseModel):
    id: int
    de: str
    para: str
    valor: str


class SaldoOut(BaseModel):
    membro: str
    saldo: str
    situacao: str  # "recebe", "deve" ou "quite"


class TransferenciaOut(BaseModel):
    de: str
    para: str
    valor: str
