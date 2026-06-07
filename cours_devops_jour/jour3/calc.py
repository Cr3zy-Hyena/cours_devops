def calculate(a, b, op='add'):
    """Effectue une opération simple entre a et b.

    Retourne le résultat numérique, ou un dict {'error': msg} en cas d'erreur.
    """
    try:
        a = float(a)
        b = float(b)
    except (TypeError, ValueError):
        return {'error': 'Les champs a et b doivent être des nombres'}

    if op == 'add':
        return a + b
    if op == 'sub':
        return a - b
    if op == 'mul':
        return a * b
    if op == 'div':
        if b == 0:
            return {'error': 'Division par zéro'}
        return a / b

    return {'error': 'Opération inconnue'}
