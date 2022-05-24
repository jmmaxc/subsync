import proceso_frases
import presentacion
import time


class GestorTranscripcion:
    """
        Esta es la clase que se encarga de gestionar todo el proceso, coordina el stream de audio, el motor de ASR y
        el sincronizado, en principio se deberia llamar lanzando un Threat del metodo inicia_trasncripicion
        es el metodo que ejecuta todo el proceso y cuando finaliza termina
        Para cerrar asincronamente este objeto y que finalice ordenadamente hay que llamar al metodo finaliza
        transcripcion
    """

    def __init__(self,
                 motor_transcripcion,
                 mic_manager,
                 sincronizador,
                 fichero_transcripcion,
                 fichero_frases,
                 fichero_salida_guion,
                 ciclo,
                 servidor_subtitulos=None):

        """
            :param  motor_transcripcion: es el motor de ASR que se va a usar, en general es Google o un lector de tramas
            :param  mic_manager: es el stream que genera el audio que se pasa al motor de transcipcion
            :param  sincronizador: la clase encargada de procesar las trmas ASR generadas por el motor de transcricion
                    se encarga de sinronizar los ASR con el guion que tiene configurado, usando diferentes algoritmos
            :param  fichero_transcripcion: es el fichero donde se almacenan las tramas ASR que devuelve el motor
            :param  fichero_frases: es el fichero donde se almacenan las frases, las palabras que el ASR reconoce
                    despues de un proceso inicial que consiste en asignar el tiempo en milisegundos a la palabra
                    mas ajustada. Por cada palabra graba el instante de la primera aparicion, el numero de veces que
                    aparece en el contexto de una misma frase y el indice de confianza que devuelve el ASR para esa
                    palabra
            :param  fichero_salida_guion: es el fichero donce se guardan los resultados de la sincronizacion, se generan
                    tres ficheros con este nombre y formatos .srt, .xlsm, .csv
        """
        self.motor_transcripcion = motor_transcripcion
        self.mic_manager = mic_manager
        self.sincronizador = sincronizador
        self.fichero_transcripcion = fichero_transcripcion
        self.fichero_frases = fichero_frases
        self.fichero_salida_guion = fichero_salida_guion
        self.ciclo = ciclo
        self.servidor_subtitulos = servidor_subtitulos
        self.cola_servidor_subtitulos = None
        self.cola_retorno = None
        self.tiempo_proceso = 0

    def get_configuracion(self):
        lista = [["Gestor Transcripcion", self.__class__.__name__],
                 ["Frases", self.fichero_frases],
                 ["Transcripcion", self.fichero_transcripcion],
                 ["Guion ajustado", self.fichero_salida_guion],
                 ["Motor", self.motor_transcripcion.get_configuracion()],
                 ["Stream", self.mic_manager.get_configuracion()],
                 ["Sincronizador", self.sincronizador.get_configuracion() if self.sincronizador is not None else None],
                 ["Servidor Subtitulos", self.servidor_subtitulos],
                 ]
        return lista

    def get_parametros(self):
        lista = [["Tiempo proceso", self.tiempo_proceso]] + self.sincronizador.get_parametros()

        return lista

    def inicia_transcripcion(self, motor_transcripcion=None,
                             mic_manager=None,
                             fichero_transcripcion=None,
                             fichero_frases=None,
                             ciclo=None,
                        ):



        if motor_transcripcion is not None:
            self.motor_transcripcion = motor_transcripcion

        if mic_manager is not None:
            self.mic_manager = mic_manager

        if fichero_transcripcion is not None:
            self.fichero_transcripcion = fichero_transcripcion

        if fichero_frases is not None:
            self.fichero_frases = fichero_frases

        if ciclo is not None:
            self.ciclo = ciclo

        if self.motor_transcripcion is None or \
                self.mic_manager is None or \
                self.fichero_transcripcion is None:
            raise RuntimeError("El gestor de transcripcion no esta bien configurado")

        self.mic_manager.ciclos = self.ciclo

        self.sincronizador.inicializa(self)

        try:
            if self.sincronizador.guion.fichero_salida_guion_online is not None:
                with open(self.fichero_transcripcion, 'w') as self.mic_manager.fd_transcripcion, \
                        open(self.sincronizador.guion.fichero_salida_guion_online,
                             mode='w', encoding='UTF-8') as \
                                self.sincronizador.guion.fd_salida_online:
                    self.tiempo_proceso = time.time()
                    self.motor_transcripcion.transcribe(self)
                    self.tiempo_proceso = time.time() - self.tiempo_proceso
                    instante = self.sincronizador.frases.get_frase_ASR().get_instante_final()
                    self.sincronizador.finaliza(instante)
            else:
                with open(self.fichero_transcripcion, 'w') as self.mic_manager.fd_transcripcion:
                    self.tiempo_proceso = time.time()
                    self.motor_transcripcion.transcribe(self)
                    self.tiempo_proceso = time.time() - self.tiempo_proceso
                    instante = self.sincronizador.frases.get_frase_ASR().get_instante_final()
                    self.sincronizador.finaliza(instante)

        except FileExistsError:
            proceso_frases.imprimir("Gst transcripccion Error apertura fichero: {0}".format(self.fichero_transcripcion))
            #
            # Se continua con el proceso pero no va a haber salida de tramas
            #
            self.mic_manager.fd_transcripcion = None
            self.motor_transcripcion.transcribe(self)

        #
        # Esta llamada es para que la ultima frase que puede no haberse transcrito como final
        # Se alamacene antes del volcado
        #

        # instante = self.sincronizador.frases.get_frase_ASR().get_instante_final()
        # self.sincronizador.finaliza(instante)
        self.sincronizador.frases.finaliza()
        try:
            with open(self.fichero_frases, 'w') as fd:
                self.sincronizador.frases.imprime_frases(fd)
        except FileExistsError:
            proceso_frases.imprimir("Error apertura fichero: {0}".format(self.fichero_frases))

        s = self.fichero_frases.rfind('.')
        fichero_tramas = self.fichero_frases + "-trm" if s is -1 else self.fichero_frases[:s] + "-trm."

        presentacion.graba_campos_fichero_excel(fichero_tramas,
                                                ["Id Frase", "Tipo"] + self.sincronizador.frases.NOMBRE_CAMPOS_PALABRAS,
                                                self.sincronizador.frases.FMT_CAMPOS_PALABRAS,
                                                'Palabras',
                                                self.sincronizador.frases.generador_palabras_frases())
        presentacion.graba_campos_fichero_excel(fichero_tramas,
                                                self.sincronizador.frases.NOMBRE_CAMPOS_FRASE,
                                                self.sincronizador.frases.FMT_CAMPOS_FRASE,
                                                'Frases',
                                                self.sincronizador.frases.generador_frases())

        if self.fichero_salida_guion is not None:
            try:

                self.sincronizador.guion.graba_guion_ajustado(self.fichero_salida_guion)



                presentacion.graba_campos_fichero_excel(self.fichero_salida_guion,
                                                        self.sincronizador.guion.NOMBRE_CAMPOS,
                                                        self.sincronizador.guion.FMT_CAMPOS,
                                                        'Resultados',
                                                        self.sincronizador.guion.get_campos_resultados())
                presentacion.graba_campos_fichero_excel(self.fichero_salida_guion,
                                                        None,
                                                        None,
                                                        'Alineamientos',
                                                        self.sincronizador.guion.get_informe_alineamientos())
                presentacion.graba_estadisticas(self.fichero_salida_guion,
                                                'Estadisticas',
                                                self.sincronizador.guion.get_estadisticas())

                presentacion.graba_configuracion_fichero_excel(self.fichero_salida_guion,
                                                               self.get_configuracion(),
                                                               self.get_parametros())
            except FileExistsError:
                proceso_frases.imprimir("Error apertura fichero: {0}".format(self.fichero_salida_guion))

        presentacion.imprimir(self.get_configuracion())

        proceso_frases.imprimir("Gestor de transcripcion -> Fin del proceso")


def finaliza_transcripcion(self):
    if self.mic_manager is None:
        raise

    self.mic_manager.closed = True
