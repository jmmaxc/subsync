
import proceso_frases


class Similitud():


    def __init__(self, alineamiento, subtitulo, linea_asr):

        self.alineamiento = alineamiento

        self.score_palabra_inicial_alineada = 0
        self.sub_palabra_inicial_alineada = None
        self.asr_palabra_inicial_alineada = None

        self.score_palabra_final_alineada = 0
        self.sub_palabra_final_alineada = None
        self.asr_palabra_final_alineada = None

        self.asr_palabra_inicial = None
        self.asr_palabra_final = None

        self.maximo_score = 0
        self.sub_palabra_max_score = None
        self.asr_palabra_max_score = None

        self.sub_densidad_alineamiento = 0
        self.sub_porcentaje_descartado = 0
        self.sub_porcentaje_utilizado = 0
        self.sub_porcentaje_no_usado = 0

        self.asr_densidad_alineamiento = 0
        self.asr_porcentaje_descartado = 0
        self.asr_porcentaje_utilizado = 0
        self.asr_porcentaje_no_usado = 0

        self.gap_temporal_descartado = 0
        self.gap_temporal_utilizado = 0
        self.gap_temporal_no_usado = 0
        self.gap_temporal_subtitulo = 0
        self.ajuste_temporal = 0

        self.t_inicial = 0
        self.t_final = 0


        parejas = zip(self.alineamiento.alineamiento_subtitulo_S,
                      self.alineamiento.alineamiento_transcripcion_T,
                      self.alineamiento.score_pareja)
        parejas_r = zip(reversed(self.alineamiento.alineamiento_subtitulo_S),
                        reversed(self.alineamiento.alineamiento_transcripcion_T),
                        reversed(self.alineamiento.score_pareja))
        try:
            self.sub_palabra_inicial_alineada, \
            self.asr_palabra_inicial_alineada, \
            self.score_palabra_inicial_alineada = \
                [(sub, trans, score_pareja) for sub, trans, score_pareja in parejas if score_pareja > 0][0]

            self.sub_palabra_final_alineada, \
            self.asr_palabra_final_alineada, \
            self.score_palabra_final_alineada = \
                [(sub, trans, score_pareja) for sub, trans, score_pareja in parejas_r if score_pareja > 0][0]
        except IndexError:
            proceso_frases.imprimir("Todos los scores son 0")


        if len(self.alineamiento.score_pareja) > 0:  # Si no hay parejas no tiene sentido
            self.maximo_score = max(self.alineamiento.score_pareja)
            ind = self.alineamiento.score_pareja.index(self.maximo_score)
            self.sub_palabra_max_score = self.alineamiento.alineamiento_subtitulo_S[ind]
            self.asr_palabra_max_score = self.alineamiento.alineamiento_transcripcion_T[ind]

            self.sub_densidad_alineamiento, \
            self.sub_porcentaje_descartado, \
            self.sub_porcentaje_utilizado, \
            self.sub_porcentaje_no_usado = self.__calcula_densidad(self.sub_palabra_inicial_alineada,
                                                                   self.sub_palabra_final_alineada,
                                                                   self.alineamiento.secuencia_subtitulo_S,
                                                                   self.alineamiento.alineamiento_subtitulo_S)

            self.asr_densidad_alineamiento, \
            self.asr_porcentaje_descartado, \
            self.asr_porcentaje_utilizado, \
            self.asr_porcentaje_no_usado = self.__calcula_densidad(self.asr_palabra_inicial_alineada,
                                                                   self.asr_palabra_final_alineada,
                                                                   self.alineamiento.secuencia_transcripcion_T,
                                                                   self.alineamiento.alineamiento_transcripcion_T)



            self.asr_palabra_inicial, self.asr_palabra_final, self.t_inicial, self.t_final = \
                self.__tiempos_extremos(subtitulo,
                                        linea_asr,
                                        self.sub_palabra_inicial_alineada,
                                        self.sub_palabra_final_alineada,
                                        self.asr_palabra_inicial_alineada,
                                        self.asr_palabra_final_alineada)




            if self.asr_palabra_inicial.instante > self.asr_palabra_final.instante or \
                    self.t_inicial > self.t_final:
                proceso_frases.imprimir("Error en los tiempos")



            self.gap_temporal_descartado = self.asr_palabra_inicial.instante - linea_asr.lista_palabras[0].instante
            self.gap_temporal_utilizado = self.asr_palabra_final.instante - self.asr_palabra_inicial.instante
            self.gap_temporal_no_usado = linea_asr.lista_palabras[-1].instante - self.asr_palabra_final.instante
            self.gap_temporal_subtitulo = self.asr_palabra_final_alineada.instante - self.asr_palabra_inicial_alineada.instante
            try:
                self.ajuste_temporal = self.gap_temporal_utilizado / self.gap_temporal_subtitulo
            except ZeroDivisionError:
                self.ajuste_temporal = 0


    def get_instante_inicial(self):
        return self.t_inicial


    def get_instante_final(self):
        return self.t_final

    def __tiempos_extremos(self,
                           subtitulo,
                           linea_asr,
                           palabra_inicial_sub,
                           palabra_final_sub,
                           palabra_inicial_asr,
                           palabra_final_asr):


        try:
            ind_palabra_inicial_sub = subtitulo.lista_palabras.index(palabra_inicial_sub)
            offset_tiempo_inicio = 385 * ind_palabra_inicial_sub
        except ValueError:
            offset_tiempo_inicio = 0

        t_inicial = palabra_inicial_asr.instante - offset_tiempo_inicio

        primera_palabra = None
        for w in linea_asr.lista_palabras:
            if w.instante >= t_inicial:
                primera_palabra = w
                break


        ind_palabra_final_sub = subtitulo.lista_palabras.index(palabra_final_sub)
        t_final = t_inicial + subtitulo.t_fin_ajustado - subtitulo.t_inicio_ajustado
        t_final_subtitulo_1 = palabra_final_asr.instante + (
                len(subtitulo.lista_palabras) - ind_palabra_final_sub) * 385

        t_final = max(t_final, t_final_subtitulo_1)

        ultima_palabra = None
        for w in linea_asr.lista_palabras[::-1]:
            if w.instante <= t_final:
                ultima_palabra = w
                break

        return primera_palabra, ultima_palabra, t_inicial, t_final

    def __calcula_densidad(self,
                           palabra_inicial,
                           palabra_final,
                           secuencia,
                           secuencia_alineada):

        try:
            ind_sec_inicio = secuencia.index(palabra_inicial)
            ind_sec_final = secuencia.index(palabra_final)
            palabras_usadas_secuencia = ind_sec_final - ind_sec_inicio + 1
        except ValueError:
            print("Error la palabra no existe")
            return



        ind_alineada_inicio = secuencia_alineada.index(palabra_inicial)
        ind_alineada_final = secuencia_alineada.index(palabra_final)
        palabras_alineamiento = ind_alineada_final - ind_alineada_inicio + 1

        densidad_alineamiento = palabras_usadas_secuencia / palabras_alineamiento
        porcentaje_descartado = ind_sec_inicio / len(secuencia)
        porcentaje_usado = palabras_usadas_secuencia / len(secuencia)
        porcentaje_no_usado = 1 - porcentaje_descartado - porcentaje_usado

        return densidad_alineamiento, porcentaje_descartado, porcentaje_usado, porcentaje_no_usado

    def zonas_densidad_alinemiento(self):

        parejas = zip(self.alineamiento.alineamiento_subtitulo_S,
                      self.alineamiento.alineamiento_transcripcion_T,
                      )

        densidad = []
        indice_secuencia = 0
        contador = 0
        esta_en_secuencia = False
        for i, (s, t) in enumerate(parejas):
            if s is not None and t is not None:
                if not esta_en_secuencia:
                    esta_en_secuencia = True
                    contador = 0
                    indice_secuencia = i
                contador += 1
            else:
                if esta_en_secuencia:
                    densidad.append([indice_secuencia, contador])
                    esta_en_secuencia = False

        if esta_en_secuencia:
            densidad.append([indice_secuencia, contador])
            esta_en_secuencia = False
        densidad.sort(key=lambda tup: tup[1], reverse=True)
        return densidad


