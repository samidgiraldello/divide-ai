import random
import unittest
from decimal import Decimal

from app.dominio import (
    Gasto,
    Pagamento,
    calcular_saldos,
    dividir_igualmente,
    formatar_reais,
    reais_para_centavos,
    simplificar,
)


def aplicar(saldos, transferencias):
    """Aplica as transferências sobre os saldos e devolve o resultado."""
    resultado = dict(saldos)
    for t in transferencias:
        resultado[t.de] += t.valor_centavos
        resultado[t.para] -= t.valor_centavos
    return resultado


class TestDinheiro(unittest.TestCase):
    def test_reais_para_centavos(self):
        self.assertEqual(reais_para_centavos(Decimal("12.34")), 1234)
        self.assertEqual(reais_para_centavos(Decimal("0.10")), 10)

    def test_rejeita_mais_de_duas_casas(self):
        with self.assertRaises(ValueError):
            reais_para_centavos(Decimal("1.234"))

    def test_formatar(self):
        self.assertEqual(formatar_reais(1234), "12.34")
        self.assertEqual(formatar_reais(5), "0.05")
        self.assertEqual(formatar_reais(-50), "-0.50")


class TestDivisao(unittest.TestCase):
    def test_divisao_exata(self):
        self.assertEqual(dividir_igualmente(1000, ["A", "B"]), {"A": 500, "B": 500})

    def test_nao_perde_centavos(self):
        partes = dividir_igualmente(100, ["A", "B", "C"])
        self.assertEqual(sum(partes.values()), 100)
        self.assertEqual(sorted(partes.values()), [33, 33, 34])

    def test_centavo_extra_gira_com_o_deslocamento(self):
        quem_leva = {
            max(dividir_igualmente(100, ["A", "B", "C"], d).items(), key=lambda i: i[1])[0]
            for d in range(3)
        }
        self.assertEqual(quem_leva, {"A", "B", "C"})

    def test_erros(self):
        with self.assertRaises(ValueError):
            dividir_igualmente(0, ["A"])
        with self.assertRaises(ValueError):
            dividir_igualmente(100, [])
        with self.assertRaises(ValueError):
            dividir_igualmente(100, ["A", "A"])


class TestSaldos(unittest.TestCase):
    def test_casal_simples(self):
        gastos = [Gasto(1, "Mercado", 12000, "Ana", ("Ana", "Bruno"))]
        saldos = calcular_saldos(gastos, membros=["Ana", "Bruno"])
        self.assertEqual(saldos, {"Ana": 6000, "Bruno": -6000})

    def test_dividas_cruzadas_se_anulam(self):
        gastos = [
            Gasto(1, "Mercado", 10000, "Ana", ("Ana", "Bruno")),
            Gasto(2, "Luz", 10000, "Bruno", ("Ana", "Bruno")),
        ]
        saldos = calcular_saldos(gastos, membros=["Ana", "Bruno"])
        self.assertEqual(saldos, {"Ana": 0, "Bruno": 0})
        self.assertEqual(simplificar(saldos), [])

    def test_pagamento_quita_a_divida(self):
        gastos = [Gasto(1, "Mercado", 12000, "Ana", ("Ana", "Bruno"))]
        pagamentos = [Pagamento(1, "Bruno", "Ana", 6000)]
        saldos = calcular_saldos(gastos, pagamentos, ["Ana", "Bruno"])
        self.assertEqual(saldos, {"Ana": 0, "Bruno": 0})

    def test_quem_paga_sem_participar(self):
        gastos = [Gasto(1, "Presente", 9000, "Ana", ("Bruno", "Carla"))]
        saldos = calcular_saldos(gastos, membros=["Ana", "Bruno", "Carla"])
        self.assertEqual(saldos, {"Ana": 9000, "Bruno": -4500, "Carla": -4500})

    def test_soma_dos_saldos_e_sempre_zero(self):
        gastos = [Gasto(i, "x", 1000 + i * 7, "A", ("A", "B", "C")) for i in range(1, 20)]
        self.assertEqual(sum(calcular_saldos(gastos, membros="ABC").values()), 0)


class TestSimplificar(unittest.TestCase):
    def test_exemplo_do_readme(self):
        gastos = [
            Gasto(1, "Mercado", 9000, "Ana", ("Ana", "Bruno", "Carla")),
            Gasto(2, "Luz", 6000, "Bruno", ("Ana", "Bruno", "Carla")),
        ]
        saldos = calcular_saldos(gastos, membros=["Ana", "Bruno", "Carla"])
        self.assertEqual(saldos, {"Ana": 4000, "Bruno": 1000, "Carla": -5000})
        transferencias = {(t.de, t.para, t.valor_centavos) for t in simplificar(saldos)}
        self.assertEqual(transferencias, {("Carla", "Ana", 4000), ("Carla", "Bruno", 1000)})

    def test_cadeia_vira_transferencia_direta(self):
        # Ana deve a Bruno e Bruno deve a Carla: Ana paga direto a Carla.
        saldos = {"Ana": -10000, "Bruno": 0, "Carla": 10000}
        resultado = simplificar(saldos)
        self.assertEqual(len(resultado), 1)
        self.assertEqual((resultado[0].de, resultado[0].para), ("Ana", "Carla"))

    def test_valores_iguais_sao_casados_primeiro(self):
        saldos = {"A": -300, "B": -500, "C": 500, "D": 300}
        resultado = simplificar(saldos)
        self.assertEqual(len(resultado), 2)

    def test_saldos_que_nao_somam_zero(self):
        with self.assertRaises(ValueError):
            simplificar({"A": 100, "B": -50})

    def test_propriedades_com_dados_aleatorios(self):
        aleatorio = random.Random(42)
        for _ in range(300):
            n = aleatorio.randint(2, 8)
            nomes = [f"P{i}" for i in range(n)]
            valores = [aleatorio.randint(-5000, 5000) for _ in range(n - 1)]
            valores.append(-sum(valores))
            saldos = dict(zip(nomes, valores))

            transferencias = simplificar(saldos)

            # 1) todas as dívidas ficam zeradas
            self.assertTrue(all(v == 0 for v in aplicar(saldos, transferencias).values()))
            # 2) no máximo n - 1 transferências
            diferentes_de_zero = sum(1 for v in valores if v != 0)
            self.assertLessEqual(len(transferencias), max(diferentes_de_zero - 1, 0))
            # 3) nenhuma transferência de valor zero ou negativo
            self.assertTrue(all(t.valor_centavos > 0 for t in transferencias))


if __name__ == "__main__":
    unittest.main()
