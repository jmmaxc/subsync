import alineamientos
import distancias

def get_acronimo_algoritmo(nombre):
    claves = list(alineamientos.ALGORITMOS.keys())
    valores = list(alineamientos.ALGORITMOS.values())
    return claves[valores.index(nombre)]


def get_distancia(nombre_clase_distancia,
                  tolerancia_desigualdad,
                  tolerancia_igualdad):
    distancia = None
    try:
        nombre_distancia = distancias.DISTANCIAS[nombre_clase_distancia]
    except:
        nombre_distancia = nombre_clase_distancia

    if nombre_distancia == distancias.Distancia.__name__:
        distancia = distancias.Distancia(tolerancia_desigualdad, tolerancia_igualdad)
    elif nombre_distancia == distancias.DistanciaPalabras.__name__:
        distancia = distancias.DistanciaPalabras(tolerancia_desigualdad, tolerancia_igualdad)
    elif nombre_distancia == distancias.DistanciaPalabrasLV.__name__:
        distancia = distancias.DistanciaPalabrasLV(tolerancia_desigualdad, tolerancia_igualdad)

    return distancia


def get_algoritmo(nombre_algoritmo_entrada,
                  distancia,
                  entropia_S,
                  entropia_ASR,
                  coste_igualdad,
                  coste_desigualdad,
                  coste_ins_subtitulo,
                  coste_ins_ASR):
    algoritmo = None

    try:
        nombre_algoritmo = alineamientos.ALGORITMOS[nombre_algoritmo_entrada]
    except:
        nombre_algoritmo = nombre_algoritmo_entrada

    if nombre_algoritmo == alineamientos.AlineamientoSW.__name__:
        algoritmo = alineamientos.AlineamientoSW(distancia,
                                                 entropia_S,
                                                 entropia_ASR,
                                                 coste_igualdad=coste_igualdad,
                                                 coste_desigualdad=coste_desigualdad,
                                                 C_subtitulo_S=coste_ins_subtitulo,
                                                 C_transcripcion_T=coste_ins_ASR, )
    elif nombre_algoritmo == alineamientos.AlineamientoNW.__name__:
        algoritmo = alineamientos.AlineamientoNW(distancia,
                                                 entropia_S,
                                                 entropia_ASR,
                                                 coste_igualdad=coste_igualdad,
                                                 coste_desigualdad=coste_desigualdad,
                                                 C_subtitulo_S=coste_ins_subtitulo,
                                                 C_transcripcion_T=coste_ins_ASR, )
    elif nombre_algoritmo == alineamientos.AlineamientoLV.__name__:
        algoritmo = alineamientos.AlineamientoLV(distancia,
                                                 entropia_S,
                                                 entropia_ASR,
                                                 coste_igualdad=coste_igualdad,
                                                 coste_desigualdad=coste_desigualdad,
                                                 C_subtitulo_S=coste_ins_subtitulo,
                                                 C_transcripcion_T=coste_ins_ASR, )
    elif nombre_algoritmo == alineamientos.AlineamientoLiterales.__name__:
        algoritmo = alineamientos.AlineamientoLiterales(distancia,
                                                        entropia_S,
                                                        entropia_ASR,
                                                        coste_igualdad=coste_igualdad,
                                                        coste_desigualdad=coste_desigualdad,
                                                        C_subtitulo_S=coste_ins_subtitulo,
                                                        C_transcripcion_T=coste_ins_ASR, )
    elif nombre_algoritmo == alineamientos.AlineamientoMultiple.__name__:
        algoritmo = alineamientos.AlineamientoMultiple(distancia,
                                                       entropia_S,
                                                       entropia_ASR,
                                                       coste_igualdad=coste_igualdad,
                                                       coste_desigualdad=coste_desigualdad,
                                                       C_subtitulo_S=coste_ins_subtitulo,
                                                       C_transcripcion_T=coste_ins_ASR, )
    return algoritmo
