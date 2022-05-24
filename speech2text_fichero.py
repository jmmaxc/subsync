# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 19:55:26 2020

@author: max

Lo que hacemos es leer las tramas de texto que generaría un speech_text pero
leidas desde un fichero

Es una clase de procesar tramas de trasncripcion pero leyendo de un ficher

Vamos a utilizar un generador de tramas generador_tramas_trasncripcion

que se le pasara a un procesado de frases

"""

import speech2text
import presentacion



class ResultadoTrama(speech2text.Resultado):
    def __init__(self, linea):
        super().__init__()

        self.final_forzado = False
        # lista = linea.replace('\n','').split('\t')
        lista = linea.split('\t')
        self.es_trama = (lista[0] == "Final" or lista[0] == "Inter" or lista[0] == "FinalF")
        es_final = (lista[0] == "Final" or lista[0] == "FinalF")
        self.final_forzado = lista[0] == "FinalF"

        if self.es_trama:
            self.is_final = es_final
            try:
                self.corrected_time = float(lista[1])
                self.result_end_time = float(lista[2])
                self.offset = self.corrected_time - self.result_end_time
            except ValueError("Error formato fichero"):
                raise
            self.transcript = lista[3]
            try:
                self.confidence = float(lista[4].split("=")[1])
            except:
                presentacion.imprimir("Error formato fichero de tramas")
                self.confidence = 0


class MotorTranscripcionTramas(speech2text.MotorTranscripcion):
    def __init__(self):
        super().__init__()

    def get_configuracion(self):
        lista = super().get_configuracion()
        return lista

    def transcribe(self, gestor_transcripcion):

        self.gestor_transcripcion = gestor_transcripcion
        mic_manager = self.gestor_transcripcion.mic_manager
        mic_manager.vuelca_configuracion()

        with mic_manager as stream:
            responses = stream.generator_audios()
            procesadas = self.procesa_resultados_asr(responses)

    def _procesa_resultado_asr(self, response):


        resultado = None
        reinicio = False


        resultado = ResultadoTrama(response)  # Convertimos las tramas en resultados

        return resultado, reinicio, None
