# Django Faturas 2.0

## Descrição
Django Faturas 2.0 é um projeto desenvolvido em Django para a gestão de faturas. Este projeto permite criar, visualizar, editar e excluir faturas de forma eficiente e organizada.

## Funcionalidades
- Criação de faturas
- Visualização de faturas
- Edição de faturas
- Exclusão de faturas
- Pesquisa e filtragem de faturas

## Requisitos
- Python 3.10
- Django 3.10 ou superior
- SQLite (ou outro banco de dados suportado pelo Django)

## Instalação
1. Clone o repositório:
    ```sh
    git clone https://github.com/aldeandersantos/Django_Faturas2.0.git
    ```
2. Navegue até o diretório do projeto:
    ```sh
    cd django-faturas2.0
    ```
3. Crie um ambiente virtual:
    ```sh
    python -m venv venv
    ```
4. Ative o ambiente virtual:
    - No Windows:
      ```sh
      venv\Scripts\activate
      ```
    - No Linux/Mac:
      ```sh
      source venv/bin/activate
      ```
5. Instale as dependências:
    ```sh
    pip install -r requirements.txt
    ```
6. Aplique as migrações do banco de dados:
    ```sh
    python manage.py migrate
    ```
7. Inicie o servidor de desenvolvimento:
    ```sh
    python manage.py runserver
    ```

## Uso
1. Acesse o servidor de desenvolvimento no navegador:
    ```
    http://127.0.0.1:8000
    ```
2. Utilize a interface web para gerenciar suas faturas.

## Contribuição
1. Faça um fork do projeto.
2. Crie uma nova branch:
    ```sh
    git checkout -b minha-nova-funcionalidade
    ```
3. Faça suas alterações e commit:
    ```sh
    git commit -m 'Adiciona nova funcionalidade'
    ```
4. Envie para o repositório remoto:
    ```sh
    git push origin minha-nova-funcionalidade
    ```
5. Abra um Pull Request.
