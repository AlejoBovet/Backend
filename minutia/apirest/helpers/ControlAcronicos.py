acronimos = {
    "PENNE TRI C C": "PASTA PENNE",
    "PENNE TRI CC": "PASTA PENNE",
    "FUSILLI TRIGD": "PASTA FUSSILI",
    "FARF TRI C CO": "PASTA FARFALLE",
    "LING TRIG C C": "PASTA LINGUINE",
    "SALCH SUR SJ": "SALCHICHA",
    "SPAG TRIDU C C": "PASTA SPAGHETTI",
    "HR MONTALVA S P":"HARINA SIN POLVO",
    "HR MONTALVA C P":"HARINA CON POLVO",
    "HR MONTBLA SP":"HARINA SIN POLVO",
    "HR MONTBLA CP":"HARINA CON POLVO",
    "HR MONTBLA C P":"HARINA CON POLVO",
    "HS SUPREME REG":"MAYONESA",
    "MAGGI SOPA":"Sopa Deshidratada carne con fideos 60 GRAMOS",
    "SOPA MAGGI":"Sopa Deshidratada Pollo con Fideos 70 gramos",
    "MINI CHORI":"SNACK DE CHORIZO",
    "SALSA C C NAT":"SALSA DE TOMATE",
    "AJI PEB CCO":"AJI PEBRE DE MESA",
    "CROQ MER 100 G ":"CROQUETAS DE MERLUZA 100 GRAMOS",
    "PASTA SALAME":"PATE DE SALAME",
    "GALL MOROCHA":"GALLETAS BANADA CON CHOCOLATE",
    "ARR G1 L AN C C":"ARROZ GRANO LARGO",
    "HALL STA ISABEL":"PAN HALLULLA",
    "AT LOM AC ANT":"ATUN LOMITO ACEITE",
    "AT LOM AC NAT":"ATUN LOMITO NATURAL",
    "HIER MANZ SUP 20 B":"TE DE MANZANILLA 20 BOLSITAS", 
    "FRAC CLASICA":"GALLETAS FRAC",
    "M M SINGLES MILK C":"M&M'S CON CHOCOLATE",
    "GALL OREO":"GALLETAS OREO",
    "PACK FIBRACTIV":"PACK BARRAS DE CEREALES",
    "LECHEENTRELAGOS4U":"LECHE ENTERA 4 UNIDADES",
    "BARRA 200G 30 UN":"BARRA DE CHOCOLATE 200G 30 UNIDADES",
    "PEPSI ZERO PET": "PEPSI ZERO 200ML",
    "COCA COLA LIGHT PE":"COCA COLA LIGHT 500ML", 
    "B.REUT.DURABAG GRA":"BOLSA DE BASURA",
    "ESPIRALES 56 POLIE":"PASTA ESPIRALES",
    "QUIROFARO N 33":"PASTA QUIROFANO",
    "QUIFARO N 33":"PASTA QUIROFANO",
    "CORBATAS N*88 ESP":"PASTA CORBATAS",
    "SALS MALL PX6":"SALSA DE TOMATE",
    "DORITOS QUESO":"NACHOS DE QUESO",
    "LAYS TA": "PAPA FRITAS LAYS",
    "AZ IANSA":"AZUCAR",
    "SPAGHETTI N 5 POLI":"PASTA SPAGHETTI",
    "SPAGHETTI N5 POLI":"PASTA SPAGHETTI",
    "ATUN LOM ACEIT CCO":"ATUN LOMITO ACEITE",
    "JUREL SAN JOSE 300":"JUREL 300 gramos",
    "SOPA POLL SEMOLA":"SOPA Deshidratada DE POLLO 60 GRAMOS",
    "MAGGI SOPA COST 60":"SOPA Deshidratada DE COSTILLA 60 GRAMOS",
    "PACK SALSA C C ITA ":"PAQUETE DE SALSA DE TOMATE 1,2 kilos",
    "HAMB SJ 90 G": "HAMBURGUESA 90 GRAMOS",
    
}

def control_acronimos(texto):
    """
    Función que reemplaza los acrónimos en el texto extraído
    :param texto: texto extraído
    :return: texto con acrónimos reemplazados
    """
    print("Texto extraído: ", texto)

    # Reemplazar acrónimos en el texto extraído
    for acronimo, completo in acronimos.items():
        texto = texto.replace(acronimo, completo)
        texto = texto.replace(acronimo.capitalize(), completo)
        texto = texto.replace(acronimo.upper(), completo)

    return texto
