import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from faturas.service.fatura_service import tratar_import_fatura, gera_fatura


class TestFaturaServiceCalculations:
    """
    Testes unitários focados nos cálculos do serviço de faturas.
    Todos os testes são mockados e não afetam o banco de dados.
    """

    @pytest.fixture
    def mock_request(self):
        """Cria um mock de request."""
        request = Mock()
        request.POST = {'usuario': 123}
        request.user = Mock()
        request.user.id = 123
        return request

    @pytest.fixture
    def mock_usuario(self):
        """Cria um mock de usuário."""
        usuario = Mock()
        usuario.id = 123
        usuario.username = 'testuser'
        return usuario

    class TestTratarImportFaturaCalculations:
        """Testes dos cálculos de importação de faturas."""

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        @patch('faturas.service.fatura_service.Compra')
        @patch('faturas.service.fatura_service.atualiza_fatura')
        def test_tratar_import_fatura_unica_calculo_valor(
            self, mock_atualiza, mock_compra_class, mock_form_class, 
            mock_user_class, mock_request, mock_usuario
        ):
            """Testa cálculo de valor para fatura única."""
            # Arrange
            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form_class.return_value = mock_form
            
            mock_compra = Mock()
            mock_compra_class.objects.create.return_value = mock_compra
            
            data = [{
                'nome_da_compra': 'Supermercado',
                'data_compra': date(2024, 3, 15),
                'parcela': None,  # Fatura única
                'valor_da_compra': '150,50'  # Valor com vírgula
            }]
            
            # Act
            resultado = tratar_import_fatura(mock_request, data)
            
            # Assert
            assert resultado['valor_compra'] == Decimal('150.50')
            assert resultado['n_parcelas'] == 1
            assert resultado['compra_parcelada'] is False
            assert resultado['nome_compra'] == 'Supermercado'
            
            # Verifica se atualiza_fatura foi chamada para fatura única
            mock_atualiza.assert_called_once_with(mock_compra)

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        @patch('faturas.service.fatura_service.Compra')
        @patch('faturas.service.fatura_service.parcelar_compra')
        def test_tratar_import_fatura_parcelada_calculo_valor_total(
            self, mock_parcelar, mock_compra_class, mock_form_class, 
            mock_user_class, mock_request, mock_usuario
        ):
            """Testa cálculo de valor total para fatura parcelada."""
            # Arrange
            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form_class.return_value = mock_form
            
            mock_compra = Mock()
            mock_compra_class.objects.create.return_value = mock_compra
            
            data = [{
                'nome_da_compra': 'Celular',
                'data_compra': date(2024, 3, 15),
                'parcela': '2|3',  # 2ª parcela de 3
                'valor_da_compra': '50,17'  # Valor da parcela
            }]
            
            # Act
            resultado = tratar_import_fatura(mock_request, data)
            
            # Assert
            # Valor total deve ser calculado: valor_parcela * total_parcelas
            valor_esperado = Decimal('50.17') * 3
            assert resultado['valor_compra'] == valor_esperado
            assert valor_esperado == Decimal('150.51')
            assert resultado['n_parcelas'] == 3
            assert resultado['compra_parcelada'] is True
            
            # Verifica se parcelar_compra foi chamada
            mock_parcelar.assert_called_once_with(mock_compra)

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        @patch('faturas.service.fatura_service.Compra')
        @patch('faturas.service.fatura_service.parcelar_compra')
        def test_tratar_import_fatura_parcela_anterior_ajuste_data(
            self, mock_parcelar, mock_compra_class, mock_form_class, 
            mock_user_class, mock_request, mock_usuario
        ):
            """Testa ajuste de data para parcelas anteriores."""
            # Arrange
            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form_class.return_value = mock_form
            
            mock_compra = Mock()
            mock_compra_class.objects.create.return_value = mock_compra
            
            data_compra_atual = date(2024, 5, 15)
            data = [{
                'nome_da_compra': 'Produto',
                'data_compra': data_compra_atual,
                'parcela': '3|5',  # 3ª parcela de 5 (2 meses atrás)
                'valor_da_compra': '100,00'
            }]
            
            # Act
            resultado = tratar_import_fatura(mock_request, data)
            
            # Assert
            # Data deve ser ajustada para 2 meses atrás (parcela_atual - 1 = 3 - 1 = 2)
            data_esperada = data_compra_atual - relativedelta(months=2)
            assert resultado['data_compra'] == data_esperada
            assert data_esperada == date(2024, 3, 15)

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        @patch('faturas.service.fatura_service.mes_atua_dia11')
        @patch('faturas.service.fatura_service.Compra')
        @patch('faturas.service.fatura_service.atualiza_fatura')
        def test_tratar_import_fatura_sem_data_usa_default(
            self, mock_atualiza, mock_compra_class, mock_mes_atua, mock_form_class, mock_user_class,
            mock_request, mock_usuario
        ):
            """Testa que usa data default quando não informada."""
            # Arrange
            data_default = date(2024, 3, 11)
            mock_mes_atua.return_value = data_default

            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form_class.return_value = mock_form
            
            mock_compra = Mock()
            mock_compra_class.objects.create.return_value = mock_compra

            data = [{
                'nome_da_compra': 'Produto',
                'data_compra': None,  # Sem data
                'parcela': None,
                'valor_da_compra': '100,00'
            }]

            # Act
            resultado = tratar_import_fatura(mock_request, data)

            # Assert
            assert resultado['data_compra'] == data_default
            mock_mes_atua.assert_called_once()

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        def test_tratar_import_fatura_form_invalido_levanta_excecao(
            self, mock_form_class, mock_user_class, mock_request, mock_usuario
        ):
            """Testa que form inválido levanta exceção."""
            # Arrange
            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = False
            mock_form_class.return_value = mock_form
            
            data = [{
                'nome_da_compra': 'Produto',
                'data_compra': date(2024, 3, 15),
                'parcela': None,
                'valor_da_compra': '100,00'
            }]
            
            # Act & Assert
            with pytest.raises(ValueError, match="Erro ao criar compra"):
                tratar_import_fatura(mock_request, data)

        def test_tratar_import_fatura_sem_data_levanta_excecao(self, mock_request):
            """Testa que dados vazios levantam exceção."""
            # Act & Assert
            with pytest.raises(ValueError, match="Erro: Upload de dados não foi bem-sucedido"):
                tratar_import_fatura(mock_request, None)

        @patch('faturas.service.fatura_service.User')
        @patch('faturas.service.fatura_service.CompraForm')
        @patch('faturas.service.fatura_service.Compra')
        @patch('faturas.service.fatura_service.atualiza_fatura')
        def test_tratar_import_fatura_valor_com_espacos_e_virgula(
            self, mock_atualiza, mock_compra_class, mock_form_class, mock_user_class, 
            mock_request, mock_usuario
        ):
            """Testa normalização de valores com espaços e vírgulas."""
            # Arrange
            mock_user_class.objects.get.return_value = mock_usuario
            mock_form = Mock()
            mock_form.is_valid.return_value = True
            mock_form_class.return_value = mock_form
            
            mock_compra = Mock()
            mock_compra_class.objects.create.return_value = mock_compra

            data = [{
                'nome_da_compra': 'Produto',
                'data_compra': date(2024, 3, 15),
                'parcela': None,
                'valor_da_compra': ' 1250,75 '  # Valor com espaços e vírgula
            }]

            # Act
            resultado = tratar_import_fatura(mock_request, data)

            # Assert
            assert resultado['valor_compra'] == Decimal('1250.75')

    class TestGeraFaturaCalculations:
        """Testes dos cálculos de geração de faturas."""

        @patch('faturas.service.fatura_service.Fatura')
        def test_gera_fatura_calculo_total_simples(self, mock_fatura_class, mock_request):
            """Testa cálculo de total de faturas simples."""
            # Arrange
            mock_fatura1 = Mock()
            mock_fatura1.valor_parcela = Decimal('100.50')
            mock_fatura2 = Mock()
            mock_fatura2.valor_parcela = Decimal('200.25')
            
            faturas_list = [mock_fatura1, mock_fatura2]
            
            # Mock for normal faturas
            mock_queryset_normal = MagicMock()
            mock_queryset_normal.count.return_value = 2
            mock_queryset_normal.__iter__ = lambda self: iter(faturas_list)
            
            # Mock for recorrentes (empty)
            mock_queryset_recorrente = MagicMock()
            mock_queryset_recorrente.__bool__.return_value = False
            
            def filter_side_effect(**kwargs):
                if 'compra__compra_recorrente' in kwargs:
                    return mock_queryset_recorrente
                else:
                    return mock_queryset_normal
            
            mock_fatura_class.objects.filter.side_effect = filter_side_effect
            
            # Act
            faturas, total, compras = gera_fatura(mock_request, mes=3, ano=2024)
            
            # Assert
            assert total == Decimal('300.75')  # 100.50 + 200.25
            assert compras == 2
            assert faturas == mock_queryset_normal

        @patch('faturas.service.fatura_service.Fatura')
        def test_gera_fatura_com_recorrentes_merge_queryset(self, mock_fatura_class, mock_request):
            """Testa merge de faturas normais com recorrentes."""
            # Arrange
            # Faturas normais
            mock_fatura_normal = Mock()
            mock_fatura_normal.valor_parcela = Decimal('150.00')
            
            mock_queryset_normal = MagicMock()
            mock_queryset_normal.__iter__ = lambda self: iter([mock_fatura_normal])
            
            # Faturas recorrentes
            mock_fatura_recorrente = Mock()
            mock_fatura_recorrente.valor_parcela = Decimal('45.90')
            
            mock_queryset_recorrente = MagicMock()
            mock_queryset_recorrente.__iter__ = lambda self: iter([mock_fatura_recorrente])
            mock_queryset_recorrente.__bool__.return_value = True
            
            # Queryset final (merged)
            faturas_list = [mock_fatura_normal, mock_fatura_recorrente]
            mock_queryset_final = MagicMock()
            mock_queryset_final.count.return_value = 2
            mock_queryset_final.__iter__ = lambda self: iter(faturas_list)
            
            # Configurar OR operation
            mock_queryset_normal.__or__ = Mock(return_value=mock_queryset_final)
            
            # Configurar os retornos do filter
            def filter_side_effect(**kwargs):
                if 'compra__compra_recorrente' in kwargs:
                    return mock_queryset_recorrente
                else:
                    return mock_queryset_normal
            
            mock_fatura_class.objects.filter.side_effect = filter_side_effect
            
            # Act
            faturas, total, compras = gera_fatura(mock_request, mes=3, ano=2024)
            
            # Assert
            assert total == Decimal('195.90')  # 150.00 + 45.90
            assert compras == 2

        @patch('faturas.service.fatura_service.Fatura')
        def test_gera_fatura_sem_recorrentes(self, mock_fatura_class, mock_request):
            """Testa geração de fatura quando não há recorrentes."""
            # Arrange
            mock_fatura = Mock()
            mock_fatura.valor_parcela = Decimal('100.00')
            
            faturas_list = [mock_fatura]
            
            mock_queryset_normal = MagicMock()
            mock_queryset_normal.count.return_value = 1
            mock_queryset_normal.__iter__ = lambda self: iter(faturas_list)
            
            mock_queryset_recorrente = MagicMock()
            mock_queryset_recorrente.__bool__.return_value = False  # Queryset vazio
            
            def filter_side_effect(**kwargs):
                if 'compra__compra_recorrente' in kwargs:
                    return mock_queryset_recorrente
                else:
                    return mock_queryset_normal
            
            mock_fatura_class.objects.filter.side_effect = filter_side_effect
            
            # Act
            faturas, total, compras = gera_fatura(mock_request, mes=3, ano=2024)
            
            # Assert
            assert total == Decimal('100.00')
            assert compras == 1
            assert faturas == mock_queryset_normal

        @patch('faturas.service.fatura_service.Fatura')
        def test_gera_fatura_valores_decimais_precisos(self, mock_fatura_class, mock_request):
            """Testa precisão decimal na soma de valores."""
            # Arrange
            faturas_valores = [
                Decimal('33.33'),
                Decimal('33.33'),
                Decimal('33.34')  # Total deve ser exato: 100.00
            ]
            
            mock_faturas = []
            for valor in faturas_valores:
                mock_fatura = Mock()
                mock_fatura.valor_parcela = valor
                mock_faturas.append(mock_fatura)
            
            # Mock for normal faturas
            mock_queryset_normal = MagicMock()
            mock_queryset_normal.count.return_value = 3
            mock_queryset_normal.__iter__ = lambda self: iter(mock_faturas)
            
            # Mock for recorrentes (empty)
            mock_queryset_recorrente = MagicMock()
            mock_queryset_recorrente.__bool__.return_value = False
            
            def filter_side_effect(**kwargs):
                if 'compra__compra_recorrente' in kwargs:
                    return mock_queryset_recorrente
                else:
                    return mock_queryset_normal
            
            mock_fatura_class.objects.filter.side_effect = filter_side_effect
            
            # Act
            faturas, total, compras = gera_fatura(mock_request, mes=3, ano=2024)
            
            # Assert
            assert total == Decimal('100.00')  # Soma precisa
            assert compras == 3

        @patch('faturas.service.fatura_service.Fatura')
        def test_gera_fatura_sem_faturas_retorna_zero(self, mock_fatura_class, mock_request):
            """Testa comportamento quando não há faturas."""
            # Arrange
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 0
            mock_queryset.__iter__ = lambda self: iter([])
            mock_queryset.__bool__.return_value = False
            
            mock_fatura_class.objects.filter.return_value = mock_queryset
            
            # Act
            faturas, total, compras = gera_fatura(mock_request, mes=3, ano=2024)
            
            # Assert
            assert total == 0
            assert compras == 0
            assert faturas == mock_queryset