# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 19:55:26 2020

@author: max
"""

import stream_audio

class ResumableFicheroTramasStream(stream_audio.ResumableStream):

    def __init__(self, fichero_tramas, rate = 0, chunk_size =0, tiempo_de_ciclo = 0):
        stream_audio.ResumableStream.__init__(self,rate,chunk_size,tiempo_de_ciclo)
        self.pausa_generador = True
        self._fichero = fichero_tramas
        try:
            self.fd_tramas_in = open(fichero_tramas,'r')
        except:
            self.fd_tramas_in = None
            raise RuntimeError("Error apertura fichero interno: {fichero_tramas}")



    def __exit__(self, type, value, traceback):

        stream_audio.ResumableStream.__exit__(self, type, value, traceback)
        if self.fd_tramas_in is not None:
            self.fd_tramas_in.close()

    def get_configuracion(self):
        lista = super().get_configuracion()
        lista.append(["Fichero de entrada de tramas", self._fichero])
        return lista

    def vuelca_configuracion(self):
        stream_audio.ResumableStream.vuelca_configuracion(self)
        if self.fd_transcripcion is not None:
            self.fd_transcripcion.write("Conf\t"+self._fichero+'\n')



    def generator_audios(self):

        for linea in self.fd_tramas_in :
            yield linea






