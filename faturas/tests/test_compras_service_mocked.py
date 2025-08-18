import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from faturas.service.compras_service import (
    salvar_compra, 
    validar_compra, 
    parcelar_compra, 
    atualiza_fatura
)


class TestComprasServiceCalculations:
    """
    Testes unitários focados nos cálculos críticos do serviço de compras.
    Todos os testes são mockados e não afetam o banco de dados.
    """

    @pytest.fixture
    def mock_compra(self):
        """Cria um mock de compra para testes."""
        compra = Mock()
        compra.usuario = Mock()
        compra.nome_compra = "Teste Compra"
        compra.valor_compra = Decimal('150.50')
        compra.data_compra = date(2024, 3, 15)
        compra.n_parcelas = 1
        compra.compra_recorrente = False
        compra.compra_parcelada = False
        compra.cartao = "Master"
        compra.save = Mock()
        return compra

    @pytest.fixture
    def mock_fatura_form(self):
        """Cria um mock do FaturaForm."""
        form = Mock()
        form.is_valid.return_value = True
        form.save = Mock()
        return form

    class TestParcelarCompraCalculations:
        """Testes focados nos cálculos de parcelamento."""

        def test_parcelar_compra_3_parcelas_calculo_preciso(self, mock_compra):
            """Testa cálculo preciso de parcelamento em 3x."""
            # Arrange
            mock_compra.valor_compra = Decimal('150.50')
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura') as mock_atualiza:
                # Act
                parcelar_compra(mock_compra)
                
                # Assert - Valor da parcela deve ser calculado corretamente
                valor_esperado = (Decimal('150.50') / 3).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('50.17')  # 150.50 / 3 = 50.166... -> 50.17
                
                # Deve chamar atualiza_fatura 3 vezes
                assert mock_atualiza.call_count == 3

        def test_parcelar_compra_2_parcelas_calculo_preciso(self, mock_compra):
            """Testa cálculo preciso de parcelamento em 2x."""
            # Arrange
            mock_compra.valor_compra = Decimal('100.15')
            mock_compra.n_parcelas = 2
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura') as mock_atualiza:
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                valor_esperado = (Decimal('100.15') / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('50.08')  # 100.15 / 2 = 50.075 -> 50.08
                
                assert mock_atualiza.call_count == 2

        def test_parcelar_compra_valor_com_muitas_casas_decimais(self, mock_compra):
            """Testa arredondamento com valores que geram muitas casas decimais."""
            # Arrange
            mock_compra.valor_compra = Decimal('100.00')
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            with patch('faturas.service.compras_service.atualiza_fatura'):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                valor_esperado = (Decimal('100.00') / 3).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                assert mock_compra.valor_parcela == valor_esperado
                assert valor_esperado == Decimal('33.33')  # 100.00 / 3 = 33.333... -> 33.33

        def test_parcelar_compra_incremento_data_parcelas(self, mock_compra):
            """Testa se as datas das parcelas são incrementadas corretamente."""
            # Arrange
            mock_compra.valor_compra = Decimal('150.00')
            mock_compra.n_parcelas = 3
            data_inicial = date(2024, 3, 15)
            mock_compra.data_compra = data_inicial
            mock_compra.data_parcela = data_inicial
            
            datas_chamadas = []
            
            def capturar_data_parcela(compra):
                datas_chamadas.append(compra.data_parcela)
            
            with patch('faturas.service.compras_service.atualiza_fatura', side_effect=capturar_data_parcela):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert - Datas devem ser incrementadas mensalmente
                assert len(datas_chamadas) == 3
                assert datas_chamadas[0] == date(2024, 3, 15)  # Primeira parcela
                assert datas_chamadas[1] == date(2024, 4, 15)  # Segunda parcela
                assert datas_chamadas[2] == date(2024, 5, 15)  # Terceira parcela

        def test_parcelar_compra_parcela_atual_formatacao(self, mock_compra):
            """Testa se a formatação da parcela atual está correta."""
            # Arrange
            mock_compra.valor_compra = Decimal('150.00')
            mock_compra.n_parcelas = 3
            mock_compra.data_compra = date(2024, 3, 15)
            mock_compra.data_parcela = date(2024, 3, 15)
            
            parcelas_chamadas = []
            
            def capturar_parcela_atual(compra):
                parcelas_chamadas.append(compra.parcela_atual)
            
            with patch('faturas.service.compras_service.atualiza_fatura', side_effect=capturar_parcela_atual):
                # Act
                parcelar_compra(mock_compra)
                
                # Assert
                assert len(parcelas_chamadas) == 3
                assert parcelas_chamadas[0] == "1/3"
                assert parcelas_chamadas[1] == "2/3"
                assert parcelas_chamadas[2] == "3/3"

    class TestValidarCompraBusinessRules:
        """Testes das regras de negócio de validação."""

        def test_validar_compra_recorrente_com_1_parcela_valida(self, mock_compra):
            """Compra recorrente com 1 parcela deve ser válida."""
            # Arrange
            mock_compra.compra_recorrente = True
            mock_compra.n_parcelas = 1
            
            # Act
            resultado = validar_compra(mock_compra)
            
            # Assert
            assert resultado is None

        def test_validar_compra_recorrente_com_multiplas_parcelas_invalida(self, mock_compra):
            """Compra recorrente não pode ter múltiplas parcelas."""
            # Arrange
            mock_compra.compra_recorrente = True
            mock_compra.n_parcelas = 3
            
            # Act
            resultado = validar_compra(mock_compra)
            
            # Assert
            assert resultado == ('n_parcelas', 'Uma compra recorrente não pode ser parcelada.')

        def test_validar_compra_nao_recorrente_com_multiplas_parcelas_valida(self, mock_compra):
            """Compra não recorrente pode ter múltiplas parcelas."""
            # Arrange
            mock_compra.compra_recorrente = False
            mock_compra.n_parcelas = 5
            
            # Act
            resultado = validar_compra(mock_compra)
            
            # Assert
            assert resultado is None

    class TestSalvarCompraDateCalculations:
        """Testes dos cálculos de data na função salvar_compra."""

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_data_menor_que_12_nao_incrementa(self, mock_parcelar, mock_compra):
            """Data menor que 12 não deve ser incrementada."""
            # Arrange
            mock_compra.data_compra = date(2024, 3, 10)  # Dia 10
            mock_compra.n_parcelas = 3
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert
            assert mock_compra.data_compra == date(2024, 3, 10)  # Não deve mudar
            assert mock_compra.compra_parcelada is True
            mock_compra.save.assert_called_once()
            mock_parcelar.assert_called_once_with(mock_compra)

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_data_maior_igual_12_incrementa_mes(self, mock_parcelar, mock_compra):
            """Data >= 12 deve incrementar um mês."""
            # Arrange
            mock_compra.data_compra = date(2024, 3, 15)  # Dia 15
            mock_compra.n_parcelas = 2
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert
            data_esperada = date(2024, 4, 15)  # Deve incrementar 1 mês
            assert mock_compra.data_compra == data_esperada
            mock_parcelar.assert_called_once_with(mock_compra)

        @patch('faturas.service.compras_service.parcelar_compra')
        def test_salvar_compra_dia_12_exato_incrementa_mes(self, mock_parcelar, mock_compra):
            """Dia 12 exato deve incrementar um mês."""
            # Arrange
            mock_compra.data_compra = date(2024, 3, 12)  # Dia 12
            mock_compra.n_parcelas = 2
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert
            data_esperada = date(2024, 4, 12)  # Deve incrementar 1 mês
            assert mock_compra.data_compra == data_esperada

        @patch('faturas.service.compras_service.atualiza_fatura')
        def test_salvar_compra_recorrente_normaliza_data(self, mock_atualiza, mock_compra):
            """Compra recorrente deve normalizar data para 2000-01-01."""
            # Arrange
            mock_compra.data_compra = date(2024, 8, 25)
            mock_compra.compra_recorrente = True
            mock_compra.n_parcelas = 1
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert
            assert mock_compra.data_compra == date(2000, 1, 1)
            assert mock_compra.parcela_atual == 'Única'
            assert mock_compra.valor_parcela == mock_compra.valor_compra
            mock_atualiza.assert_called_once_with(mock_compra)

        @patch('faturas.service.compras_service.atualiza_fatura')
        def test_salvar_compra_unica_nao_parcelada(self, mock_atualiza, mock_compra):
            """Compra única não deve ser parcelada."""
            # Arrange
            mock_compra.data_compra = date(2024, 3, 10)
            mock_compra.n_parcelas = 1
            
            # Act
            salvar_compra(mock_compra)
            
            # Assert
            assert mock_compra.compra_parcelada is False
            assert mock_compra.parcela_atual == 'Única'
            assert mock_compra.data_parcela == mock_compra.data_compra
            assert mock_compra.valor_parcela == mock_compra.valor_compra
            mock_atualiza.assert_called_once_with(mock_compra)

    class TestAtualizaFaturaIntegration:
        """Testes da função atualiza_fatura com mocks."""

        @patch('faturas.service.compras_service.FaturaForm')
        def test_atualiza_fatura_form_valido(self, mock_form_class, mock_compra, mock_fatura_form):
            """Testa criação de fatura com form válido."""
            # Arrange
            mock_form_class.return_value = mock_fatura_form
            mock_compra.parcela_atual = "1/3"
            mock_compra.valor_parcela = Decimal('50.17')
            mock_compra.data_parcela = date(2024, 3, 15)
            
            # Act
            atualiza_fatura(mock_compra)
            
            # Assert
            mock_form_class.assert_called_once()
            call_args = mock_form_class.call_args[0][0]
            
            assert call_args['usuario'] == mock_compra.usuario
            assert call_args['compra'] == mock_compra
            assert call_args['nome_compra'] == mock_compra.nome_compra
            assert call_args['parcela_atual'] == "1/3"
            assert call_args['valor_parcela'] == Decimal('50.17')
            assert call_args['mes'] == 3
            assert call_args['ano'] == 2024
            
            mock_fatura_form.is_valid.assert_called_once()
            mock_fatura_form.save.assert_called_once()

        @patch('faturas.service.compras_service.FaturaForm')
        def test_atualiza_fatura_form_invalido_levanta_excecao(self, mock_form_class, mock_compra):
            """Testa que form inválido levanta exceção."""
            # Arrange
            mock_form = Mock()
            mock_form.is_valid.return_value = False
            mock_form.errors = {'campo': ['erro']}
            mock_form_class.return_value = mock_form
            
            # Act & Assert
            with pytest.raises(ValueError, match="Erro ao criar fatura"):
                atualiza_fatura(mock_compra)
            
            mock_form.save.assert_not_called()