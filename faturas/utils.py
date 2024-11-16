from datetime import datetime

def hoje():
    return datetime.now().strftime("%d/%m/%Y")

def hoje_ymd():
    return datetime.now().strftime("%Y-%m-%d")

def mes_ano_atual():
    mes = datetime.now().month
    ano = datetime.now().year
    return mes, ano