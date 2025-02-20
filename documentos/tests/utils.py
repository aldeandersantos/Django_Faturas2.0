import os
import json

def carregar_dados_teste(arquivo):
    caminho = os.path.join(os.path.dirname(__file__), 'data', arquivo)
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f) 