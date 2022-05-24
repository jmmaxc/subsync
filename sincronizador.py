
import proceso_frases
import proceso_guion
import similitud
import copy


class Sincronizador:
    def __init__(self, distancia, entropia, algoritmo, fichero_guion,
                 fichero_salida_guion_online=None,
                 pierde_palabras=True,
                 confianza_minima=0.7,
                 score_minimo=0.5,
                 longitud_minima_frase=6,
                 tiempo_adelanto=5000,
                 tiempo_maximo_sin_sincronizar=0):
        self.confianza_minima = confianza_minima
        self.longitud_minima_frase = longitud_minima_frase
        self.score_minimo = score_minimo
        self.tiempo_max_sin_sincronizar = tiempo_maximo_sin_sincronizar
        self.tiempo_adelanto = tiempo_adelanto
        self.pierde_palabras = pierde_palabras
        self.frases = None
        self.guion = None
        self.fichero_guion = fichero_guion
        self.fichero_salida_guion_online = fichero_salida_guion_online
        self.instante_sincronizacion_guion = 0
        self.subtitulo_activo = None
        self.distancia = distancia
        self.algoritmo = algoritmo
        self.algoritmo_auxiliar = copy.deepcopy(algoritmo)
        self.entropia = entropia
        self.procesa_guion = False
        self.gestor_transcripcion = None
        self.offset_proceso = 0
        self.ultima_sincronizacion = 0
        self.nivel_trazas_sincronizador = 2
        self.instanta_ultimo_intento_sinc = 0
        self.ciclo_sincronizacion = 100

    def get_configuracion(self):
        lista = [["Sincronizador", self.__class__.__name__],
                 ["Pierde Palabras", self.pierde_palabras],
                 ["Guion inicial", self.fichero_guion],
                 ["Confianza minima", self.confianza_minima],
                 ["Score minimo", self.score_minimo],
                 ["Longitud minima frase", self.longitud_minima_frase],
                 ["Tiempo adelanto", self.tiempo_adelanto],
                 ["Tiempo max sin sincronizar", self.tiempo_max_sin_sincronizar],
                 ["Algoritmo",
                  None if self.algoritmo is None else self.algoritmo.get_configuracion()]
                 ]
        return lista

    def get_parametros(self):
        lista = [
            ["Confianza minima", self.confianza_minima],
            ["Score minimo", self.score_minimo],
            ["Longitud minima frase", self.longitud_minima_frase],
            ["Tiempo adelanto", self.tiempo_adelanto],
            ["Tiempo max sin sincronizar", self.tiempo_max_sin_sincronizar],
        ]
        return lista + self.algoritmo.get_parametros() + self.guion.get_parametros()

    def inicializa(self, gestor_transcripcion):
        self.gestor_transcripcion = gestor_transcripcion
        self.frases = proceso_frases.Frases()
        if self.fichero_guion is not None:
            self.guion = proceso_guion.Guion(self.fichero_guion, self.fichero_salida_guion_online)

    def set_offset_proceso(self, offset):
        self.offset_proceso = offset
        if self.guion is not None:
            self.guion.set_offset_proceso(self.offset_proceso)

    def procesa_ASR(self, transcripcion, instante, confidence, is_final, offset):


        frase = proceso_frases.Frase(transcripcion, instante, confidence, is_final, offset=offset)
        self.frases.add_frase(frase,
                              is_final,
                              self.pierde_palabras)


        if not self.procesa_guion:
            return

        if self.nivel_trazas_sincronizador == 1:
            print("Nueva Frase asr: T0:{0} Tf:{1} c={2:4.2f} ...{3}".format(frase.get_instante_inicial(),
                                                                            frase.get_instante_final(),
                                                                            frase.get_confianza(),
                                                                            self.frases.get_frase_ASR().
                                                                            get_ultimas_incorporaciones()))


        if (instante - self.instanta_ultimo_intento_sinc) > self.ciclo_sincronizacion:
            self.instanta_ultimo_intento_sinc = instante
            if (instante < self.guion.get_instante_ultimo_subtitulo() + 5000):
                self.sincroniza(instante, finaliza=False)

    def finaliza(self, instante):
        if self.procesa_guion:
            self.sincroniza(instante, finaliza=True)

    def sincroniza(self, instante, finaliza):

        for frase_asr in self.frases.generador_frases_asr(quita_palabra_corte=False):
            sim = None


            try:
                self.tiempo_sin_sincronizar = frase_asr.get_instante_final() - frase_asr.get_instante_inicial()
            except IndexError or ValueError:
                self.tiempo_sin_sincronizar = 0


            lng_transcripcion = self.algoritmo.entropia_transcripcion_T.numero_palabras(frase_asr.lista_palabras)
            if frase_asr.get_confianza() >= self.confianza_minima and \
                    (lng_transcripcion > self.longitud_minima_frase or finaliza):


                sim = None

                subtitulo_max_score = None
                score_max = self.score_minimo
                subtitulos_superan_corte = []

                for subtitulo in self.guion.get_subtitulos_pendientes_cronificar(
                        instante=instante + self.tiempo_adelanto, finaliza=finaliza):
                    self.algoritmo.calcula_similitud(subtitulo.lista_palabras,
                                                     frase_asr.lista_palabras,
                                                     )


                    subtitulo.alineamiento_subtitulo = self.algoritmo.alineamiento_subtitulo_S
                    subtitulo.alineamiento_ASR = self.algoritmo.alineamiento_transcripcion_T
                    subtitulo.score_pareja = self.algoritmo.score_pareja
                    subtitulo.score_alineamiento = self.algoritmo.score_alineamiento
                    subtitulo.algoritmo_usado = self.algoritmo.algoritmo_usado
                    if self.algoritmo.score_alineamiento >= self.score_minimo:
                        subtitulos_superan_corte.append([self.algoritmo.score_alineamiento, subtitulo])
                        if self.algoritmo.score_alineamiento >= score_max:
                            score_max = self.algoritmo.score_alineamiento
                            subtitulo_max_score = subtitulo
                            break
                    elif (0 < self.tiempo_max_sin_sincronizar < instante - subtitulo.t_ini) or finaliza:
                        subtitulo.linea_ASR = proceso_frases.FraseASR(frase_asr)
                        subtitulo.score_alineamiento = self.algoritmo.score_alineamiento
                        subtitulo.interpola(instante)

                subtitulo = subtitulo_max_score
                if subtitulo is not None:

                    primera_palabra_subtitulo = self.algoritmo.primer_elemento_subtitulo_alineado
                    ind_primera_pareja = self.algoritmo.alineamiento_subtitulo_S.index(primera_palabra_subtitulo)

                    subtitulo.linea_ASR = proceso_frases.FraseASR(frase_asr)
                    subtitulo.score_alineamiento = self.algoritmo.score_alineamiento
                    subtitulo.algoritmo_usado = self.algoritmo.algoritmo_usado

                    sim = similitud.Similitud(self.algoritmo, subtitulo, frase_asr)
                    star = sim.get_instante_inicial()
                    end = sim.get_instante_final()
                    self.ultima_sincronizacion = star


                    subtitulo.frase_ASR_descartada, linea_asr_asociada = frase_asr.split_palabras(
                        sim.asr_palabra_inicial_alineada,
                        sim.asr_palabra_final_alineada)

                    subtitulo.frase_ASR_descartada.quita_palabra(sim.asr_palabra_inicial_alineada)
                    subtitulo.frase_ASR_no_usada = proceso_frases.FraseASR(frase_asr)
                    subtitulo.frase_ASR_no_usada.quita_palabra(sim.asr_palabra_final_alineada)

                    subtitulo.sincroniza(star, end, linea_asr_asociada, instante)

                    subtitulo.alineamiento_subtitulo = self.algoritmo.alineamiento_subtitulo_S
                    subtitulo.alineamiento_ASR = self.algoritmo.alineamiento_transcripcion_T
                    subtitulo.score_pareja = self.algoritmo.score_pareja


                if sim is not None:
                    self.frases.set_palabra_de_corte_frases(sim.asr_palabra_final_alineada, siguiente=True)


