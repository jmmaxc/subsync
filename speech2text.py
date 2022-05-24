
import presentacion
import time



class Resultado:


    def __init__(self):
        self.offset = 0
        self.final_forzado = False
        self.es_trama = False
        self.transcript = None
        self.is_final = False
        self.confidence = 0
        self.result_end_time = 0
        self.corrected_time = 0



CAUSAS_REINICIO = {'FRASE_FINAL': 'FRASE_FINAL',
                   'GENERADOR': 'GENERADOR',
                   'MOTOR': 'MOTOR',
                   'ERROR MOTOR':'ERROR MOTOR',
                   'SIN CAUSA': 'SIN_CAUSA',
                   }


class MotorTranscripcion:

    def __init__(self):
        self.cfg_fuerza_fin_frase = False
        self.intervalo_max_frase_fin = 0
        self.fuerza_ciclo_fin_frase = False
        self.gestor_transcripcion = None
        self.causa_nuevo_bucle = CAUSAS_REINICIO['SIN CAUSA']
        self.instante_ultimo_resultado = 0

        self.palabra_sincronizacion = None
        self.instante_palabra_sincronizacion = 0
        self.sincronizado_motor_audio = False
        self.offset_sincronizacion = 0

        self.resultados = []
        self.instante_primera_respuesta = None

    def get_configuracion(self):
        lista = [["Motor", self.__class__.__name__],
                 ["Fuerza fin frase", self.cfg_fuerza_fin_frase],
                 ["Intervalo frase forzada", self.intervalo_max_frase_fin],
                 ["Palabra sincronizacion", self.palabra_sincronizacion],
                 ["Instante sincronizacion", self.instante_palabra_sincronizacion],

                 ]
        return lista


    def _procesa_resultado_asr(self, response):
        raise NotImplementedError("_procesa_resultados_asr es Metodo abstracto")

    def transcribe(self, gestor_transcripcion):
        raise NotImplementedError("transcribe es un metodo abstracto")


    def procesa_resultados_asr(self, responses):

        stream = self.gestor_transcripcion.mic_manager
        procesadas = 0
        print("speech2text --> Inicio bucle de responses {0}".format(stream.get_current_time()))
        tiempo = stream.get_current_time()
        salida_pantalla = None
        longitud = 0
        trama = None
        trama_anterior = None
        informacion_nueva = False

        for response in responses:

            resultado, reinicio_ciclo, error = self._procesa_resultado_asr(response)

            if error is not None:
                try:
                    stream.fd_transcripcion.write("Info\t{0}\n".format(error))
                except:
                    pass

            if reinicio_ciclo:
                presentacion.imprimir(
                    "{0} {1} procesa ASR -> Se reinicia el ciclo".format(stream.get_current_time(),
                                                                         self.__class__.__name__))
                break

            if resultado is None:

                continue

            if not resultado.es_trama:

                continue

            if resultado.corrected_time - self.instante_ultimo_resultado > 2000:
                presentacion.imprimir("{} Tiempo entre resultados demasiado largo:  {} {}".
                                      format(resultado.corrected_time,
                                             self.instante_ultimo_resultado,
                                             resultado.corrected_time - self.instante_ultimo_resultado))

            self.instante_ultimo_resultado = resultado.corrected_time
            procesadas += 1


            self.resultados.append(resultado)

            salida = "{0}\t{1}\t{2}\tc = {3:.2f}\n".format(
                resultado.corrected_time,
                resultado.result_end_time,
                resultado.transcript,
                resultado.confidence)

            if self.instante_primera_respuesta is None:
                self.instante_primera_respuesta = int(round(time.time() * 1000))
                print("Instante primera respuesta: {0} --> {1}".format(self.instante_primera_respuesta, salida))

            if trama is None:

                trama = resultado.transcript
            else:
                if resultado.transcript[0:len(trama_anterior)] == trama_anterior:  # Todo lo anterior igual
                    trama = resultado.transcript[len(trama_anterior):]  # lo nuevo, si no hay nada nuevo esto vale 0
                else:

                    trama = resultado.transcript

            trama_anterior = resultado.transcript

            if len(trama) == 0:
                informacion_nueva = False
            else:
                informacion_nueva = True

                if not self.sincronizado_motor_audio:
                    if self.palabra_sincronizacion is None:
                        self.sincronizado_motor_audio = True
                        self.offset_sincronizacion = 0
                    else:
                        if not trama.find(self.palabra_sincronizacion) == -1:
                            self.sincronizado_motor_audio = True
                            self.offset_sincronizacion = self.instante_palabra_sincronizacion - resultado.corrected_time

                            print("Offset sincro: ", self.offset_sincronizacion)

            salida_pantalla = "{0}\t{1}\t{2}\tc = {3:.2f}\n".format(
                resultado.corrected_time,
                resultado.result_end_time,
                trama,
                resultado.confidence)


            stream.result_end_time = resultado.result_end_time
            stream.last_transcript_was_final = resultado.is_final

            if resultado.final_forzado and not resultado.is_final:
                salida = "FinalF\t" + salida
                salida_pantalla = salida
                trama = None
                informacion_nueva = True
            elif resultado.is_final:
                salida = "Final\t" + salida
                salida_pantalla = salida

                stream.is_final_end_time = resultado.result_end_time
                trama = None
                informacion_nueva = True
            elif not resultado.final_forzado and not resultado.is_final:
                salida = "Inter\t" + salida
                if stream.resultados_intermedios:
                    salida_pantalla = "Inter\t" + salida_pantalla
                else:
                    salida_pantalla = None
            else:
                presentacion.imprimir("Problemas en speech2text")
            if informacion_nueva and salida_pantalla is not None:
                presentacion.imprimir(salida_pantalla)


            try:
                stream.fd_transcripcion.write(salida)
            except:
                pass


            if informacion_nueva and self.sincronizado_motor_audio:
                for resultado in self.resultados:

                    if resultado.confidence > 0.2:
                        self.gestor_transcripcion.sincronizador.procesa_ASR(resultado.transcript,
                                                                            resultado.corrected_time +
                                                                            self.offset_sincronizacion,
                                                                            resultado.confidence,
                                                                            resultado.is_final or resultado.final_forzado,
                                                                            resultado.offset)

            if self.sincronizado_motor_audio:
                self.resultados = []
        return procesadas
