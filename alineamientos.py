import numpy as np
import presentacion
import factory


class Matriz_S:

    def __init__(self, distancia, coste_desigualdad=1, coste_igualdad=0):

        self.coste_desigualdad = coste_desigualdad
        self.coste_igualdad = coste_igualdad
        self.__distancia = distancia
        self.subtitulo_S = None
        self.transcripcion_T = None
        self.__matriz = None


    def get(self,
            subtitulo_S,
            transcripcion_T,
            coste_igualdad=None,
            coste_desigualdad=None):

        self.subtitulo_S = subtitulo_S
        self.transcripcion_T = transcripcion_T

        if coste_desigualdad is not None:
            self.coste_desigualdad = coste_desigualdad
        if coste_igualdad is not None:
            self.coste_igualdad = coste_igualdad


        try:
            l_t = len(self.transcripcion_T)
            l_s = len(self.subtitulo_S)
        except ValueError:
            raise ValueError(f"Error en las longitudes de las secuencias")

        self.__matriz = np.zeros((l_s + 1, l_t + 1), dtype=float)
        self.__calcula_matriz()
        return self.__matriz

    def get_distancias(self,
                       subtitulo_S,
                       transcripcion_T,
                       coste_igualdad=None,
                       coste_desigualdad=None):

        self.subtitulo_S = subtitulo_S
        self.transcripcion_T = transcripcion_T

        if coste_desigualdad is not None:
            self.coste_desigualdad = coste_desigualdad
        if coste_igualdad is not None:
            self.coste_igualdad = coste_igualdad


        try:
            l_t = len(self.transcripcion_T)
            l_s = len(self.subtitulo_S)
        except ValueError:
            raise ValueError("Error en las longitudes de las secuencias")

        matriz_distancias = np.zeros((l_s, l_t), dtype=float)
        fila = 0
        for palabra_s in self.subtitulo_S:  # la secuencia_S define las filas
            columna = 0
            for palabra_t in self.transcripcion_T:  # la secuencia_T define las columnas
                matriz_distancias[fila, columna] = self.__distancia.get(palabra_s, palabra_t)
                columna += 1
            fila += 1

        return matriz_distancias

    def set_distancia(self, distancia, coste_igualdad, coste_desigualdad):
        self.coste_desigualdad = coste_desigualdad
        self.coste_igualdad = coste_igualdad
        self.__distancia = distancia

    def __calcula_matriz(self):

        cd = self.coste_desigualdad - self.coste_igualdad
        fila = 1
        for palabra_s in self.subtitulo_S:
            columna = 1
            for palabra_t in self.transcripcion_T:
                self.__matriz[fila, columna] = self.coste_igualdad + \
                                               cd * self.__distancia.get(palabra_s, palabra_t)
                columna += 1
            fila += 1


class Alineamiento:

    def __init__(self, distancia, entropia_subtitulo_S,
                 entropia_transcripcion_T=None, coste_igualdad=0, coste_desigualdad=1,
                 C_subtitulo_S=1, C_transcripcion_T=1):

        self.minimizando = False
        self.coste_desigualdad = coste_desigualdad
        self.coste_igualdad = coste_igualdad
        self.C_subtitulo_S = C_subtitulo_S
        self.C_transcripcion_T = C_transcripcion_T
        self.distancia = distancia
        self.entropia_subtitulo_S = entropia_subtitulo_S
        self.entropia_transcripcion_T = \
            entropia_transcripcion_T if entropia_transcripcion_T is not None else entropia_subtitulo_S

        self.matriz_s = Matriz_S(distancia,
                                 self.coste_desigualdad,
                                 self.coste_igualdad)


        self.secuencia_transcripcion_T = []
        self.secuencia_subtitulo_S = []
        self.distancias_S = None
        self.score_alineamiento = 0
        self.primer_elemento_subtitulo_alineado = None
        self.score_pareja = []
        self.distancia_pareja = []
        self.iguales = 0
        self.distintas = 0
        self.insercion = 0
        self.insercion_subtitulo = 0
        self.insercion_asr = 0
        self.score_alineamiento = 0
        self.asimetria = True
        self.longitud_acumulada = 0
        self.longitud_S = 0
        self.longitud_T = 0

        #
        # Calculados en la funcion de implementacion especifica
        #
        self.coste_F = None
        self.traceback_T = None
        self.coste = 0
        self.alineamiento_transcripcion_T = []
        self.alineamiento_subtitulo_S = []
        self.acronimo_algoritmo = factory.get_acronimo_algoritmo(self.__class__.__name__)
        self.algoritmo_usado = self.acronimo_algoritmo

    def get_configuracion(self):
        """
        :returns    devuelve una lista de pares nombre_parametro, valor con los valores de configuracion
        """
        lista_configuracion = [
            ["Algoritmo", self.__class__.__name__],
            ["Coste desigualdad", self.coste_desigualdad],
            ["Coste igualdad", self.coste_igualdad],
            ["Coste Subtitulo", self.C_subtitulo_S],
            ["Coste Transcipcion", self.C_transcripcion_T],
            ["Distancia", self.distancia.get_configuracion()],
            ["Entropia subtitulo", self.entropia_subtitulo_S.get_configuracion()],
            ["Entropia transcripcion", self.entropia_transcripcion_T.get_configuracion()],

        ]
        return lista_configuracion

    def get_parametros(self):
        """
        :returns    devuelve una lista de pares nombre_parametro, valor con los valores de configuracion
        """
        lista_parametros = [
            ["Algoritmo", self.__class__.__name__],
            ["Coste desigualdad", self.coste_desigualdad],
            ["Coste igualdad", self.coste_igualdad],
            ["Coste Subtitulo", self.C_subtitulo_S],
            ["Coste Transcripcion", self.C_transcripcion_T],
            ["Lng minima palabras", self.C_transcripcion_T],
        ]
        #
        # Realmente como parametros de entropia tendríamos 2, la longitud de cada
        # una de las entropias, aunque lo logico es que la entropia sea comun en ambos
        #
        #
        return lista_parametros + self.entropia_subtitulo_S.get_parametros()

    #
    # Este es el metodo que construye las matrices F y T segun el algoritmo que implemente
    #
    def _impl_coste_alineamiento(self):
        raise NotImplementedError("Clase abstracta, falta implementacion")

    def calcula_similitud(self, subtitulo, transcripcion, asimetria=None):


        self.secuencia_subtitulo_S = self.entropia_subtitulo_S.pasa_filtro(subtitulo)
        self.secuencia_transcripcion_T = self.entropia_transcripcion_T.pasa_filtro(transcripcion)

        self.iguales = 0
        self.distintas = 0
        self.insercion = 0
        self.insercion_subtitulo = 0
        self.insercion_asr = 0
        self.primer_elemento_subtitulo_alineado = None
        self.ultimo_elemento_subtitulo_alineado = None
        self.primer_elemento_asr_alineado = None
        self.ultimo_elemento_asr_alineado = None
        self.score_alineamiento = 0
        self.score_pareja = []
        self.distancia_pareja = []
        self.longitud_acumulada = 0
        self.longitud_S = 0
        self.longitud_transcripcion_asociada = 0
        self.longitud_subtitulo_asociado = 0
        self.score_no_alineamiento_transcripcion = 0

        for w in self.secuencia_subtitulo_S:
            self.longitud_S += len(w)
        self.longitud_T = 0
        for w in self.secuencia_transcripcion_T:
            self.longitud_T += len(w)

        if self.longitud_S == 0 or self.longitud_T == 0:
            self.score_alineamiento = 0
            return



        self.distancias_S = self.matriz_s.get(self.secuencia_subtitulo_S,
                                              self.secuencia_transcripcion_T,
                                              self.coste_igualdad,
                                              self.coste_desigualdad)

        if asimetria is not None:
            self.asimetria = asimetria


        self._impl_coste_alineamiento()


        self.longitud_transcripcion_asociada = self.get_longitud_transcripcion_asociada()
        self.longitud_transcripcion_asociada = 0
        score_acumulado = 0
        alineamientos = zip(self.alineamiento_subtitulo_S,
                            self.alineamiento_transcripcion_T, )
        for subtitulo, transcripcion in alineamientos:
            score_pareja = 0
            distancia_pareja = 1
            if subtitulo is None:
                if transcripcion is not None:
                    self.insercion_subtitulo += 1
            else:

                if transcripcion is not None:
                    self.ultimo_elemento_asr_alineado = transcripcion
                    self.ultimo_elemento_subtitulo_alineado = subtitulo
                    score_pareja = self.distancia.score(subtitulo, transcripcion)
                    distancia_pareja = self.distancia.get(subtitulo, transcripcion)
                    score_acumulado += score_pareja  # En score acumulado esta la longitud de los coincidentes
                    if score_pareja != 0 and self.primer_elemento_subtitulo_alineado is None:
                        self.primer_elemento_subtitulo_alineado = subtitulo
                        self.primer_elemento_asr_alineado = transcripcion

                    if self.distancia.get(subtitulo, transcripcion) == 0:
                        self.longitud_acumulada += len(subtitulo)  # la longitud total alineada de los que son iguales
                        self.iguales += 1
                    else:
                        self.distintas += 1
                else:
                    self.insercion_asr += 1
            self.score_pareja.append(score_pareja)
            self.distancia_pareja.append(distancia_pareja)

        try:

            self.longitud_transcripcion_asociada = self.get_longitud_transcripcion_asociada()
            self.longitud_subtitulo_asociado = self.get_longitud_subtitulo_asociado()

            # self.score_alineamiento = score_acumulado / min(self.longitud_S, self.longitud_T)
            self.score_alineamiento = \
                2 * score_acumulado / (self.longitud_S + self.longitud_transcripcion_asociada)
            self.score_no_alineamiento_transcripcion = \
                2 * score_acumulado / (self.longitud_S + self.longitud_transcripcion_asociada)



        except ValueError or ZeroDivisionError:
            self.score_alineamiento = 0
        return

    def get_longitud_transcripcion_asociada(self):

        longitud = 0
        try:
            indice_primera = self.alineamiento_transcripcion_T.index(self.primer_elemento_asr_alineado)
            indice_ultima = self.alineamiento_transcripcion_T.index(self.ultimo_elemento_asr_alineado)
            for i in range(indice_primera, indice_ultima + 1):
                w = self.alineamiento_transcripcion_T[i]
                if w is not None:
                    longitud = longitud + len(w)
        except ValueError:
            pass
        return longitud

    def get_longitud_subtitulo_asociado(self):

        longitud = 0
        try:
            indice_primera = self.alineamiento_subtitulo_S.index(self.primer_elemento_subtitulo_alineado)
            indice_ultima = self.alineamiento_subtitulo_S.index(self.ultimo_elemento_subtitulo_alineado)
            for i in range(indice_primera, indice_ultima + 1):
                w = self.alineamiento_subtitulo_S[i]
                if w is not None:
                    longitud = longitud + len(w)
        except ValueError:
            pass
        return longitud

    def get_ultimos_elementos_alineados(self):

        alineamientos = zip(reversed(self.alineamiento_subtitulo_S),
                            reversed(self.alineamiento_transcripcion_T), )

        retorno_s = None
        retorno_t = None
        for subtitulo, transcripcion in alineamientos:
            if subtitulo is None or transcripcion is None:
                continue
            retorno_s = subtitulo
            retorno_t = transcripcion
            break
        return retorno_s, retorno_t

    def graba_fichero(self, fichero, alineamiento=True, matriz_F=False, matriz_S=False):
        if alineamiento:
            presentacion.graba_campos_fichero_excel(fichero,
                                                    None,
                                                    None,
                                                    'Alineamientos',
                                                    self.generador_filas_alineamiento())
        if matriz_F:
            presentacion.graba_campos_fichero_excel(fichero,
                                                    None,
                                                    None,
                                                    'Matriz_F',
                                                    presentacion.generador_rows_F_Mix(
                                                        self.secuencia_transcripcion_T,
                                                        self.secuencia_subtitulo_S,
                                                        self.coste_F,
                                                        self.traceback_T
                                                    ))
        if matriz_S:
            presentacion.graba_fichero_F(fichero,
                                        'Distancias',
                                         self.secuencia_transcripcion_T,
                                         self.secuencia_subtitulo_S,
                                         self.distancias_S)


    def generador_fila(self, lista):
        row = []
        for w in lista:
            s = "-"
            if w is not None:
                try:
                    s = w.palabra_str
                except AttributeError:
                    s = "{0:3.2f}".format(w)
            row.append(s)
        return row

    def generador_filas_alineamiento(self):
        try:
            yield ["Subtitulo"] + self.generador_fila(self.alineamiento_subtitulo_S)
            yield ["ASR"] + self.generador_fila(self.alineamiento_transcripcion_T)
            yield ["Score"] + self.generador_fila(self.score_pareja)
            yield ["Distancia"] + self.generador_fila(self.distancia_pareja)
            yield [" "]
        except:
            raise

    def imprime_matrices(self, alineamiento=True, matriz_F=False, matriz_S=False):

        if alineamiento:
            print(presentacion.show_alineamiento(["Subtitulo", "ASR", "Score", "Distancia"],
                                                 [self.alineamiento_subtitulo_S,
                                                  self.alineamiento_transcripcion_T,
                                                  self.score_pareja,
                                                  self.distancia_pareja]))

        if matriz_F:
            print(presentacion.show_F_Mix(self.secuencia_transcripcion_T,
                                          self.secuencia_subtitulo_S,
                                          self.coste_F,
                                          self.traceback_T))

        if matriz_S:
            print(presentacion.show_F(self.secuencia_transcripcion_T,
                                      self.secuencia_subtitulo_S,
                                      self.distancias_S,
                                      ))


class AlineamientoNW(Alineamiento):

    def __init__(self,
                 distancia,
                 entropia_subtitulo_S,
                 entropia_transcripcion_T=None,
                 coste_igualdad=0,
                 coste_desigualdad=1,
                 C_subtitulo_S=2,
                 C_transcripcion_T=2,
                 asimetria=True):
        super().__init__(distancia,
                         entropia_subtitulo_S,
                         entropia_transcripcion_T,
                         coste_igualdad,
                         coste_desigualdad,
                         C_subtitulo_S,
                         C_transcripcion_T)


        self.asimetria = asimetria


    def _impl_coste_alineamiento(self):

        if self.distancias_S is None:
            raise Exception("No se puede calcular costes de alineamiento sin matriz de distancias")

        self.coste_F = np.zeros_like(self.distancias_S)

        self.traceback_T = []
        filas_f, columnas_f = self.coste_F.shape

        for i in range(filas_f):
            fila = [''] * columnas_f
            self.traceback_T.append(fila)



        for columna in range(1, columnas_f):
            self.coste_F[0, columna] = self.coste_F[0, columna - 1] + self.C_subtitulo_S  # ct
            self.traceback_T[0][columna] = 'H'


        for fila in range(1, filas_f):
            self.coste_F[fila, 0] = self.coste_F[fila - 1, 0] + self.C_transcripcion_T  # traslacion vertical
            self.traceback_T[fila][0] = 'V'


        posibles_direcciones = ('D', 'V', 'H')
        for fila in range(1, filas_f):
            for columna in range(1, columnas_f):
                diagonal = self.coste_F[fila - 1, columna - 1] + self.distancias_S[fila, columna]
                vertical = self.coste_F[fila - 1, columna] + self.C_transcripcion_T
                horizontal = self.coste_F[fila, columna - 1] + self.C_subtitulo_S
                valores = (diagonal, vertical, horizontal)
                if self.minimizando:
                    minimo = min(valores)
                else:
                    minimo = max(valores)
                direccion = ''
                for v, d in zip(valores, posibles_direcciones):
                    if minimo == v:
                        direccion = direccion + d
                self.traceback_T[fila][columna] = direccion
                self.coste_F[fila, columna] = minimo


        indice_s = len(self.secuencia_subtitulo_S) - 1
        indice_t = len(self.secuencia_transcripcion_T) - 1
        fila = filas_f - 1
        columna = columnas_f - 1
        if self.asimetria:
            if self.minimizando:
                m = min(self.coste_F[fila])
            else:
                m = max(self.coste_F[fila])
            indice_m = [i for i, j in enumerate(self.coste_F[fila]) if j == m]
            columna = indice_m[-1] #
            indice_t = columna - 1




        self.coste = self.coste_F[fila, columna]


        self.alineamiento_transcripcion_T = []
        self.alineamiento_subtitulo_S = []


        while self.traceback_T[fila][columna] != 'F' \
                and self.traceback_T[fila][columna] != '':
            if 'D' in self.traceback_T[fila][columna]:
                self.alineamiento_subtitulo_S.append(self.secuencia_subtitulo_S[indice_s])
                self.alineamiento_transcripcion_T.append(self.secuencia_transcripcion_T[indice_t])
                indice_s -= 1
                indice_t -= 1
                fila -= 1
                columna -= 1
            elif 'H' in self.traceback_T[fila][columna]:
                self.alineamiento_subtitulo_S.append(None)
                self.alineamiento_transcripcion_T.append(self.secuencia_transcripcion_T[indice_t])
                indice_t -= 1
                columna -= 1
            else:
                self.alineamiento_subtitulo_S.append(self.secuencia_subtitulo_S[indice_s])
                self.alineamiento_transcripcion_T.append(None)
                indice_s -= 1
                fila -= 1


        self.alineamiento_subtitulo_S.reverse()
        self.alineamiento_transcripcion_T.reverse()



        return self.coste


class AlineamientoLV(AlineamientoNW):


    def __init__(self,
                 distancia,
                 entropia_subtitulo_S,
                 entropia_transcripcion_T=None,
                 coste_igualdad=0,
                 coste_desigualdad=1,
                 C_subtitulo_S=1,
                 C_transcripcion_T=1,
                 asimetria=False):
        super().__init__(distancia,
                         entropia_subtitulo_S,
                         entropia_transcripcion_T,
                         coste_igualdad=0,
                         coste_desigualdad=1,
                         C_subtitulo_S=1,
                         C_transcripcion_T=1)
        self.minimizando = True
        self.asimetria = False


#
# Busca secuencias locales
#
class AlineamientoSW(Alineamiento):

    def __init__(self,
                 distancia,
                 entropia_subtitulo_S,
                 entropia_transcripcion_T=None,
                 coste_igualdad=0,
                 coste_desigualdad=1,
                 C_subtitulo_S=2,
                 C_transcripcion_T=2,
                 asimetria=False):
        super().__init__(distancia,
                         entropia_subtitulo_S,
                         entropia_transcripcion_T,
                         coste_igualdad,
                         coste_desigualdad,
                         C_subtitulo_S,
                         C_transcripcion_T)


        self.asimetria = asimetria


    def _impl_coste_alineamiento(self):



        if self.distancias_S is None:
            raise Exception("No se puede calcular costes de alineamiento sin matriz de distancias")

        self.coste_F = np.zeros_like(self.distancias_S)

        filas, columnas = self.coste_F.shape
        self.traceback_T = []
        for i in range(filas):
            fila = [''] * columnas
            self.traceback_T.append(fila)


        filas, columnas = self.coste_F.shape
        filas -= 1
        columnas -= 1

        minimo_global = 0
        min_fila = 0
        min_columna = 0

        posibles_direcciones = ('D', 'V', 'H')
        for fila in range(1, filas + 1):
            for columna in range(1, columnas + 1):
                diagonal = self.coste_F[fila - 1, columna - 1] + self.distancias_S[fila, columna]
                vertical = self.coste_F[fila - 1, columna] + self.C_transcripcion_T
                horizontal = self.coste_F[fila, columna - 1] + self.C_subtitulo_S
                valores = (diagonal, vertical, horizontal)
                if self.minimizando:
                    minimo = min(valores + (0,))
                else:
                    minimo = max(valores + (0,))
                direccion = ''
                for v, d in zip(valores, posibles_direcciones):
                    if minimo == v:
                        direccion = direccion + d
                if direccion == '':
                    direccion = 'F'


                self.traceback_T[fila][columna] = direccion
                self.coste_F[fila, columna] = minimo
                if self.minimizando:
                    if minimo <= minimo_global:
                        min_fila = fila
                        min_columna = columna
                        minimo_global = minimo
                else:
                    if minimo >= minimo_global:
                        min_fila = fila
                        min_columna = columna
                        minimo_global = minimo

        self.coste = self.coste_F[min_fila, min_columna]

        self.alineamiento_transcripcion_T = []
        self.alineamiento_subtitulo_S = []



        fila = min_fila
        columna = min_columna


        indice_s = fila - 1
        indice_t = columna - 1

        while not self.traceback_T[fila][columna] == '' and not self.traceback_T[fila][columna] == 'F':
            if 'D' in self.traceback_T[fila][columna]:  # diagonal se cogen los dos
                self.alineamiento_subtitulo_S.append(self.secuencia_subtitulo_S[indice_s])
                self.alineamiento_transcripcion_T.append(self.secuencia_transcripcion_T[indice_t])
                indice_s -= 1
                indice_t -= 1
                fila -= 1
                columna -= 1
            elif 'H' in self.traceback_T[fila][columna]:
                self.alineamiento_subtitulo_S.append(None)
                self.alineamiento_transcripcion_T.append(self.secuencia_transcripcion_T[indice_t])
                indice_t -= 1
                columna -= 1
            elif 'V' in self.traceback_T[fila][columna]:
                self.alineamiento_subtitulo_S.append(self.secuencia_subtitulo_S[indice_s])
                self.alineamiento_transcripcion_T.append(None)
                indice_s -= 1
                fila -= 1


        self.alineamiento_subtitulo_S.reverse()
        self.alineamiento_transcripcion_T.reverse()

        return self.coste


class AlineamientoLiterales(Alineamiento):

    def __init__(self,
                 distancia,
                 entropia_subtitulo_S,
                 entropia_transcripcion_T=None,
                 coste_igualdad=0,
                 coste_desigualdad=1,
                 C_subtitulo_S=2,
                 C_transcripcion_T=2,
                 asimetria=False):


        super().__init__(distancia,
                         entropia_subtitulo_S,
                         entropia_transcripcion_T,
                         coste_igualdad=0,
                         coste_desigualdad=1,
                         C_subtitulo_S=2,
                         C_transcripcion_T=2)


        self.asimetria = asimetria
        self.numero_maximo_elementos_iguales = 0
        self.numero_total_elementos_iguales = 0
        self.indices_secuencia = []

    def get_numero_secuencia_mas_larga(self):
        """
        Devuelve el numero de elementos de la secuncia las larga
        """
        try:
            self.numero_maximo_elementos_iguales = self.indices_secuencia[0][2]
        except IndexError:
            self.numero_maximo_elementos_iguales = 0
        return self.numero_maximo_elementos_iguales

    def get_numero_de_secuencias(self):
        """
        Devuelve el numero de elementos alineados de la secuencia mas larga
        """
        return len(self.indices_secuencia)

    def get_numero_total_coincidentes(self):
        """
        Devuelve el total de elementos alineados
        """
        self.numero_total_elementos_iguales = 0
        for secuencia in self.indices_secuencia:
            self.numero_total_elementos_iguales += secuencia[2]
        return self.numero_total_elementos_iguales

    def _impl_coste_alineamiento(self):



        if self.distancias_S is None:
            raise Exception("No se puede calcular costes de alineamiento sin matriz de distancias")

        self.coste_F = np.zeros_like(self.distancias_S)
        self.traceback_T = np.zeros_like(self.distancias_S, dtype=str)


        filas, columnas = self.coste_F.shape


        for fila in range(1, filas):
            for columna in range(1, columnas):
                if not self.distancias_S[fila, columna] == 0:  # Son distintos
                    self.coste_F[fila, columna] = 0
                else:
                    #
                    # En la matriz de costes se cumulan los caracteres alineados
                    #
                    self.coste_F[fila, columna] = self.coste_F[fila - 1, columna - 1] + 1
                    self.traceback_T[fila, columna] = 'D'



        self.coste = 0

        self.indices_secuencia, patron_S, patron_T = \
            self.agrupacion_alineamientos(np.copy(self.coste_F[1:, 1:]))

        self.alineamiento_transcripcion_T = []
        self.alineamiento_subtitulo_S = []


        indice_s = 0
        indice_t = 0
        filas = len(patron_S)
        columnas = len(patron_T)
        while indice_s < filas and indice_t < columnas:
            if patron_S[indice_s] == "F" and patron_T[indice_t] == "F":
                break
            if patron_S[indice_s] == "C" and patron_T[indice_t] == "C":

                self.alineamiento_subtitulo_S. \
                    append(self.secuencia_subtitulo_S[indice_s])
                self.alineamiento_transcripcion_T. \
                    append(self.secuencia_transcripcion_T[indice_t])
                indice_s += 1
                indice_t += 1

            else:
                if patron_S[indice_s] == "I":
                    self.alineamiento_subtitulo_S. \
                        append(self.secuencia_subtitulo_S[indice_s])
                    self.alineamiento_transcripcion_T. \
                        append(None)
                    indice_s += 1

                if patron_T[indice_t] == "I":
                    self.alineamiento_subtitulo_S. \
                        append(None)
                    self.alineamiento_transcripcion_T. \
                        append(self.secuencia_transcripcion_T[indice_t])
                    indice_t += 1

        try:
            self.coste = self.indices_secuencia[0][2]
            self.numero_maximo_elementos_iguales = self.indices_secuencia[0][2]
        except IndexError:
            pass

        return self.coste

    def agrupacion_alineamientos(self, matriz):

        posiciones_agrupamientos = []
        total_coincidentes = 0
        while True:
            i_max = np.argmax(matriz)
            fila, columna = np.unravel_index(i_max, matriz.shape)
            valor = matriz[fila, columna]

            if valor == 0:
                break


            f, c = fila, columna
            while True:
                if f < 0 or c < 0 or matriz[f, c] <= 0:

                    f = f + 1
                    c = c + 1
                    break
                f = f - 1
                c = c - 1
            numero_iguales_consecutivos = fila - f + 1
            total_coincidentes += numero_iguales_consecutivos

            if self.agrupamiento_valido([f, c, numero_iguales_consecutivos], posiciones_agrupamientos):
                posiciones_agrupamientos.append([f, c, numero_iguales_consecutivos])

                matriz[f:f + numero_iguales_consecutivos, :] = 0
                matriz[:, c:c + numero_iguales_consecutivos] = 0
            else:

                matriz[f:f + numero_iguales_consecutivos, c:c + numero_iguales_consecutivos] = 0

        patron_S = ["I" for i in range(len(self.secuencia_subtitulo_S))]
        patron_T = ["I" for i in range(len(self.secuencia_transcripcion_T))]
        grupo = 0
        for coincidentes in posiciones_agrupamientos:
            for indice in range(coincidentes[2]):
                patron_S[coincidentes[0] + indice] = "C"
                patron_T[coincidentes[1] + indice] = "C"
            grupo += 1

        patron_S.append("F")
        patron_T.append("F")
        return posiciones_agrupamientos, patron_S, patron_T

    def agrupamiento_valido(self, agrupamiento, agrupamientos):
        valido = True
        for agrupamiento_valido in agrupamientos:
            if (agrupamiento[0] < agrupamiento_valido[0] and agrupamiento[1] < agrupamiento_valido[1]) or \
                    (agrupamiento[0] > agrupamiento_valido[0] and agrupamiento[1] > agrupamiento_valido[1]):
                continue
            else:
                valido = False
                break
        return valido


class AlineamientoMultiple(Alineamiento):


    def __init__(self,
                 distancia,
                 entropia_subtitulo_S,
                 entropia_transcripcion_T=None,
                 coste_igualdad=0,
                 coste_desigualdad=1,
                 C_subtitulo_S=2,
                 C_transcripcion_T=2,
                 asimetria=False):
        super().__init__(distancia,
                         entropia_subtitulo_S,
                         entropia_transcripcion_T,
                         coste_igualdad,
                         coste_desigualdad,
                         C_subtitulo_S,
                         C_transcripcion_T)



        self.asimetria = asimetria
        self.alineamientos = [
            AlineamientoNW(self.distancia,
                           self.entropia_subtitulo_S,
                           self.entropia_transcripcion_T,
                           self.coste_igualdad,
                           self.coste_desigualdad,
                           self.C_subtitulo_S,
                           self.C_transcripcion_T,
                           False), #asimetria
            AlineamientoNW(self.distancia,
                           self.entropia_subtitulo_S,
                           self.entropia_transcripcion_T,
                           self.coste_igualdad,
                           self.coste_desigualdad,
                           self.C_subtitulo_S,
                           self.C_transcripcion_T,
                           True), #asimetricca
            AlineamientoSW(self.distancia,
                           self.entropia_subtitulo_S,
                           self.entropia_transcripcion_T,
                           self.coste_igualdad,
                           self.coste_desigualdad,
                           self.C_subtitulo_S,
                           self.C_transcripcion_T,
                           False), #alineamiento

        ]


    def _impl_coste_alineamiento(self):

        self.algoritmo_usado = None
        maximo = 0

        for alineamiento in self.alineamientos:
            alineamiento.calcula_similitud(self.secuencia_subtitulo_S,
                                           self.secuencia_transcripcion_T,
                                           )
            if alineamiento.score_alineamiento >= maximo:
                maximo = alineamiento.score_alineamiento
                self.alineamiento_subtitulo_S = alineamiento.alineamiento_subtitulo_S
                self.alineamiento_transcripcion_T = alineamiento.alineamiento_transcripcion_T
                self.coste_F = alineamiento.coste_F
                self.traceback_T = alineamiento.traceback_T
                self.coste = alineamiento.coste
                self.algoritmo_usado = "{0}{1}".format(alineamiento.acronimo_algoritmo,
                                                        'A' if alineamiento.asimetria else '')
                if maximo == 1:
                    break



        return self.coste


ALGORITMOS = {'SW': AlineamientoSW.__name__,
              'NW': AlineamientoNW.__name__,
              'LV': AlineamientoLV.__name__,
              'LT': AlineamientoLiterales.__name__,
              'MT': AlineamientoMultiple.__name__
              }