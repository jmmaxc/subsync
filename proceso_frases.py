# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 14:54:35 2020

@author: max
"""
import re
from presentacion import imprimir


FMT_CSV_PALABRA = "Pal.,{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n"
FMT_CSV_CABECERA_PALABRA = "Info,{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n"
FMT_CSV_FRASE = "Frase, {0},{1}"

FMT_PANTALLA_PALABRA = "Pal.  {0:^15}{1:^10}{2:^10}{3:^15}{4:^10}{5:^10.2f}" \
                       "{6:^10}{7:^10}{8:^10}{9:^10}{10:^10}{10:^10}"
FMT_PANTALLA_CABECERA_PALABRA = "Info. {0:^15}{1:^10}{2:^10}{3:^15}{4:^10}{5:^10}" \
                                "{6:^10}{7:^10}{8:^10}{9:^10}{10:^10}{11:^10}"
FMT_PANTALLA_FRASE = "Frase {0} {1}"


def elimina_tildes(cadena):
    a, b = 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'
    trans = str.maketrans(a, b)
    return cadena.translate(trans)


def deja_linea_plana(cadena):
    #
    # quitamos los retorno de carro
    #
    quita_formato = re.compile(r'\<.*?>')
    quita_caracteres_control = re.compile(r'\W')
    deja_un_espacio = re.compile(r'  *')
    retorno = quita_formato.sub(" ", cadena)
    retorno = quita_caracteres_control.sub(" ", retorno)
    retorno = deja_un_espacio.sub(" ", retorno).strip()
    return elimina_tildes(retorno).lower()


class Palabras:

    def __init__(self, *args):
        self.palabra_str = args[0]
        self.repeticiones = args[1]
        self.posicion = args[2]
        self.instante = args[3]
        self.instante_original = self.instante
        self.confianza = args[4]
        self.posicion_repeticion = args[5]
        self.offset = args[6]
        self.numero_comprobaciones = 0
        self.veces_encontrada = 0
        self.veces_no_encontrada = 0
        self.pendiente_ordenar = False
        self.debug = "Nueva"
        self.nueva = True
        self.perdida = False
        self.palabra_antigua = None

    def __len__(self):
        return len(self.palabra_str)

    def estadoPalabra(self, formato):
        # salida = "Pal. \t{0:<10}{1}{1:10}{2}{1:15}{3}{1:15}\
        #        {4}{:5.2f}{5}{1:15}{6}{1:15}{7}{1:15}{8}{1:15}{9}{1:15}{10}{1:15}{11}\n"
        salida = formato.format(
            self.palabra_str,
            self.repeticiones,
            self.posicion,
            self.instante,
            self.instante_original,
            self.confianza,
            self.posicion_repeticion,
            self.numero_comprobaciones,
            self.veces_encontrada,
            self.veces_no_encontrada,
            self.pendiente_ordenar,
            self.debug)
        return (salida)

    def get_estado_palabra(self):
        salida = [
            "Palabra",
            self.palabra_str,
            self.repeticiones,
            self.posicion,
            self.instante,
            self.instante_original,
            self.confianza,
            self.posicion_repeticion,
            self.numero_comprobaciones,
            self.veces_encontrada,
            self.veces_no_encontrada,
            self.pendiente_ordenar,
            self.debug]
        return (salida)

    @classmethod
    def cabeceraPalabra(cls, formato):
        salida = formato.format(
            "pal.",
            "rep.",
            "pos.",
            "inst.",
            "inst_o",
            "conf.",
            "p_rep.",
            "n_comp.",
            "enc.",
            "no_enc.",
            "pend.",
            "debug")
        return (salida)


class Frase:
    def __init__(self, frase_str, instante, confianza, es_final, aplana_frase=True, offset=0):

        self.es_final = es_final
        self.es_final_forzado = False
        self.frase_str = frase_str if not aplana_frase else deja_linea_plana(frase_str)
        self.instante_creacion = instante  # El instante de creacion de la frase
        self.instante_inicial = instante  # el instante de la palabra mas baja
        self.instante_final = instante  # Este hay que actualizarlo siempre que se incorpora informacion
        self.confianza = confianza
        self.h_frase_str = []
        self.h_instante = []
        self.h_confianza = []
        self.h_frase_str.append(frase_str)  # tal cual lo manda el ASR
        self.h_instante.append(instante)
        self.h_confianza.append(confianza)
        self.lista_palabras = []
        self.lista_palabras_total = []
        self.lista_palabras_perdidas = []

        if self.frase_str == "":
            self.esta_vacia = True
            return

        self.esta_vacia = False
        split_palabras = self.frase_str.split()

        try:
            posicion, w = zip(*enumerate(split_palabras))
        except ValueError:
            raise ValueError(f"Error creacion frase: {frase_str}")

        lista_palabras = [list(a) for a in zip(
            split_palabras,  # Lista con los textos de las palabras
            [split_palabras.count(w) for w in split_palabras],  # numero de veces que se repite la palabra
            posicion,  # posicion de la palabra en el split
            [instante] * len(split_palabras),  # Se asigna el mismo instante a todas las palabras de la frase
            [confianza] * len(split_palabras),  # se asigna la misma confianza
            [0] * len(split_palabras),  # esto es la posicion de cada repeticion
            [offset] * len(split_palabras))]  # se asgina el mismo offset

        self.lista_palabras = [Palabras(*f) for f in
                               lista_palabras]  # crea todos los objetos Palabra a partir de la lista
        self.asigna_posicion_duplicado_palabras()
        self.lista_palabras_total = [w for w in self.lista_palabras]

    def incorpora_frase(self, frase, es_final, pierde_palabras):


        if (self.es_final):
            raise Exception("Error")

        self.h_frase_str.append(frase.frase_str)
        self.h_instante.append(frase.instante_final)
        self.h_confianza.append(frase.confianza)

        self.es_final = es_final

        palabras_nuevas, palabras_no_nuevas = self.busca_coincidencias_en_frase(frase)
        palabras_perdidas, palabras_conocidas = frase.busca_coincidencias_en_frase(self)

        for w_nueva, w_antigua in [(w_no_nueva, w_conocida) for w_no_nueva in palabras_no_nuevas
                                   for w_conocida in palabras_conocidas
                                   if w_conocida.palabra_str == w_no_nueva.palabra_str and
                                      w_conocida.posicion_repeticion == w_no_nueva.posicion_repeticion]:

            w_nueva.palabra_antigua = w_antigua
            w_nueva.nueva = False
            w_antigua.confianza = w_nueva.confianza
            w_antigua.veces_encontrada += 1
            w_antigua.numero_comprobaciones += 1
            w_antigua.debug = "Conocida"
            w_antigua.nueva = False
            w_antigua.perdida = False
            if w_antigua.posicion != w_nueva.posicion:
                w_antigua.pendiente_ordenar = True
                w_nueva.pendiente_ordenar = True

        for w in palabras_perdidas:
            self.lista_palabras.remove(w)
            self.lista_palabras_perdidas.append(w)
            w.perdida = True

        palabras_nuevas = [w for w in frase.lista_palabras if w.nueva]

        for w in palabras_nuevas:
            indice = frase.lista_palabras.index(w)
            try:
                for w_derecha in frase.lista_palabras[indice + 1:]:
                    if not w_derecha.nueva:
                        palabra_antigua = w_derecha.palabra_antigua
                        w.instante = palabra_antigua.instante
                        indice_palabra_antigua = self.lista_palabras.index(palabra_antigua)
                        self.lista_palabras.insert(indice_palabra_antigua, w)
                        break
                else:
                    self.lista_palabras.append(w)
            except:
                pass

        self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])

        self.asigna_posicion_duplicado_palabras()
        for posicion, palabra_perdida in enumerate(self.lista_palabras):
            palabra_perdida.posicion = posicion

        self.set_instante()

    def get_ultimas_incorporaciones(self, numero_de_cambios=1):


        cambios = 1
        try:
            instante = self.lista_palabras[-1].instante
        except IndexError:
            instante = 0

        lista = []
        for w in reversed(self.lista_palabras):
            if not w.instante == instante:
                cambios += 1
                if cambios > numero_de_cambios:
                    break
                instante = w.instante
            lista.append(w)

        retorno = ' '.join([w.palabra_str for w in reversed(lista)])
        return retorno

    def set_instante(self):

        if self.lista_palabras is not None:
            try:
                self.instante_inicial = self.lista_palabras[0].instante
                self.instante_final = self.lista_palabras[-1].instante
            except IndexError:
                pass
        return

    def get_instante_inicial(self):
        return self.instante_inicial

    def get_instante_final(self):
        return self.instante_final

    def get_instante1(self):

        instante = 0
        if self.lista_palabras is not None:
            try:
                instante = self.lista_palabras[0].instante
            except IndexError:
                instante = self.instante
        return instante

    def get_confianza(self):

        confianza = self.confianza
        for w in self.lista_palabras:
            if w.confianza > confianza:
                confianza = w.confianza

        return confianza

    def organiza_tiempos_palabras(self):

        #
        # Analizamos como encaja el tiempo de las Nuevas
        # Hay que tener en cuenta que las viejas se supone que estan arregladas
        # y que las nuevas entran todas con el mismo tiempo
        #
        for i in range(len(self.lista_palabras) - 1, 0, -1):
            if self.lista_palabras[i].instante < self.lista_palabras[i - 1].instante:
                self.lista_palabras[i - 1].instante = self.lista_palabras[i].instante

    def busca_coincidencias_en_frase(self, frase):


        palabras_no_coincidentes = []
        palabras_coincidentes = []
        for w_nueva in frase.lista_palabras:
            encontrada = False
            for w_actual in self.lista_palabras:
                if w_nueva.palabra_str == w_actual.palabra_str and \
                        w_nueva.posicion_repeticion == w_actual.posicion_repeticion:
                    palabras_coincidentes.append(w_nueva)
                    encontrada = True
                    break
            if not encontrada:
                palabras_no_coincidentes.append(w_nueva)
        return palabras_no_coincidentes, palabras_coincidentes

    def asigna_posicion_duplicado_palabras(self):

        for s in set(w.palabra_str for w in self.lista_palabras):
            cont = len([w for w in self.lista_palabras if w.palabra_str == s])
            orden = 0
            for w in [w for w in self.lista_palabras if w.palabra_str == s]:
                w.repeticiones = cont
                w.posicion_repeticion = orden
                orden = orden + 1

    def estadoFrase(self, fd=None):

        if self.es_final:
            final = "Final"
        elif not self.es_final:
            final = "No final"
        else:
            final = "None"

        cabecera = f"Frase,{final},{self.frase_str} \n" + Palabras.cabeceraPalabra(FMT_CSV_CABECERA_PALABRA)
        imprimir(f"\nFrase\t{final}\t{self.frase_str} \n" + \
                 Palabras.cabeceraPalabra(FMT_PANTALLA_CABECERA_PALABRA))

        if fd is not None:
            fd.write(cabecera)

        for w in self.lista_palabras:

            imprimir(w.estadoPalabra(FMT_PANTALLA_PALABRA))
            if fd is not None:
                fd.write(w.estadoPalabra(FMT_CSV_PALABRA))

    def generador_palabras_frase(self):

        for w in self.lista_palabras:
            yield w.get_estado_palabra()


class FraseASR(Frase):


    def __init__(self, frase, palabra_corte=None, lado_izquierdo=False):



        if frase is None:  # Hemos creado una vacia
            super().__init__("", 0, 0, False, 0)
            self.esta_vacia = True
            return

        super().__init__("", frase.instante_creacion, frase.confianza, frase.es_final)
        self.instante_inicial = frase.instante_inicial
        self.instante_final = frase.instante_final

        if palabra_corte is None:

            self.lista_palabras = [w for w in frase.lista_palabras]
            self.lista_palabras_perdidas = [w for w in frase.lista_palabras_perdidas]
            self.esta_vacia = False
            self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])

        else:
            try:
                posicion_derecha = frase.lista_palabras.index(palabra_corte)
                posicion_izquierda = posicion_derecha + 1
                self.lista_palabras = [w for w in frase.lista_palabras[:posicion_izquierda]] \
                    if lado_izquierdo else [w for w in frase.lista_palabras[posicion_derecha:]]

                self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])
                self.es_final = frase.es_final
                self.esta_vacia = False
            except ValueError:
                self.lista_palabras = [] \
                    if not lado_izquierdo else frase.lista_palabras
                self.esta_vacia = False

        self.set_instante()
        self.confianza = frase.confianza

    def quita_palabra(self, palabra):
        try:
            self.lista_palabras.remove(palabra)
            if len(self.lista_palabras) == 0:
                self.esta_vacia = True
            else:
                self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])
                self.set_instante()
                self.confianza = self.get_confianza()
        except ValueError:
            return

    def set_palabra_de_corte(self, palabra_corte):
        try:
            posicion_derecha = self.lista_palabras.index(palabra_corte)
            self.lista_palabras = [w for w in self.lista_palabras[posicion_derecha:]]
            self.confianza = self.get_confianza()
        except ValueError:
            self.lista_palabras = []

        self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])
        self.set_instante()

    def incorpora_frase(self, frase, es_final, pierde_palabras):
        raise NotImplementedError("Esta subclase no tiene este metodo")

    def une_frase_ASR(self, frase_derecha, palabra_corte=None):


        if frase_derecha is not None:
            self.h_frase_str.append(frase_derecha.frase_str)
            self.h_instante.append(frase_derecha.instante_creacion)
            self.h_confianza.append(frase_derecha.confianza)

        if palabra_corte is not None:
            try:
                indice_palabra_corte = self.lista_palabras.index(palabra_corte)
                self.lista_palabras = [w for w in self.lista_palabras[indice_palabra_corte:]]
                if frase_derecha is not None:
                    self.lista_palabras = self.lista_palabras + frase_derecha.lista_palabras
            except ValueError:
                if frase_derecha is not None:
                    try:
                        indice_palabra_corte = frase_derecha.lista_palabras.index(palabra_corte)
                        self.lista_palabras = frase_derecha.lista_palabras[indice_palabra_corte:]
                    except ValueError:
                        self.lista_palabras = frase_derecha.lista_palabras
                else:
                    self.lista_palabras = []
        else:
            if frase_derecha is not None:
                self.lista_palabras = self.lista_palabras + frase_derecha.lista_palabras

        if len(self.lista_palabras) == 0:
            self.esta_vacia = True

        self.organiza_tiempos_palabras()
        self.frase_str = ' '.join([w.palabra_str for w in self.lista_palabras])
        self.set_instante()
        self.confianza = self.get_confianza()

    def get_frase_analisis(self, frase, palabra_corte=None):


        frase_ret = FraseASR(self)
        if frase_ret is None:
            raise ValueError

        frase_ret.une_frase_ASR(frase, palabra_corte)

        frase_ret.set_instante()
        frase_ret.confianza = frase_ret.get_confianza()

        return frase_ret

    def split_palabras(self, inicial, final):


        frase_izquierda = FraseASR(self, palabra_corte=inicial, lado_izquierdo=True)
        if final is None:
            frase_central = FraseASR(None)  # Si no hay final la fase central esta vacia
        else:
            frase_central = FraseASR(self, palabra_corte=inicial, lado_izquierdo=False)
            frase_central = FraseASR(frase_central, palabra_corte=final, lado_izquierdo=True)

        self.set_palabra_de_corte(palabra_corte=inicial if final is None else final)
        self.set_instante()
        self.confianza = self.get_confianza()

        if frase_izquierda is not None:
            frase_izquierda.set_instante()
            frase_izquierda.confianza = frase_izquierda.get_confianza()

        if frase_central is not None:
            frase_central.set_instante()
            frase_central.confianza = frase_central.get_confianza()

        return frase_izquierda, frase_central


class Frases:
    NOMBRE_CAMPOS_FRASE = ["IdFrase", "Final", "Final Forzado", "Texto"]
    FMT_CAMPOS_FRASE = len(NOMBRE_CAMPOS_FRASE) * ["{}"]
    NOMBRE_CAMPOS_PALABRAS = ["pal.",
                              "rep.",
                              "pos.",
                              "inst.",
                              "inst_o",
                              "conf.",
                              "p_rep.",
                              "n_comp.",
                              "enc.",
                              "no_enc.",
                              "pend.",
                              "debug"]
    FMT_CAMPOS_PALABRAS = len(NOMBRE_CAMPOS_PALABRAS) * ["{}"]



    def __init__(self):
        self.frase_activa = None
        self.frases = []
        self.secuencia_corte = None
        self.palabra_corte = None
        self.siguiente_palabra = False

        self.frase_ASR = FraseASR(None)

    def add_frase(self, frase, es_final, pierde_palabras):


        if frase.es_final != es_final:
            raise ValueError("Error consistencia en cuanto a si la frase es final o no ")



        if self.frase_activa is None:
            self.frase_activa = frase
        else:
            self.frase_activa.incorpora_frase(frase, es_final, pierde_palabras)  # la unimos y colocamos los tiempos

        if frase.es_final:

            self.frase_activa.es_final = True

            #
            # A la frase_ASR solo se incorporan las frases finales
            # La frase que se usa para el proyecto son las frases que se construyen a partir
            # de la frase_ASR y la que en ese momento este active
            #
            if self.frase_ASR is None:
                self.frase_ASR = FraseASR(self.frase_activa)
                imprimir("No debe PASAR POR AQUI")
            else:
                self.frase_ASR.une_frase_ASR(self.frase_activa)

            self.frases.append(self.frase_activa)
            self.frase_activa = None


    def set_palabra_de_corte_frases(self, palabra_corte, siguiente=False):
        self.palabra_corte = palabra_corte
        self.siguiente_palabra = siguiente

    def get_frase_ASR(self):
        if self.frase_ASR is None:
            imprimir("NO DEBE PASAR POR AQUI")
            return FraseASR(self.frase_activa)
        else:
            palabra_corte = self.palabra_corte
            indice = None
            frase = self.frase_ASR
            try:
                indice = frase.lista_palabras.index(palabra_corte)
            except ValueError:
                frase = self.frase_activa
                if frase is not None:
                    frase = self.frase_activa
                    try:
                        indice = frase.lista_palabras.index(palabra_corte)
                    except ValueError:
                        frase = None
            if frase is not None and indice is not None:
                try:
                    palabra_corte = frase.lista_palabras[indice + 1]
                except IndexError:
                    palabra_corte = self.palabra_corte

            return self.frase_ASR.get_frase_analisis(self.frase_activa, palabra_corte=palabra_corte)

    def generador_frases_asr(self, quita_palabra_corte=False):

        ultima_palabra_corte = self.palabra_corte
        while True:
            frase_asr = self.get_frase_ASR()
            if len(frase_asr.lista_palabras) == 0:
                if not frase_asr.esta_vacia:
                    print("ERROR FRASE VACIA")
                break
            if quita_palabra_corte:
                if frase_asr.lista_palabras[0] == ultima_palabra_corte:
                    frase_asr.lista_palabras = frase_asr.lista_palabras[1:]
                    frase_asr.frase_str = ' '.join([w.palabra_str for w in frase_asr.lista_palabras])
                    if len(frase_asr.lista_palabras) == 0:
                        frase_asr.esta_vacia = True

            frase_asr.set_instante()
            frase_asr.confianza = frase_asr.get_confianza()
            yield frase_asr
            if self.palabra_corte == ultima_palabra_corte:
                break
            ultima_palabra_corte = self.palabra_corte
        return

    def finaliza(self):
        if self.frase_activa is not None:
            self.frase_activa.es_final = True
            self.frases.append(self.frase_activa)
            self.frase_activa = None

    def imprime_frases(self, fd=None):
        for f in self.frases:
            f.estadoFrase(fd)

        for f in self.frases:
            salida = ' '.join(w.palabra_str for w in f.lista_palabras)
            fd.write(salida + "\n")

    def generador_palabras_frases(self):

        id_frase = 0
        for f in self.frases:
            for w in f.generador_palabras_frase():
                w.insert(0, id_frase)
                yield w
            id_frase += 1

    def generador_frases(self):

        id_frase = 0
        for f in self.frases:
            yield [id_frase, f.es_final, f.es_final_forzado, f.frase_str]
            id_frase += 1
