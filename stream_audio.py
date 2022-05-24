# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 19:55:26 2020

@author: max
"""

import time
from six.moves import queue
import struct

STREAMING_LIMIT = 240000
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100 ms
CYCLE_MAX_LENGH_INITIAL_SAMPLE_MS = 10000  # la longitud inicial maxima a enviar  10 seg.


class ExcepcionGeneradorAudio(RuntimeError):
    def __init__(self, arg):
        self.args = arg


class ResumableStream:

    def __init__(self, rate, chunk_size, tiempo_de_ciclo):
        self.ciclos = 0
        self.fd_transcripcion = None
        self.tiempo_de_ciclo = tiempo_de_ciclo
        self.instante_ultima_trama_audio = 0
        self.resultados_intermedios = False
        self.chunks_ultimo_ciclo = 0
        self.tramas_generadas_ultimo_ciclo = 0
        self.max_longitud_trama_inicial_ciclo = CYCLE_MAX_LENGH_INITIAL_SAMPLE_MS
        self.offset = 0

        self.chunks_leidos = 0
        self.offset_trama_audio = 0
        self.rate = rate
        self.chunk_size = chunk_size
        try:
            self.chunk_time = chunk_size * 1000.0 / rate
        except:
            self.chunk_time = 0

        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = 0
        self.instante_apertura_mic = self.get_current_time()
        self.restart_counter = 0
        self.audio_inicial_ciclo = []
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True

        self.descarte_tiempo_inicial = 0
        self.descarte_tiempo_final = 0
        self.hay_descarte = False

        self.instante_ultimo_proceso = 0
        self.pausa_generador = False
        self.bucle_por_final = False

    def __enter__(self):

        self.instante_apertura_mic = self.get_current_time()
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True

    def get_current_time(self):
        return int(round(time.time() * 1000))

    def get_configuracion(self):

        lista = [
            ["Tipo stream", self.__class__.__name__],
            ["Sample rate", self.rate],
            ["Chunk size", self.chunk_size],
            ["Chunk time(ms)", self.chunk_time],
            ["Tiempo ciclo", self.tiempo_de_ciclo],
            ["Control del ciclo", "Generador audio" if self.pausa_generador else "motor ASR"],
        ]
        return lista

    def vuelca_configuracion(self):
        if self.fd_transcripcion is not None:
            self.fd_transcripcion.write("Conf\t {0} \n".format(type(self).__name__))
            configuracion = "Conf\tSample rate {0} chunk size {1} tiempo muestra: {2} " \
                            " tiempo de ciclo = {3} Control del ciclo por {4}\n".format(
                self.rate,
                self.chunk_size,
                self.chunk_time,
                self.tiempo_de_ciclo,
                "generador audio" if self.pausa_generador else "trasncriptor")
            self.fd_transcripcion.write(configuracion)

    def enlaza_audios(self, data):

        audio_ciclo = self.audio_inicial_ciclo + self.last_audio_input

        chunk_time = self.tiempo_de_ciclo * 1000 / len(self.last_audio_input)

        posicion_ultima_trama_final = round(self.final_request_end_time / self.chunk_time)
        puntero_corte_max = len(audio_ciclo) - round(self.max_longitud_trama_inicial_ciclo / self.chunk_time)
        if puntero_corte_max < 0:
            puntero_corte_max = 0

        if puntero_corte_max > posicion_ultima_trama_final:
            posicion_corte = puntero_corte_max
            audios_descartados = puntero_corte_max - posicion_ultima_trama_final
            self.hay_descarte = True
            self.descarte_tiempo_inicial = self.offset + self.final_request_end_time
            self.descarte_tiempo_final = self.descarte_tiempo_inicial + audios_descartados * self.chunk_time
        else:
            posicion_corte = posicion_ultima_trama_final
            audios_descartados = 0

        self.offset = self.offset + posicion_corte * self.chunk_time
        self.start_time = self.offset

        salida = ("Ciclo anterior --> Tiempo Total: " +
                  str(self.chunk_time * len(self.last_audio_input)) +
                  " Numero tramas " + str(len(self.last_audio_input)) +
                  "\nPosicion trama final: " + str(posicion_ultima_trama_final) +
                  " Instante trama final: " + str(self.final_request_end_time) +
                  "\nPosicion Corte final: " + str(posicion_corte) +
                  " Instante Corte: " + str(posicion_corte * self.chunk_time) +
                  "\nFrames de Audios descartados: " + str(audios_descartados) +
                  " Nuevo Offset: " + str(self.offset))

        salida = salida.replace('\n', ' ')

        if self.fd_transcripcion is not None:
            self.fd_transcripcion.write("Info.\t" + salida + '\n')
        self.final_request_end_time = 0

        self.audio_inicial_ciclo = []
        for audio in audio_ciclo[posicion_corte:]:
            self.audio_inicial_ciclo.append(audio)
            data.append(audio)

    def generator_audios(self):
        raise NotImplementedError
