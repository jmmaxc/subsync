# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 18:59:00 2020

@author: max
"""
import io

import proceso_frases

import time
import datetime
import srt
import re
import interpolacion



class Subtitulo(proceso_frases.Frase):
    """
      Es la clase que soporta a un subtitulo
      t_ini: tiempo de inicio del subtitulo
      t_fin: tiempo de finalizacion
      linea: es un string que contiene una linea,
      si es multilinea es porque contiene varios retornos de carro
    """


    ESTADOS = {'PENDIENTE': 'PENDIENTE',
               'SINCRONIZADO': 'ALINEADO',
               'SINCRONIZADO2': 'SINCRONIZADO2',
               'INTERPOLADO': 'INTERPOLADO',
               'INERCIADO': 'INERCIADO',
               'DESCARTADO': 'DESCARTADO'}
    ESTADO_EMISION = {'PENDIENTE': 1, 'EMITIDO': 2}

    EST_SINC_TFIN = {'PENDIENTE': 1,  # Esta en el estado inicial
                     'OFFSET': 2,  # Segun los datos iniciales actualizado segun el tini
                     'SINCRONIZADO': 3,  # Se ha sincronizado con el end del asr
                     'INTERPOLADO': 4,  # Se ha usado una interpolacion en funcion del tini y el largo
                     'DESCARTADO': 5}  # No ha habido forma de encajarlo y se descarta el subtitulo

    def __init__(self, subtitulo_guion, guion=None):

        self.guion = guion
        self.subtitulo_guion = subtitulo_guion
        self.estado_emision = Subtitulo.ESTADO_EMISION['PENDIENTE']
        self.estado = Subtitulo.ESTADOS['PENDIENTE']
        self.sinc_tiempo_fin = Subtitulo.EST_SINC_TFIN['PENDIENTE']
        self.cronificado = False
        self.tiene_ASR_asociado = False
        self.frase_ASR_asociada = None
        self.frase_ASR_descartada = None
        self.frase_ASR_no_usada = None
        self.linea_ASR = None
        self.score_alineamiento = 0
        self.algoritmo_usado = None


        self.alineamiento_subtitulo = None
        self.alineamiento_ASR = None
        self.score_pareja = None

        self.instante_sincronizacion = 0
        self.t_ini = subtitulo_guion.start.total_seconds() * 1000  # ms
        self.t_fin = subtitulo_guion.end.total_seconds() * 1000
        self.t_inicio_ajustado = self.t_ini
        self.t_fin_ajustado = self.t_fin
        self.delay = self.t_ini - self.t_inicio_ajustado


        self.duracion_original = self.t_fin - self.t_ini
        self.duracion = self.duracion_original

        self.star = 0
        self.end = 0


        self.gap_derecho = 0
        self.gap_izquierdo = 0
        self.gap_derecho_ini = 0
        self.gap_izquierdo_ini = 0

        super().__init__(subtitulo_guion.content,
                         self.t_ini,
                         1.0,
                         True,
                         True)

    def duracion_standard(self, ):
        return 1000 * len(self.frase_str) / 15


    def update_time(self):

        try:
            # delay = self.t_inicio_ajustado - self.lista_palabras[0].instante
            # for palabra in self.lista_palabras:
            #     palabra.instante = palabra.instante + delay
            for palabra in self.lista_palabras:
                palabra.instante = self.t_inicio_ajustado
        except IndexError:
            pass

    def sincroniza(self, star, end, linea_asr=None, instante=None, limite_end=None):
        indice = self.subtitulo_guion.index
        self.guion.sincroniza_subtitulo(self, star, end, linea_asr, instante, limite_end)

    def get_subtitulos_anteriores(self):
        for s in self.guion.get_subtitulos_anteriores(self):
            yield s

    def get_numero_subtitulos_anteriores(self):
        return self.guion.get_numero_subtitulos_anteriores(self)

    def interpola(self, instante=None):
        self.guion.subtitulo_inerciado(self, instante)

    def get_campos_linea(self, tipo, linea):

        instante_inicial = 0
        instante_final = 0
        frase_str = " "
        confianza = 0
        if linea is not None and not linea.esta_vacia:
            try:
                confianza = linea.lista_palabras[-1].confianza
                instante_inicial = linea.lista_palabras[0].instante
                instante_final = linea.lista_palabras[-1].instante
                frase_str = ' '.join([w.palabra_str for w in linea.lista_palabras])
            except:
                #
                # Si viene por aqui hay un bug porque linea esta vacia esta indicando algo mal
                #
                pass

        retorno = [tipo,
                   self.subtitulo_guion.index,
                   self.estado,
                   confianza,
                   instante_inicial,
                   instante_final,
                   0,
                   frase_str,
                   0,
                   0,
                   0,
                   0,
                   self.instante_sincronizacion,
                   self.algoritmo_usado]
        return retorno


class Guion:

    GAP_MINIMO_SUBTITULOS = 100  # En ms
    DURACION_MINIMA_SUBTITULO = 500  # En ms
    SEGMENTACION_DELAY = [3, 8, 12]
    SEGMENTACION = True

    def __init__(self, nombre_fichero_guion_entrada, fichero_salida_guion_online=None):

        if nombre_fichero_guion_entrada == "":
            raise Exception("FaltaFichero")

        self._nombre_fichero_guion_entrada = nombre_fichero_guion_entrada
        self.fichero_salida_guion_online = fichero_salida_guion_online
        self.fd_salida_online = None
        self.subtitulos = []


        self.delay_segmento = [0] * len(Guion.SEGMENTACION_DELAY)
        self.n_delay_segmento = [0] * len(Guion.SEGMENTACION_DELAY)
        self.pendiente = [0] * len(Guion.SEGMENTACION_DELAY)
        self.delay_media_movil = [0] * len(Guion.SEGMENTACION_DELAY)


        self.ajuste_delay = [interpolacion.Interpolacion()] * len(Guion.SEGMENTACION_DELAY)
        self.ajuste_longitud = [interpolacion.Interpolacion()] * len(Guion.SEGMENTACION_DELAY)

        self.delay = 0
        self.delay_media_movil_sin_segmentar = 0
        self.delay_acumulado = 0
        self.delay2_acumulado = 0
        self.numero_delays = 0
        self.offset_proceso = 0  #
        self.fin_sincronizacion = False
        self.instante_ultimo_subtitulo = 0

        formato_srt = True
        try:
            s = self._nombre_fichero_guion_entrada.rindex('.srt')
        except:
            formato_srt = False


        with open(self._nombre_fichero_guion_entrada, mode='r', encoding='UTF-8') as fd:  # U

            if formato_srt:
                subtitulos_srt = srt.sort_and_reindex(
                    [subtitulo_srt for subtitulo_srt in srt.parse(fd)
                     if len(proceso_frases.deja_linea_plana(subtitulo_srt.content)) > 0],
                    start_index=1)
            else:
                subtitulos_srt = srt.sort_and_reindex([subtitulo_srt
                                                       for subtitulo_srt in parse_txt(fd, milisegundos=True)],
                                                      start_index=1)

            gap_medio = 0
            duracion_media = 0
            t_fin_anterior = 0
            subtitulo_anterior = None
            for subtitulo_srt in subtitulos_srt:
                try:
                    subtitulo = Subtitulo(subtitulo_srt, self)
                    self.subtitulos.append(subtitulo)
                    duracion_media += subtitulo.t_fin - subtitulo.t_ini
                    gap_medio += subtitulo.t_ini - t_fin_anterior
                    if subtitulo_anterior is not None:
                        subtitulo.gap_izquierdo_ini = subtitulo.t_ini - subtitulo_anterior.t_fin
                        subtitulo_anterior.gap_derecho_ini = subtitulo.gap_izquierdo_ini
                        subtitulo.gap_izquierdo = subtitulo.gap_izquierdo_ini
                        subtitulo_anterior.gap_derecho = subtitulo.gap_izquierdo_ini
                        subtitulo.gap_derecho_ini = 0
                        subtitulo.gap_derecho = 0
                    else:
                        subtitulo.gap_izquierdo_ini = 0
                        subtitulo.gap_izquierdo = 0

                    subtitulo_anterior = subtitulo
                    t_fin_anterior = subtitulo.t_fin
                except ValueError:
                    proceso_frases.imprimir("Error al procesar el subtitulo: {0}".format(subtitulo_srt.index))
                    continue

        try:
            self.duracion_media = duracion_media / len(self.subtitulos)
            self.gap_medio = gap_medio / len(self.subtitulos)
        except ZeroDivisionError:
            self.duracion_media = 1
            self.gap_medio = 1

        try:
            self.subtitulo_activo = self.subtitulos[0]
            self.ultimo_subtitulo_sincronizado  = None
        except IndexError:
            self.subtitulo_activo = None
            self.ultimo_subtitulo_sincronizado = None
            self.fin_sincronizacion = True

        try:
            self.instante_ultimo_subtitulo = self.subtitulos[-1].t_ini
        except IndexError:
            self.instante_ultimo_subtitulo = 0

    def get_instante_ultimo_subtitulo(self):

        return self.instante_ultimo_subtitulo

    def get_parametros(self):
        lista = [
            ["Numero delays", self.numero_delays],
            ["Delay medio", 0 if self.numero_delays == 0 else self.delay_acumulado / self.numero_delays],
            ["numero segmentos", len(self.SEGMENTACION_DELAY)],

        ]
        n_delays_segmento = [["N_delays_Segmento{0}".format(a), b] for a, b in zip(self.SEGMENTACION_DELAY,
                                                                                   self.n_delay_segmento)]
        medias = [0 if n == 0 else d / n for d, n in zip(self.delay_segmento, self.n_delay_segmento)]
        medias_segmento = [["Media_Segmento{0}".format(a), b] for a, b in zip(self.SEGMENTACION_DELAY,
                                                                              medias)]
        return lista + n_delays_segmento + medias_segmento



    def set_offset_proceso(self, offset_proceso):
        self.offset_proceso = offset_proceso

    def elimina_subtitulo(self, subtitulo):
        self.subtitulos.remove(subtitulo)

    def get_subtitulos(self):
        return self.subtitulos

    def total_pendientes_sincronizar(self):

        if self.fin_sincronizacion:
            return 0

        try:
            indice_subtitulo_activo = self.subtitulos.index(self.subtitulo_activo)
        except ValueError:
            indice_subtitulo_activo = 0

        return len(self.subtitulos) - indice_subtitulo_activo

    def sincroniza_subtitulo(self,
                             subtitulo,
                             star,
                             end,
                             linea_asr=None,
                             instante=None,
                             limite_end=None):

        if self.fin_sincronizacion or self.subtitulo_activo is None:
            raise ValueError("Todos los subtitulos estan sincronizados")

        if subtitulo.cronificado:
            raise ValueError("El subtitulo ya esta cronificado")

        if subtitulo not in self.subtitulos:
            raise ValueError("El subtitulo no forma parte del guion")

        if star > end:
            raise ValueError("El instante inicial no puede ser posterior al instante final")

        if limite_end is not None:
            #
            # Hay que comprobar que el subtitulo activo
            #
            if star > limite_end or end > limite_end:
                raise ValueError("No se puede superar el valor de sincronizacion principal: ", limite_end)


        delay_star = 0

        if self.ultimo_subtitulo_sincronizado is not None:
            if self.ultimo_subtitulo_sincronizado.t_fin_ajustado > star:
                self.ultimo_subtitulo_sincronizado.t_fin_ajustado = star - self.GAP_MINIMO_SUBTITULOS
                if self.ultimo_subtitulo_sincronizado.t_inicio_ajustado > self.ultimo_subtitulo_sincronizado.t_fin_ajustado:
                    print("Mayor")



        primer_subtitulo = self.subtitulo_activo
        delay_star = 0
        star_ajustado = star + delay_star
        subtitulo.delay = star_ajustado - subtitulo.t_ini

        if subtitulo is not self.subtitulo_activo:
            delay_star = self.sincroniza_subtitulos_anteriores_interpolando(self.subtitulo_activo,
                                                                            subtitulo,
                                                                            star_ajustado,
                                                                            end,
                                                                            instante)

            self.subtitulo_activo = subtitulo

        star_ajustado = star_ajustado + delay_star

        self.subtitulo_activo.t_inicio_ajustado = star_ajustado
        self.subtitulo_activo.t_fin_ajustado = self.subtitulo_activo.t_inicio_ajustado + \
                                               self.calcula_duracion(self.subtitulo_activo)
        self.subtitulo_activo.delay = \
            self.subtitulo_activo.t_inicio_ajustado - self.subtitulo_activo.t_ini

        if limite_end is None:

            delay = self.subtitulo_activo.delay
            self.delay_acumulado = self.delay_acumulado + delay
            self.delay2_acumulado = self.delay2_acumulado + delay * delay


            self.delay_media_movil_sin_segmentar = 0.5*(self.delay_media_movil_sin_segmentar + delay)

            self.numero_delays += 1


            for n, segmento in enumerate(Guion.SEGMENTACION_DELAY):
                if len(self.subtitulo_activo.lista_palabras) <= segmento:
                    k = n
                    break
            else:
                k = -1

            if not Guion.SEGMENTACION:
                k = 0

            if linea_asr is not None:
                longitud_asr = len(linea_asr.lista_palabras)
                tiempo_asr = linea_asr.lista_palabras[-1].instante - linea_asr.lista_palabras[0].instante
                longitud_subtitulo = len(self.subtitulo_activo.lista_palabras)

                if self.subtitulo_activo.score_alineamiento > 0:


                    try:
                        self.pendiente[k] += delay / longitud_subtitulo
                    except ZeroDivisionError:
                        pass

                    # ajuste por delay medio
                    self.delay_segmento[k] += delay
                    self.n_delay_segmento[k] += 1

                    # ajuste por recta regresion
                    self.ajuste_delay[k].incorpora(longitud_subtitulo, delay)
                    self.ajuste_longitud[k].incorpora(longitud_asr, longitud_asr)

                    # ajuste por media movil
                    self.delay_media_movil[k] = 0.5 * (self.delay_media_movil[k] + delay)


            self.subtitulo_activo.estado = Subtitulo.ESTADOS['SINCRONIZADO']
        else:

            self.subtitulo_activo.estado = Subtitulo.ESTADOS['SINCRONIZADO2']

            if self.subtitulo_activo.t_fin_ajustado > limite_end:

                self.subtitulo_activo.t_fin_ajustado = star_ajustado + Guion.DURACION_MINIMA_SUBTITULO
                if self.subtitulo_activo.t_fin_ajustado > limite_end:
                    self.subtitulo_activo.t_fin_ajustado = limite_end - Guion.GAP_MINIMO_SUBTITULOS
            self.subtitulo_activo.duracion = \
                self.subtitulo_activo.t_fin_ajustado - self.subtitulo_activo.t_inicio_ajustado

        self.subtitulo_activo.cronificado = True
        self.subtitulo_activo.update_time()
        self.subtitulo_activo.instante_sincronizacion = instante
        self.subtitulo_activo.star = star
        self.subtitulo_activo.end = end

        if linea_asr is not None:
            self.subtitulo_activo.frase_ASR_asociada = linea_asr
            self.subtitulo_activo.tiene_ASR_asociado = True


        if self.ultimo_subtitulo_sincronizado is None:
            self.subtitulo_activo.gap_izquierdo = 0
        else:
            self.subtitulo_activo.gap_izquierdo = self.subtitulo_activo.t_inicio_ajustado - \
                                                  self.ultimo_subtitulo_sincronizado.t_fin_ajustado
            self.ultimo_subtitulo_sincronizado.gap_derecho = self.subtitulo_activo.gap_izquierdo

        try:
            ind_siguiente = self.subtitulos.index(self.subtitulo_activo) + 1
            self.subtitulo_activo = self.subtitulos[ind_siguiente]
            self.ultimo_subtitulo_sincronizado = subtitulo
        except IndexError:
            self.subtitulo_activo.gap_derecho = 0
            self.subtitulo_activo = None
            self.fin_sincronizacion = True

        if subtitulo.t_inicio_ajustado > 5000000 or subtitulo.t_fin_ajustado > 5000000:
            print("error")

        if self.fd_salida_online is not None:
            indice_ultimo = self.subtitulos.index(subtitulo)
            indice_primero = self.subtitulos.index(primer_subtitulo)
            self.graba_subtitulo_ajustado_online([s for s in self.subtitulos[indice_primero:indice_ultimo + 1]])

    def calcula_delay_inerciado(self, subtitulo):

        algoritmo = 'MEDIA_MOVIL'

        for n, segmento in enumerate(Guion.SEGMENTACION_DELAY):

            if len(subtitulo.lista_palabras) <= segmento:
                k = n
                break
        else:
            k = -1  # El ultimo


        if not Guion.SEGMENTACION:
            k = 0

        n_delays = self.n_delay_segmento[k]
        if n_delays == 0:
            delay = -385 * len(subtitulo.lista_palabras)
        elif n_delays < 3:
            delay=self.delay_media_movil_sin_segmentar

        else:
            if algoritmo is 'PENDIENTE':
                delay = len(self.subtitulo_activo.lista_palabras) * self.pendiente[k] / n_delays
            elif algoritmo is 'AJUSTE':
                m, n, r, media = self.ajuste_delay[k].get_ajuste(forzar_cero=True)
                delay = n + m * len(self.subtitulo_activo.lista_palabras)  # Ajuste
            elif algoritmo is 'MEDIA':
                delay = self.delay_segmento[k] / n_delays  # por segmento medio
            else:
                delay = self.delay_media_movil[k]

        return delay

    def get_media_movil(self,subtitulo):
        for n, segmento in enumerate(Guion.SEGMENTACION_DELAY):
            if len(subtitulo.lista_palabras) <= segmento:
                k = n
                break
        else:
            k = -1  # El ultimo

        if not Guion.SEGMENTACION:
            k = 0

        n_delays = self.n_delay_segmento[k]
        if n_delays == 0:
            delay = -385 * len(subtitulo.lista_palabras)
        elif n_delays < 3:
            delay=self.delay_media_movil_sin_segmentar
        else:
            delay = self.delay_media_movil[k]

        return delay


    def subtitulo_inerciado(self, subtitulo, instante=None):

        if self.fin_sincronizacion or self.subtitulo_activo is None:
            raise ValueError("Todos los subtitulos estan sincronizados")

        if subtitulo.cronificado:
            raise ValueError("El subtitulo ya esta cronificado")

        if subtitulo not in self.subtitulos:
            raise ValueError("El subtitulo no forma parte del guion")

        if subtitulo is not self.subtitulo_activo:
            raise ValueError("El subtitulo a interpolar siempre tiene que ser el activo")


        t_fin_ultima_sincronizacion = 0 if self.ultimo_subtitulo_sincronizado is None \
            else self.ultimo_subtitulo_sincronizado.t_fin_ajustado
        delay = self.calcula_delay_inerciado(self.subtitulo_activo)

        self.subtitulo_activo.t_inicio_ajustado = self.subtitulo_activo.t_ini + delay
        if self.subtitulo_activo.t_inicio_ajustado < 0:
            self.subtitulo_activo.t_inicio_ajustado = 0
        self.subtitulo_activo.t_fin_ajustado = self.subtitulo_activo.t_inicio_ajustado + \
                                               self.calcula_duracion(self.subtitulo_activo)
        self.subtitulo_activo.cronificado = True
        self.subtitulo_activo.update_time()


        self.subtitulo_activo.estado = Subtitulo.ESTADOS['INERCIADO']
        self.subtitulo_activo.instante_sincronizacion = instante
        self.subtitulo_activo.star = 0  # Los tiempos del asr asociado a sincronizar
        self.subtitulo_activo.end = 0

        if self.ultimo_subtitulo_sincronizado is None:
            self.subtitulo_activo.gap_izquierdo = 0
        else:
            self.subtitulo_activo.gap_izquierdo = self.subtitulo_activo.t_inicio_ajustado - \
                                                  self.ultimo_subtitulo_sincronizado.t_fin_ajustado
            self.ultimo_subtitulo_sincronizado.gap_derecho = self.subtitulo_activo.gap_izquierdo


        try:
            ind_siguiente = self.subtitulos.index(self.subtitulo_activo) + 1
            self.subtitulo_activo = self.subtitulos[ind_siguiente]
            self.ultimo_subtitulo_sincronizado = subtitulo
            sub_anterior = self.ultimo_subtitulo_sincronizado
            sub_anterior.gap_derecho = 0
        except IndexError:
            self.subtitulo_activo = None
            self.fin_sincronizacion = True

        if self.fd_salida_online is not None:
            indice_ultimo = self.subtitulos.index(subtitulo)
            indice_primero = self.subtitulos.index(subtitulo)
            self.graba_subtitulo_ajustado_online([s for s in self.subtitulos[indice_primero:indice_ultimo + 1]])


    def calcula_duracion(self, subtitulo, star=0, end=0):
        duracion = min(subtitulo.duracion, subtitulo.duracion_standard())

        if duracion < Guion.DURACION_MINIMA_SUBTITULO:
            duracion = Guion.DURACION_MINIMA_SUBTITULO
        return duracion


    def sincroniza_subtitulos_anteriores_interpolando(self, subtitulo_activo, subtitulo, star, end, instante):

        ind_activo = self.subtitulos.index(subtitulo_activo)
        ind_subtitulo = self.subtitulos.index(subtitulo)

        #
        # delay_sincronizado es el delay que se aplicaria al subtitulo que se puede sincronizar
        #
        t_ini_1 = 0 if self.ultimo_subtitulo_sincronizado is None else self.ultimo_subtitulo_sincronizado.t_ini
        t_ini_3 = subtitulo.t_ini
        gap31 = t_ini_3 - t_ini_1

        l1 = len(self.ultimo_subtitulo_sincronizado.lista_palabras) if self.ultimo_subtitulo_sincronizado is not None \
            else 0
        l3 = subtitulo.duracion_original
        l3 = len(subtitulo.lista_palabras)

        ultimo_subtitulo_sincronizado = self.ultimo_subtitulo_sincronizado

        delay1 = 0 if self.ultimo_subtitulo_sincronizado is None else self.ultimo_subtitulo_sincronizado.delay
        delay3 = star - t_ini_3
        delay3 = subtitulo.delay  # en esta rutina entra con un delay calculado

        delay1 = self.delay_media_movil_sin_segmentar #El acumulado hasta ahora
        delay3 = 0.5 * (delay1 + delay3)  # en esta rutina entra con un delay calculado

        inerciado = True
        if self.ultimo_subtitulo_sincronizado is not None:
            if self.ultimo_subtitulo_sincronizado.estado is Subtitulo.ESTADOS['SINCRONIZADO']:
                inerciado = False


        delay_star = 0

        for sub in self.subtitulos[ind_activo:ind_subtitulo]:




            gap21 = sub.t_ini - t_ini_1
            gap32 = t_ini_3 - sub.t_ini
            delta = gap21 / gap31  #
            if inerciado:
                delay = self.calcula_delay_inerciado(sub)
            else:
                delay = delta * delay3 + (1 - delta) * delay1
                delay = delay3

                for n, segmento in enumerate(Guion.SEGMENTACION_DELAY):
                    if len(subtitulo.lista_palabras) <= segmento:
                        k = n
                        break
                else:
                    k = -1  # El ultimo
                for n, segmento in enumerate(Guion.SEGMENTACION_DELAY):
                    if len(sub.lista_palabras) <= segmento:
                        j = n
                        break
                else:
                    j = -1  # El ultimo


                if j == k:

                    delay3 = 0.5*(self.get_media_movil(subtitulo)+subtitulo.delay)
                else:

                    delay3 = self.get_media_movil(sub)

                delay = (1-delta)*self.get_media_movil(sub) + delta*delay3




                sub.t_inicio_ajustado = sub.t_ini + delay
                sub.t_fin_ajustado = sub.t_inicio_ajustado + self.calcula_duracion(sub)

                if sub.t_inicio_ajustado > star:
                     sub.t_inicio_ajustado = star - self.GAP_MINIMO_SUBTITULOS

            sub.delay = sub.t_inicio_ajustado - sub.t_ini
            sub.t_fin_ajustado = sub.t_inicio_ajustado + self.calcula_duracion(sub)
            sub.cronificado = True
            sub.update_time()
            sub.estado = Subtitulo.ESTADOS['INTERPOLADO']
            sub.instante_sincronizacion = instante
            sub.star = star
            sub.end = end
            sub.linea_ASR = subtitulo.linea_ASR

            if self.ultimo_subtitulo_sincronizado is None:
                sub.gap_izquierdo = 0
            else:
                sub.gap_izquierdo = sub.t_inicio_ajustado - \
                                                      self.ultimo_subtitulo_sincronizado.t_fin_ajustado
                sub.gap_derecho = sub.gap_izquierdo


            try:
                ind_siguiente = self.subtitulos.index(sub) + 1
                self.subtitulo_activo = self.subtitulos[ind_siguiente]
                self.ultimo_subtitulo_sincronizado = sub
                self.ultimo_subtitulo_sincronizado.gap_derecho = 0  #
            except IndexError:
                self.subtitulo_activo = None
                self.fin_sincronizacion = True

        return delay_star


    def instante_sincronizacion(self):
        return self.subtitulo_activo.t_ini

    def get_subtitulos_pendientes_cronificar(self, instante=0, pendientes=True, finaliza=False):

        no_sincronizados = [s for s in self.subtitulos
                            if not s.cronificado]
        cuantos_quedan = len(no_sincronizados)


        if finaliza or instante == 0:
            todos = True
        else:
            todos = False

        for subtitulo in self.subtitulos:
            if ((not subtitulo.cronificado and pendientes) or not pendientes):
                if todos or subtitulo.t_inicio_ajustado <= instante:
                    yield subtitulo
                else:
                    break

    def get_subtitulos_anteriores(self, subtitulo):
        indice_sub_activo = self.subtitulos.index(self.subtitulo_activo)
        indice_sub_actual = self.subtitulos.index(subtitulo)
        for sub in self.subtitulos[indice_sub_activo:indice_sub_actual]:
            if sub.cronificado:
                print("Este subtitilo esta cronificaco \n")
                raise ValueError
            yield sub

    def get_numero_subtitulos_anteriores(self, subtitulo):
        indice_sub_activo = self.subtitulos.index(self.subtitulo_activo)
        indice_sub_actual = self.subtitulos.index(subtitulo)
        return indice_sub_actual - indice_sub_activo


    def get_subtitulos_srt(self, subtitulos, cronificados=True):
        for subtitulo in subtitulos:
            if cronificados:  # Si los piden cronificados se devuelven con la hora de inicio y fin modificada
                if subtitulo.cronificado:
                    self.prepara_subtitulo_guion(subtitulo)
            yield subtitulo.subtitulo_guion

    def prepara_subtitulo_guion(self, subtitulo):
        quita_formato = re.compile(r'\<.*?>')
        try:
            subtitulo.subtitulo_guion.end = \
                datetime.timedelta(milliseconds=subtitulo.t_fin_ajustado + self.offset_proceso)
        except OverflowError:
            pass
        subtitulo.subtitulo_guion.start = \
            datetime.timedelta(milliseconds=subtitulo.t_inicio_ajustado + self.offset_proceso)
        subtitulo.subtitulo_guion.content = quita_formato.sub("", subtitulo.subtitulo_guion.content)
        if subtitulo.estado == Subtitulo.ESTADOS['INTERPOLADO']:
            self.pon_color(subtitulo, "\"#FF0000\"")

    def pon_color(self, subtitulo, color):
        lineas = subtitulo.subtitulo_guion.content.split("\n")
        contenido = ""
        for linea in lineas:
            if linea is not "":
                contenido = contenido + "<font color=" + color + ">" + linea + "</font>" + "\n"
        subtitulo.subtitulo_guion.content = contenido

    def graba_guion_ajustado(self, fichero_salida, cronificados=True):


        salida_subtitulos = srt.compose(self.get_subtitulos_srt(self.subtitulos, cronificados),
                                        reindex=True,
                                        start_index=1,
                                        strict=True,
                                        eol='\n')
        if fichero_salida == "":
            try:
                fsalida = self._nombre_fichero_guion_entrada.split(".srt")
            except ValueError:
                fsalida = self._nombre_fichero_guion_entrada
            fsalida = fsalida + "_pr_" + time.strftime("%m%d-%H%M%S", time.localtime()) + ".srt"
        else:
            s = fichero_salida.rfind('.')
            fsalida = fichero_salida + ".srt" if s is -1 else fichero_salida[:s] + ".srt"

        with open(fsalida, mode='w', encoding='UTF-8') as f_guion:
            f_guion.write(salida_subtitulos)

    def graba_subtitulo_ajustado_online(self, subtitulos):

        if self.fd_salida_online is None:
            return

        salida_subtitulos = srt.compose(self.get_subtitulos_srt(subtitulos, True),
                                        reindex=False,
                                        start_index=1,
                                        strict=True,
                                        eol='\n')

        try:
            self.fd_salida_online.write(salida_subtitulos)
        except ValueError:
            pass

    NOMBRE_CAMPOS = ["Tipo", "Indice", "Estado", "Score/Confianza", "T_inicio", "T_fin",
                     "Delay", "Texto", "T_inicio_inicial", "T_Final_inicial", "Duracion_inicial", "duracion_final",
                     "Delay proceso", "Algoritmo"]
    FMT_CAMPOS = ["{}", "{}", "{}", "{:6.2f}", "{:6.2f}", "{:6.2f}", "{:6.2f}", "{}", "{:6.2f}", "{:6.2f}", "{:6.2f}",
                  "{:6.2f}", "{:6.2f}", "{}"]

    def get_estadisticas(self):


        n_total = len(self.subtitulos)
        n_sincronizados = len([w for w in self.subtitulos if w.estado == Subtitulo.ESTADOS['SINCRONIZADO']])
        n_interpolados = len([w for w in self.subtitulos if w.estado == Subtitulo.ESTADOS['INTERPOLADO']])
        n_inerciados = len([w for w in self.subtitulos if w.estado == Subtitulo.ESTADOS['INERCIADO']])
        n_pendientes = len([w for w in self.subtitulos if w.estado == Subtitulo.ESTADOS['PENDIENTE']])

        yield [["Subtitulos", "Numero", "Porcentaje"], [["TOTAL", n_total,
                                                         0 if n_total == 0 else 1, ],
                                                        [Subtitulo.ESTADOS['SINCRONIZADO'], n_sincronizados,
                                                         0 if n_total == 0 else n_sincronizados / n_total],
                                                        [Subtitulo.ESTADOS['INTERPOLADO'], n_interpolados,
                                                         0 if n_total == 0 else n_interpolados / n_total],
                                                        [Subtitulo.ESTADOS['INERCIADO'], n_inerciados,
                                                         0 if n_total == 0 else n_inerciados / n_total],
                                                        [Subtitulo.ESTADOS['PENDIENTE'], n_pendientes,
                                                         0 if n_total == 0 else n_pendientes / n_total], ]]

    def get_campos_resultados(self):
        try:
            for subtitulo in self.subtitulos:
                yield [
                    "Guion",
                    subtitulo.subtitulo_guion.index,
                    subtitulo.estado,
                    subtitulo.score_alineamiento,
                    subtitulo.t_inicio_ajustado + self.offset_proceso,
                    subtitulo.t_fin_ajustado + self.offset_proceso,
                    subtitulo.t_ini - subtitulo.t_inicio_ajustado,
                    subtitulo.frase_str,
                    subtitulo.t_ini,
                    subtitulo.t_fin,
                    subtitulo.t_fin - subtitulo.t_ini,
                    subtitulo.t_fin_ajustado - subtitulo.t_inicio_ajustado,
                    subtitulo.instante_sincronizacion - subtitulo.t_inicio_ajustado,
                    subtitulo.algoritmo_usado
                ]
                yield subtitulo.get_campos_linea("ASR", subtitulo.linea_ASR)
                yield subtitulo.get_campos_linea("ASR descartada", subtitulo.frase_ASR_descartada)
                yield subtitulo.get_campos_linea("ASR asociada", subtitulo.frase_ASR_asociada)
                yield subtitulo.get_campos_linea("ASR no usada", subtitulo.frase_ASR_no_usada)

        except:
            raise

    def get_informe_alineamientos(self):
        try:
            for subtitulo in self.subtitulos:
                if subtitulo.alineamiento_subtitulo is not None:
                    retorno = ["Subtitulo", subtitulo.subtitulo_guion.index] + \
                              [w.palabra_str if w is not None else "-" for w in subtitulo.alineamiento_subtitulo]
                    yield retorno
                if subtitulo.alineamiento_ASR is not None:
                    retorno = ["ASR", " "] + \
                              [w.palabra_str if w is not None else "-" for w in subtitulo.alineamiento_ASR]
                    yield retorno
                if subtitulo.alineamiento_ASR is not None:
                    retorno = ["Instante", subtitulo.t_inicio_ajustado] + \
                              [w.instante if w is not None else "-" for w in subtitulo.alineamiento_ASR]
                    yield retorno
                if subtitulo.score_pareja is not None:
                    retorno = ["Score", subtitulo.score_alineamiento, ] + [w for w in subtitulo.score_pareja]
                    yield retorno
                yield [" "]

        except:
            raise




def parse_txt(fd, milisegundos=True):

    if isinstance(fd, (io.IOBase,)):
        indice = 1
        proprietary = ""
        for line in fd:
            start, end, content = re.split('\t', line, 2)
            content = content.replace("#", "\n")
            try:
                start = float(start.replace(",", ""))
                end = float(end.replace(",", ""))
            except ValueError:
                print("error formato tiempos subtitulo")
                raise
            if not milisegundos:
                start = 1000 * start
                end = 1000 * end

            yield srt.Subtitle(
                index=indice,
                start=datetime.timedelta(milliseconds=start),
                end=datetime.timedelta(milliseconds=end),
                content=content.replace("\r\n", "\n"),
                proprietary=proprietary,
            )
