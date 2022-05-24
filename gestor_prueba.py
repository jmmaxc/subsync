
import time
import gestor_transcripcion
import stream_tramas
import speech2text_fichero
import sincronizador
import distancias
import alineamientos
import factory
import entropias

import json

class ValoresJSON:
    def __init__(self, d):
        self.d = d
    def get(self, clv, valor):
        try:
            ret = self.d[clv]
        except:
            ret = valor
        return ret


class Prueba:
    def __init__(self, config):

            self.config = config
            stream = ValoresJSON(self.config['Stream'])
            motor_transcripcion = ValoresJSON(self.config['MotorTranscrripcion'])
            distancia = ValoresJSON(self.config['Distacia'])
            entropia = ValoresJSON(self.config['Entropia'])
            algoritmo = ValoresJSON(self.config['Algoritmo'])
            sincronizador_j = ValoresJSON(self.config['Sincronizador'])
            gestor_transcripcion_j = ValoresJSON(self.config['GestorTranscripcion'])

            # stream
            self.fichero_tramas = stream.get('fichero_tramas', None)
            self.pausa_generador = stream.get('pausa_generador', False)
            self.resultados_intermedios = stream.get('resultados_intermedios', False)
            self.tipo_stream = 'TRAMAS'
            self.proceso_por_tramas = True
            self.stream = None

            # MotorTranscrripcion
            self.palabra_sincronizacion = motor_transcripcion.get('palabra_sincronizacion', None)
            self.instanta_palabra_sincronizacion = motor_transcripcion.get('instanta_palabra_sincronizacion', 0)
            self.resultados_intermedios = motor_transcripcion.get('resultados_intermedios', False)
            self.tipo_motor = 'TRAMAS'
            self.motor_transcripcion = None

            # Distancia
            self.tipo_distancia = GestorPrueba.DISTANCIAS[distancia.get('tipo_distancia', 'DEFECTO')]
            self.tolerancia_igualdad = distancia.get('tolerancia_igualdad', 0.1)
            self.tolerancia_desigualdad = distancia.get('tolerancia_igualdad', 0.6)
            self.distancia = None

            # Entropia
            self.tipo_entropia = GestorPrueba.ENTROPIAS[entropia.get('tipo_entropia', 'DEFECTO')]
            self.largo_min_palabra = entropia.get('largo_min_palabra', 3)
            self.entropia = None

            # Algoritmo
            self.tipo_algoritmo = GestorPrueba.ALGORITMOS[algoritmo.get('tipo_algoritmo', 'SW')]
            self.coste_igualdad = algoritmo.get('coste_igualdad', 1)
            self.coste_desigualdad = algoritmo.get('coste_desigualdad', -1)
            self.coste_insercion_subtitulo = algoritmo.get('coste_insercion_subtitulo', -2)
            self.coste_insercion_transcripcion = algoritmo.get('coste_insercion_transcripcion', -2)
            self.algoritmo = None

            # Sincronizador
            self.sincroniza = sincronizador_j.get('sincroniza', True)
            self.fichero_guion = sincronizador_j.get('fichero_guion', None)
            self.pierde_palabras = sincronizador_j.get('pierde_palabras', True)
            self.longitud_minima_frase = sincronizador_j.get('longitud_minima_frase', 6)
            self.confianza_minima = sincronizador_j.get('confianza_minima', 0.7)
            self.score_minimo = sincronizador_j.get('score_minimo', 0.6)
            self.tiempo_adelanto = sincronizador_j.get('tiempo_adelanto', 0)
            self.tiempo_maximo_sin_sincronizar = sincronizador_j.get('tiempo_maximo_sin_sincronizar', 20000)
            self.nivel_trazas_sincronizador = sincronizador_j.get('nivel_trazas_sincronizador', 0)
            self.sincronizador = None

            # Gestor transcripcion
            self.fichero_transcripcion = gestor_transcripcion_j.get('fichero_transcripcion', None)
            self.fichero_frases = gestor_transcripcion_j.get('fichero_frases', None)
            self.fichero_salida_guion = gestor_transcripcion_j.get('fichero_salida_guion', None)
            self.ciclos = gestor_transcripcion_j.get('ciclos', 10)
            self.gestor_transcripcion = None

    def inicia_transcripcion(self):
        print("Servidor Sincrosub --> Crea la tarea de transcripcion {0}".format(int(round(time.time() * 1000))))

        self.stream = stream_tramas.ResumableFicheroTramasStream(self.fichero_tramas)

        self.motor_transcripcion = speech2text_fichero.MotorTranscripcionTramas()
        self.motor_transcripcion.palabra_sincronizacion = self.palabra_sincronizacion
        self.motor_transcripcion.instante_palabra_sincronizacion = self.instanta_palabra_sincronizacion

        self.distancia = factory.get_distancia(self.tipo_distancia,
                                               self.tolerancia_desigualdad,
                                               self.tolerancia_igualdad)

        self.entropia = entropias.Entropia(
            largo_palabra=self.largo_min_palabra)


        self.algoritmo = factory.get_algoritmo(self.tipo_algoritmo,
                                               self.distancia,
                                               self.entropia,
                                               None,
                                               self.coste_igualdad,
                                               self.coste_desigualdad,
                                               self.coste_insercion_subtitulo,
                                               self.coste_insercion_transcripcion,
                                               )

        self.sincronizador = sincronizador.Sincronizador(self.distancia,
                                                         self.entropia,
                                                         self.algoritmo,
                                                         self.fichero_guion,
                                                         pierde_palabras=self.pierde_palabras,
                                                         longitud_minima_frase=self.longitud_minima_frase,
                                                         score_minimo=self.score_minimo,
                                                         tiempo_adelanto=self.tiempo_adelanto,
                                                         tiempo_maximo_sin_sincronizar= \
                                                             self.tiempo_maximo_sin_sincronizar)
        if self.sincroniza:
            self.sincronizador.procesa_guion = True
            self.sincronizador.nivel_trazas_sincronizador = self.nivel_trazas_sincronizador
        else:
            self.sincronizador.procesa_guion = False
        self.sincronizador.fichero_salida_guion = None

        self.gestor_transcripcion = gestor_transcripcion.GestorTranscripcion(self.motor_transcripcion,
                                                                             self.stream,
                                                                             self.sincronizador,
                                                                             self.fichero_transcripcion,
                                                                             self.fichero_frases,
                                                                             self.fichero_salida_guion,
                                                                             self.ciclos, )
        self.gestor_transcripcion.inicia_transcripcion()

    def fin_transcripcion(self):
        if self.gestor_transcripcion is None:
            raise
        self.stream.closed = True
        self.stream = None
        self.motor_transcripcion = None
        self.distancia = None
        self.entropia = None
        self.algoritmo = None
        self.sincronizador = None
        self.gestor_transcripcion = None




class GestorPrueba:
    STREAMS = {
        'TRAMAS': stream_tramas.ResumableFicheroTramasStream.__name__
    }

    ALGORITMOS = alineamientos.ALGORITMOS
    DISTANCIAS = distancias.DISTANCIAS

    ENTROPIAS = {'DEFECTO': entropias.Entropia.__name__}
    MOTORES = {'TRAMAS': speech2text_fichero.MotorTranscripcionTramas.__name__,
               }

    def __init__(self,configuracion_file ):

        self.json_file = configuracion_file

        with open(self.json_file, "r") as fileObject:
            self.json_content = fileObject.read()

        self.config = json.loads(self.json_content)

        self.pruebas = [Prueba(config) for config in self.config]


    def get_pruebas(self):
        for prueba in self.pruebas:
            yield prueba



