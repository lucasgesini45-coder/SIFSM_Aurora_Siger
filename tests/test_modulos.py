import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.simulation import gerar_simulacao, exportar_csv
from src.regression import calcular_regressao

class TestModulos(unittest.TestCase):
    def test_reproducao_e_horas(self):
        d = gerar_simulacao()
        pd.testing.assert_frame_equal(d, gerar_simulacao())
        self.assertEqual(len(d), 168)
        self.assertEqual(d.hora.tolist(), list(range(168)))
        self.assertTrue((d.groupby('dia').size() == 24).all())
        self.assertFalse(d.isna().any().any())

    def test_conservacao_e_limites(self):
        d = gerar_simulacao()
        np.testing.assert_allclose(d.geracao_kw + d.bateria_inicio_kwh + d.deficit_kwh,
            d.consumo_kw + d.bateria_fim_kwh + d.perdas_kwh + d.excedente_kwh, atol=1e-10)
        np.testing.assert_allclose(d.bateria_inicio_kwh.iloc[1:], d.bateria_fim_kwh.iloc[:-1])
        self.assertTrue(d.soc_pct.between(0, 100).all())
        self.assertTrue((d[['perdas_kwh','deficit_kwh','excedente_kwh']] >= -1e-10).all().all())
        self.assertTrue((d.loc[(d.hora_dia < 6) | (d.hora_dia >= 18), 'geracao_kw'] == 0).all())
        self.assertTrue((d.deficit_kwh > 0).any())
        self.assertTrue((d.excedente_kwh > 0).any())

    def test_csv(self):
        with tempfile.TemporaryDirectory() as pasta:
            d = gerar_simulacao()
            arquivo = exportar_csv(d, Path(pasta) / 'dados.csv')
            pd.testing.assert_frame_equal(d, pd.read_csv(arquivo), atol=1e-8)

    def test_regressao_conhecida(self):
        x = np.arange(50)
        r = calcular_regressao(pd.DataFrame({'hora':x, 'consumo_kw':2*x+3}))
        self.assertAlmostEqual(r['coeficiente_angular'], 2)
        self.assertAlmostEqual(r['intercepto'], 3)
        self.assertAlmostEqual(r['r2_teste'], 1)
        self.assertAlmostEqual(r['consumo_previsto_kw'], 103)

    def test_entradas_invalidas(self):
        for valor in [0, -1, True, 2.5, '168']:
            with self.assertRaises(ValueError): gerar_simulacao(valor)
        for d in [None, pd.DataFrame(), pd.DataFrame({'hora':range(10), 'consumo_kw':[float('nan')]*10}),
                  pd.DataFrame({'hora':[0]*10, 'consumo_kw':[1]*10})]:
            with self.assertRaises(ValueError): calcular_regressao(d)

    def test_alvo_constante(self):
        r = calcular_regressao(pd.DataFrame({'hora':range(20), 'consumo_kw':[5]*20}))
        self.assertIsNone(r['r2_teste'])
        self.assertAlmostEqual(r['mae_kw'], 0)

if __name__ == '__main__': unittest.main()
