import unittest

try:
    from fastapi.testclient import TestClient

    from app.main import criar_app

    DISPONIVEL = True
except ImportError:  # fastapi/httpx não instalados
    DISPONIVEL = False


@unittest.skipUnless(DISPONIVEL, "instale requirements-dev.txt para rodar os testes da API")
class TestApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(criar_app())  # cada teste começa com um repositório vazio

    def _criar_grupo(self, membros=("Ana", "Bruno")):
        resposta = self.client.post("/grupos", json={"nome": "Casa", "membros": list(membros)})
        self.assertEqual(resposta.status_code, 201)
        return resposta.json()["id"]

    def test_saude(self):
        self.assertEqual(self.client.get("/saude").json(), {"status": "ok"})

    def test_fluxo_completo_do_casal(self):
        grupo = self._criar_grupo()
        gasto = self.client.post(
            f"/grupos/{grupo}/gastos",
            json={"descricao": "Mercado", "valor": "120.00", "pago_por": "Ana"},
        )
        self.assertEqual(gasto.status_code, 201)

        acertos = self.client.get(f"/grupos/{grupo}/acertos").json()
        self.assertEqual(acertos, [{"de": "Bruno", "para": "Ana", "valor": "60.00"}])

        self.client.post(f"/grupos/{grupo}/pagamentos", json={"de": "Bruno", "para": "Ana", "valor": "60.00"})
        self.assertEqual(self.client.get(f"/grupos/{grupo}/acertos").json(), [])
        situacoes = {s["membro"]: s["situacao"] for s in self.client.get(f"/grupos/{grupo}/saldos").json()}
        self.assertEqual(situacoes, {"Ana": "quite", "Bruno": "quite"})

    def test_grupo_inexistente(self):
        self.assertEqual(self.client.get("/grupos/999/saldos").status_code, 404)

    def test_pagador_fora_do_grupo(self):
        grupo = self._criar_grupo()
        resposta = self.client.post(
            f"/grupos/{grupo}/gastos",
            json={"descricao": "Cinema", "valor": "50.00", "pago_por": "Zé"},
        )
        self.assertEqual(resposta.status_code, 422)

    def test_valor_invalido(self):
        grupo = self._criar_grupo()
        for valor in ("0", "-5", "10.999"):
            resposta = self.client.post(
                f"/grupos/{grupo}/gastos",
                json={"descricao": "x", "valor": valor, "pago_por": "Ana"},
            )
            self.assertEqual(resposta.status_code, 422, valor)

    def test_grupo_precisa_de_dois_membros(self):
        resposta = self.client.post("/grupos", json={"nome": "Sozinho", "membros": ["Ana"]})
        self.assertEqual(resposta.status_code, 422)


if __name__ == "__main__":
    unittest.main()
