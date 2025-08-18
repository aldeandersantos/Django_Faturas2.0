import pytest
from unittest.mock import Mock, patch, MagicMock

from faturas.service.usuario_service import registra_usuario


class TestUsuarioServiceValidations:
    """
    Testes unitários para validações do serviço de usuário.
    Todos os testes são mockados e não afetam o banco de dados.
    """

    @pytest.fixture
    def mock_request(self):
        """Cria um mock de request básico."""
        request = Mock()
        request.method = 'POST'
        request.POST = {}
        return request

    @pytest.fixture
    def mock_messages(self):
        """Mock para o sistema de messages do Django."""
        with patch('faturas.service.usuario_service.messages') as mock_msg:
            yield mock_msg

    class TestRegistraUsuarioValidations:
        """Testes das validações de registro de usuário."""

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_sucesso_gera_username_correto(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa geração correta do username a partir do email."""
            # Arrange
            mock_request.POST = {
                'first_name': 'João',
                'last_name': 'Silva',
                'email': 'joao.silva@email.com',
                'password1': 'senha123',
                'password2': 'senha123'
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado is None  # Sucesso retorna None
            
            # Verifica se create_user foi chamado com username correto
            mock_user_class.objects.create_user.assert_called_once_with(
                username='joao.silva',  # Parte antes do @ do email
                first_name='João',
                last_name='Silva',
                email='joao.silva@email.com',
                password='senha123'
            )
            
            mock_user_instance.save.assert_called_once()
            mock_messages.success.assert_called_once_with(
                mock_request, 'Usuário registrado com sucesso!'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_email_complexo_username_correto(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa geração de username com email complexo."""
            # Arrange
            mock_request.POST = {
                'first_name': 'Maria',
                'last_name': 'Santos',
                'email': 'maria.santos.oliveira@empresa.com.br',
                'password1': 'senha456',
                'password2': 'senha456'
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            mock_user_class.objects.create_user.assert_called_once_with(
                username='maria.santos.oliveira',  # Parte antes do primeiro @
                first_name='Maria',
                last_name='Santos',
                email='maria.santos.oliveira@empresa.com.br',
                password='senha456'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_senhas_diferentes_retorna_erro(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa validação de senhas diferentes."""
            # Arrange
            mock_request.POST = {
                'first_name': 'João',
                'last_name': 'Silva',
                'email': 'joao@email.com',
                'password1': 'senha123',
                'password2': 'senha456'  # Senha diferente
            }
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado == mock_request  # Erro retorna o request
            
            # Não deve tentar criar usuário
            mock_user_class.objects.create_user.assert_not_called()
            
            # Deve mostrar erro
            mock_messages.error.assert_called_once_with(
                mock_request, 'As senhas não coincidem!'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_email_existente_retorna_erro(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa validação de email já existente."""
            # Arrange
            mock_request.POST = {
                'first_name': 'João',
                'last_name': 'Silva',
                'email': 'joao@email.com',
                'password1': 'senha123',
                'password2': 'senha123'
            }
            
            # Email já existe
            mock_user_class.objects.filter.return_value.exists.return_value = True
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado == mock_request  # Erro retorna o request
            
            # Verifica se consultou email existente
            mock_user_class.objects.filter.assert_called_once_with(
                email='joao@email.com'
            )
            
            # Não deve tentar criar usuário
            mock_user_class.objects.create_user.assert_not_called()
            
            # Deve mostrar erro
            mock_messages.error.assert_called_once_with(
                mock_request, 'Este email já está registrado!'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_senha_vazia_nao_causa_erro_interno(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa comportamento com senha vazia."""
            # Arrange
            mock_request.POST = {
                'first_name': 'João',
                'last_name': 'Silva',
                'email': 'joao@email.com',
                'password1': '',
                'password2': ''
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            # Senhas iguais (mesmo que vazias) não deve dar erro de validação
            assert resultado is None
            
            # Deve tentar criar usuário
            mock_user_class.objects.create_user.assert_called_once_with(
                username='joao',
                first_name='João',
                last_name='Silva',
                email='joao@email.com',
                password=''
            )

        def test_registra_usuario_metodo_nao_post_retorna_request(self, mock_request):
            """Testa comportamento com método diferente de POST."""
            # Arrange
            mock_request.method = 'GET'
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado == mock_request

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_campos_opcionais_vazios(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa criação com campos opcionais vazios."""
            # Arrange
            mock_request.POST = {
                'first_name': '',  # Vazio
                'last_name': '',   # Vazio
                'email': 'usuario@email.com',
                'password1': 'senha123',
                'password2': 'senha123'
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado is None
            
            mock_user_class.objects.create_user.assert_called_once_with(
                username='usuario',
                first_name='',
                last_name='',
                email='usuario@email.com',
                password='senha123'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_email_com_subdominios_username_correto(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa username com email que tem subdomínios."""
            # Arrange
            mock_request.POST = {
                'first_name': 'Ana',
                'last_name': 'Costa',
                'email': 'ana.costa+trabalho@mail.empresa.com.br',
                'password1': 'senha789',
                'password2': 'senha789'
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            mock_user_class.objects.create_user.assert_called_once_with(
                username='ana.costa+trabalho',  # Tudo antes do @
                first_name='Ana',
                last_name='Costa',
                email='ana.costa+trabalho@mail.empresa.com.br',
                password='senha789'
            )

        @patch('faturas.service.usuario_service.User')
        def test_registra_usuario_email_valido_com_formato_correto(
            self, mock_user_class, mock_request, mock_messages
        ):
            """Testa comportamento com email válido bem formatado."""
            # Arrange
            mock_request.POST = {
                'first_name': 'Carlos',
                'last_name': 'Oliveira',
                'email': 'carlos@empresa.com',
                'password1': 'senha123',
                'password2': 'senha123'
            }
            
            mock_user_class.objects.filter.return_value.exists.return_value = False
            mock_user_instance = Mock()
            mock_user_class.objects.create_user.return_value = mock_user_instance
            
            # Act
            resultado = registra_usuario(mock_request)
            
            # Assert
            assert resultado is None
            
            mock_user_class.objects.create_user.assert_called_once_with(
                username='carlos',
                first_name='Carlos',
                last_name='Oliveira',
                email='carlos@empresa.com',
                password='senha123'
            )