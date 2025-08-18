import pytest
from unittest.mock import Mock, patch
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from faturas.service.compras_service import parcelar_compra, salvar_compra


class TestCalculationEdgeCases:
    """
    Testes de casos extremos para garantir precisão matemática.
    Foco em casos que podem causar erros de cálculo.
    """

    @pytest.fixture
    def mock_compra(self):
        """Cria um mock de compra para testes."""
        compra = Mock()
        compra.usuario = Mock()
        compra.nome_compra = "Teste Edge Case"
        compra.compra_recorrente = False  # Default não recorrente
        compra.compra_parcelada = False  # Default não parcelada
        compra.save = Mock()
        return compra

    class TestDecimalPrecisionEdgeCases:
        """Testes de precisão decimal em casos extremos."""

        def test_parcelar_compra_valor_que_nao_divide_exato(self, mock_compra):
            """Testa parcelamento de valor que não divide exato."""
            # Arrange
            mock_compra.valor_compra = Decimal('100.00')
            mock_compra.n_parcelas = 7  # 100/7 = 14.285714...
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # 100.00 / 7 = 14.285714... -> deve arredondar para 14.29
                valor_esperado = (Decimal('100.00') / 7).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('14.29')

        def test_parcelar_compra_valor_centavos_impares(self, mock_compra):
            """Testa parcelamento com centavos ímpares."""
            # Arrange
            mock_compra.valor_compra = Decimal('99.99')
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # 99.99 / 3 = 33.33 exato
                valor_esperado = (Decimal('99.99') / 3).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('33.33')

        def test_parcelar_compra_valor_alto_muitas_parcelas(self, mock_compra):
            """Testa parcelamento de valor alto com muitas parcelas."""
            # Arrange
            mock_compra.valor_compra = Decimal('9999.99')
            mock_compra.n_parcelas = 12
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # 9999.99 / 12 = 833.33249... -> deve arredondar para 833.33
                valor_esperado = (Decimal('9999.99') / 12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('833.33')

        def test_parcelar_compra_valor_com_muitos_decimais(self, mock_compra):
            """Testa valor de entrada já com muitos decimais."""
            # Arrange - Simula valor calculado externamente
            mock_compra.valor_compra = Decimal('150.123456789')  # Muitos decimais
            mock_compra.n_parcelas = 4
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # Deve funcionar corretamente mesmo com input com muitos decimais
                valor_esperado = (Decimal('150.123456789') / 4).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('37.53')  # 150.123456789 / 4 = 37.530864... -> 37.53

        def test_parcelar_compra_arredondamento_half_up_exato(self, mock_compra):
            """Testa arredondamento HALF_UP em caso exato de 0.5."""
            # Arrange - Valor que gera exatamente .5 centavos
            mock_compra.valor_compra = Decimal('100.01')
            mock_compra.n_parcelas = 3  # 100.01 / 3 = 33.336666... -> 33.34
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                valor_esperado = (Decimal('100.01') / 3).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('33.34')

    class TestDateCalculationEdgeCases:
        """Testes de casos extremos para cálculos de data."""

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_ultimo_dia_mes_incremento(self, mock_parcelar, mock_compra):
            """Testa incremento de data no último dia do mês."""
            # Arrange - 31 de janeiro, dia >= 12
            mock_compra.data_compra = date(2024, 1, 31)
            mock_compra.n_parcelas = 2
            mock_compra.compra_recorrente = False  # Não é recorrente
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert - Deve virar para 29 de fevereiro (2024 é bissexto)
            data_esperada = date(2024, 2, 29)  # relativedelta lida corretamente com fim de mês
            assert mock_compra.data_compra == data_esperada

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_dia_29_fevereiro_bissexto(self, mock_parcelar, mock_compra):
            """Testa data em ano bissexto."""
            # Arrange - 29 de fevereiro em ano bissexto, dia >= 12
            mock_compra.data_compra = date(2024, 2, 29)  # 2024 é bissexto
            mock_compra.n_parcelas = 2
            mock_compra.compra_recorrente = False  # Não é recorrente
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert - Deve virar para 29 de março
            data_esperada = date(2024, 3, 29)
            assert mock_compra.data_compra == data_esperada

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_transicao_ano(self, mock_parcelar, mock_compra):
            """Testa transição de ano."""
            # Arrange - 31 de dezembro, dia >= 12
            mock_compra.data_compra = date(2024, 12, 31)
            mock_compra.n_parcelas = 3
            mock_compra.compra_recorrente = False  # Não é recorrente
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert - Deve virar para janeiro do ano seguinte
            data_esperada = date(2025, 1, 31)
            assert mock_compra.data_compra == data_esperada

        def test_parcelar_compra_incremento_data_atraves_mudanca_ano(self, mock_compra):
            """Testa incremento de datas que passam por mudança de ano."""
            # Arrange
            mock_compra.valor_compra = Decimal('300.00')
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 11, 15)  # Novembro
            mock_compra.data_parcela = date(2024, 11, 15)
            
            datas_chamadas = []
            
            def capturar_data_parcela(compra):
                datas_chamadas.append(compra.data_parcela)
            
            with patch('faturas.service.compras_service.atualiza_fatura', side_effect=capturar_data_parcela):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert - Deve atravessar o ano
                assert len(datas_chamadas) == 3
                assert datas_chamadas[0] == date(2024, 11, 15)  # Primeira parcela
                assert datas_chamadas[1] == date(2024, 12, 15)  # Segunda parcela
                assert datas_chamadas[2] == date(2025, 1, 15)   # Terceira parcela (ano seguinte)

    class TestBusinessRuleEdgeCases:
        """Testes de casos extremos das regras de negócio."""

        @patch('faturas.service.compras_service.atualiza_fatura')
        def test_salvar_compra_recorrente_com_data_futura(self, mock_atualiza, mock_compra):
            """Testa compra recorrente sempre normaliza para 2000-01-01."""
            # Arrange - Data muito no futuro
            mock_compra.data_compra = date(2030, 12, 25)
            mock_compra.compra_recorrente = True
            mock_compra.n_parcelas = 1
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert - Sempre normaliza para 2000-01-01
            assert mock_compra.data_compra == date(2000, 1, 1)

        def test_parcelar_compra_1_parcela_nao_executa_loop(self, mock_compra):
            """Testa que parcelar com 1 parcela não executa o loop."""
            # Arrange
            mock_compra.valor_compra = Decimal('100.00')
            mock_compra.n_parcelas = 1
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura') as mock_atualiza:
                # Act
                parcelar_compra(mock_compra)
                
                # Assert - Deve executar apenas 1 vez
                assert mock_atualiza.call_count == 1
                assert mock_compra.valor_parcela == Decimal('100.00')

        def test_parcelar_compra_muitas_parcelas(self, mock_compra):
            """Testa parcelamento com muitas parcelas."""
            # Arrange
            mock_compra.valor_compra = Decimal('2400.00')
            mock_compra.n_parcelas = 24  # 24 parcelas
            mock_compra.data_compra = date(2024, 1, 15)
            mock_compra.data_parcela = date(2024, 1, 15)
            
            datas_chamadas = []
            parcelas_chamadas = []
            
            def capturar_dados(compra):
                datas_chamadas.append(compra.data_parcela)
                parcelas_chamadas.append(compra.parcela_atual)
            
            with patch('faturas.service.compras_service.atualiza_fatura', side_effect=capturar_dados):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                assert len(datas_chamadas) == 24
                assert len(parcelas_chamadas) == 24
                
                # Primeira e última parcela
                assert parcelas_chamadas[0] == "1/24"
                assert parcelas_chamadas[23] == "24/24"
                
                # Primeira e última data (2 anos depois)
                assert datas_chamadas[0] == date(2024, 1, 15)
                assert datas_chamadas[23] == date(2025, 12, 15)
                
                # Valor da parcela
                valor_esperado = Decimal('100.00')  # 2400 / 24 = 100 exato
                assert mock_compra.valor_parcela == valor_esperado

    class TestNumericalStabilityTests:
        """Testes de estabilidade numérica com valores extremos."""

        def test_parcelar_compra_valor_muito_pequeno(self, mock_compra):
            """Testa parcelamento de valor muito pequeno."""
            # Arrange
            mock_compra.valor_compra = Decimal('0.03')  # 3 centavos
            mock_compra.n_parcelas = 2
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # 0.03 / 2 = 0.015 -> deve arredondar para 0.02
                valor_esperado = (Decimal('0.03') / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('0.02')

        def test_parcelar_compra_valor_exatamente_um_centavo(self, mock_compra):
            """Testa parcelamento do menor valor possível."""
            # Arrange
            mock_compra.valor_compra = Decimal('0.01')
            mock_compra.n_parcelas = 1
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                assert mock_compra.valor_parcela == Decimal('0.01')

        def test_decimal_operations_mantain_precision(self, mock_compra):
            """Testa que operações decimais mantêm precisão."""
            # Arrange - Testa um caso conhecido por problemas com float
            mock_compra.valor_compra = Decimal('0.1') + Decimal('0.2')  # Seria 0.30000000000000004 em float
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                # Com Decimal, 0.1 + 0.2 = 0.3 exato
                assert mock_compra.valor_compra == Decimal('0.3')
                # 0.3 / 3 = 0.1 exato
                valor_esperado = Decimal('0.10')
                assert mock_compra.valor_parcela == valor_esperado