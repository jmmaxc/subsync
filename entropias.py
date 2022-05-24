class Entropia():

    palabras_importantes = {'se',
                            'ha',
                            'he',
                            'si',
                            'es',
                            'va',
                            'ir'}
    def __init__(self, largo_palabra = -1):
        self.largo_palabra = largo_palabra

    def get_configuracion(self):
        retorno = [["Entropia", self.__class__.__name__],
                   ["Longitud minima", self.largo_palabra],
                   ]
        return retorno

    def get_parametros(self):
        lista = [["Lng minima palabras",self.largo_palabra],]
        return lista

    def pasa_filtro(self, lista_palabras):
        palabras_filtradas = []
        for palabra in lista_palabras:
            if self._imp_pasa_filtro(palabra):
                palabras_filtradas.append(palabra)
        return palabras_filtradas

    def numero_palabras(self,lista_palabras):
        return len(self.pasa_filtro(lista_palabras))

    def _imp_pasa_filtro(self, palabra):
        if self.largo_palabra is not -1:
            if len(palabra) > self.largo_palabra:
                return True
            else:

                try:
                    p_str = palabra.palabra_str.lower()
                except AttributeError:
                    p_str = palabra.lower()
                if p_str in Entropia.palabras_importantes:
                    return True
                else:
                    return False

        return True


