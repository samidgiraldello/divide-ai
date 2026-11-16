# DIVIDE AI

API em **Python + FastAPI** para dividir gastos entre pessoas, no estilo Splitwise.
Você lança os gastos e pagamentos e a API diz **quem deve para quem**, resumindo as dívidas no
menor número razoável de transferências.

> Status: versão 0.1 (núcleo de regras pronto e testado). Veja o [roadmap](#roadmap).

## O desafio: simplificar dívidas

Dividir um gasto é fácil. O interessante é o fim do mês. Exemplo com 3 pessoas:

- Ana pagou o mercado (R$ 90,00) e dividiu entre as três.
- Bruno pagou a luz (R$ 60,00) e dividiu entre as três.

Ninguém quer fazer 4 transferências cruzadas. O DIVIDE AI calcula o **saldo** de cada pessoa
(Ana +R$ 40,00, Bruno +R$ 10,00, Carla -R$ 50,00) e devolve só o necessário:

```
Carla -> Ana    R$ 40,00
Carla -> Bruno  R$ 10,00
```

E se Ana deve a Bruno e Bruno deve a Carla, a API manda Ana pagar direto a Carla.

### Como o algoritmo funciona

1. **Saldo líquido:** cada pessoa recebe `+` pelo que pagou e `-` pela sua parte em cada gasto.
   A soma de todos os saldos é sempre zero.
2. **Casamento exato:** se um devedor deve exatamente o que um credor tem a receber, uma única
   transferência resolve as duas pessoas.
3. **Guloso:** no que sobrar, o maior devedor paga ao maior credor, repetidamente.

Isso garante **no máximo (pessoas com saldo ≠ 0) − 1 transferências**. Achar o mínimo absoluto é um
problema NP-difícil, então o resultado é uma boa heurística, não uma prova de otimalidade.

### Decisões de projeto

- **Dinheiro em centavos (`int`)**, nunca `float`, para não acumular erro de arredondamento.
- **Sem perder centavos:** R$ 1,00 dividido por 3 vira 0,34 + 0,33 + 0,33. O centavo extra gira entre
  os participantes a cada gasto, para ninguém ficar sempre no prejuízo.
- **Regras separadas da API:** `app/dominio.py` não depende de FastAPI e é testado sozinho.
- **Testes de propriedade:** 300 casos aleatórios verificam que as transferências zeram todos os
  saldos, nunca passam do limite e nunca têm valor zero.

## Como rodar

Requisitos: Python 3.10 ou mais novo.

```bash
git clone https://github.com/samidgiraldello/divide-ai.git
cd divide-ai

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000/docs para usar a documentação interativa (Swagger).

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| POST | `/grupos` | Cria um grupo com 2 ou mais membros |
| GET | `/grupos/{id}` | Consulta um grupo |
| POST | `/grupos/{id}/gastos` | Lança um gasto (quem pagou, valor, quem divide) |
| GET | `/grupos/{id}/gastos` | Lista os gastos |
| POST | `/grupos/{id}/pagamentos` | Registra um acerto já feito entre duas pessoas |
| GET | `/grupos/{id}/saldos` | Mostra quem recebe, quem deve e quem está quite |
| GET | `/grupos/{id}/acertos` | Mostra as transferências que zeram as dívidas |

### Exemplo: casal

```bash
# 1. criar o grupo
curl -X POST http://127.0.0.1:8000/grupos -H "Content-Type: application/json" \
  -d '{"nome": "Casa", "membros": ["Ana", "Bruno"]}'

# 2. Ana pagou o mercado e dividiu com Bruno
curl -X POST http://127.0.0.1:8000/grupos/1/gastos -H "Content-Type: application/json" \
  -d '{"descricao": "Mercado", "valor": "120.00", "pago_por": "Ana"}'

# 3. quem deve para quem?
curl http://127.0.0.1:8000/grupos/1/acertos
# [{"de": "Bruno", "para": "Ana", "valor": "60.00"}]
```

Se `participantes` for omitido, o gasto é dividido entre todos os membros do grupo.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -v
```

Os testes das regras de negócio rodam sem dependências extras. Os testes da API precisam do
`requirements-dev.txt`. Um workflow do GitHub Actions roda tudo a cada commit.

## Estrutura

```
app/dominio.py        regras: divisão, saldos e simplificação (sem dependências)
app/schemas.py        validação de entrada e saída (Pydantic)
app/armazenamento.py  armazenamento em memória
app/main.py           rotas FastAPI
tests/                testes das regras e da API
```

## Roadmap

- [ ] Persistência em SQLite com SQLAlchemy
- [ ] Divisão desigual (por porcentagem ou por valores)
- [ ] Autenticação e vários grupos por usuário
- [ ] **Lançar gastos por texto com IA:** `POST /grupos/{id}/gastos/texto` recebe uma frase como
      *"Ana pagou 120 no mercado, dividido entre nós"*, usa o **Gemini** para extrair os campos em JSON
      e devolve uma **prévia para a pessoa confirmar** antes de salvar
- [ ] Dockerfile
- [ ] Exportar o resumo do mês

## Autora

Samid Giraldello de Oliveira · https://github.com/samidgiraldello ·
https://www.linkedin.com/in/samid-giraldello-491427255/
