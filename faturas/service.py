


def validar_compra(compra):
    if not compra.compra_parcelada and compra.parcelas != 1:
        return ('parcelas', 'Uma compra não parcelada deve ter apenas uma parcela.')

    if compra.compra_parcelada and compra.parcelas <= 1:
        return ('parcelas', 'Uma compra parcelada deve ter mais de uma parcela.')

    return None
