import entropias
import alineamientos




class Calculo:
    def __init__(self):
        pass

    def get(self, palabra1, palabra2):
        raise NotImplemented("Clase abstracta")

    def get_configuracion(self):
        raise NotImplemented("Clase abstracta")



class Distancia(Calculo):
    def __init__(self,tolerancia_desigualdad = 0.0,tolerancia_igualdad=None):
        super().__init__()

        self.tolerancia_desigualdad=tolerancia_desigualdad
        if tolerancia_igualdad is None:
            self.tolerancia_igualdad=1-tolerancia_desigualdad
        else:
            self.tolerancia_igualdad = tolerancia_igualdad


    def get_configuracion(self):
        lista = [
            ["Distancia", self.__class__.__name__],
            ["Tolerancia desigualdad", self.tolerancia_desigualdad],
            ["Tolerancia igualdad", self.tolerancia_igualdad],

        ]
        return lista

    def get_parametros(self):
        lista =  [
            ["Tolerancia desigualdad", self.tolerancia_desigualdad],
            ["Tolerancia igualdad", self.tolerancia_igualdad],
        ]

        return lista

    def get(self, palabra1, palabra2):

        try:
            p1 = palabra1.palabra_str.upper()
            p2 = palabra2.palabra_str.upper()
        except AttributeError:
            p1 = palabra1.upper()
            p2 = palabra2.upper()
        if p1 == p2:
            return 0
        else:
            return 1

    def score(self, palabra1, palabra2):

        if palabra1 is None or palabra2 is None:
            retorno = 0
        else:
            retorno = (1 - self.get(palabra1, palabra2)) * len(palabra1)
        return retorno


class DistanciaPalabras(Distancia):

    def __init__(self, tolerancia_desigualdad,tolerancia_igualdad=None):




        super().__init__(tolerancia_desigualdad,tolerancia_igualdad)


        self.entropia = entropias.Entropia()
        self.distancia = Distancia() #Esta funcion puede recibir palabras o puede recibir cadenas
        self.algoritmo_iguales = alineamientos.AlineamientoLiterales(self.distancia,
                                                                     self.entropia)



    def get_parametros(self):
        lista = super().get_parametros()  + self.entropia.get_parametros()

        return lista


    def get(self, palabra1, palabra2):

        try:
            p1 = palabra1.palabra_str.upper()
            p2 = palabra2.palabra_str.upper()
        except AttributeError:
            p1 = palabra1.upper()
            p2 = palabra2.upper()

        maxima_longitud = max([len(p1), len(p2)])
        minima_longitud = min([len(p1), len(p2)])

        if p1 == p2:
            distancia = 0
        elif self.tolerancia_desigualdad == 0.0 or minima_longitud <= 2:

            distancia = 1
        else:

            self.algoritmo_iguales.calcula_similitud(p1, p2)

            iguales = self.algoritmo_iguales.get_numero_secuencia_mas_larga()
            p_igualdad = iguales / maxima_longitud
            distancia = 1 - p_igualdad
            if distancia >= self.tolerancia_desigualdad:
                distancia = 1
            elif distancia <= self.tolerancia_igualdad:
                distancia = 0

        return distancia


class DistanciaPalabrasLV(Distancia):

    def __init__(self,  tolerancia_desigualdad,tolerancia_igualdad=None):


        super().__init__(tolerancia_desigualdad,tolerancia_igualdad)


        self.entropia = entropias.Entropia()
        self.distancia = Distancia()
        self.algoritmo_iguales = alineamientos.AlineamientoLV(self.distancia,
                                                              self.entropia)





    def get_parametros(self):
        lista = super().get_parametros() + self.entropia.get_parametros()
        return lista


    def get(self, palabra1, palabra2):

        try:
            p1 = palabra1.palabra_str.upper()
            p2 = palabra2.palabra_str.upper()
        except AttributeError:
            p1=palabra1.upper()
            p2=palabra2.upper()
        maxima_longitud = max([len(p1), len(p2)])
        minima_longitud = min([len(p1), len(p2)])

        if p1 == p2:
            distancia = 0
        elif self.tolerancia_desigualdad == 0.0 or minima_longitud <= 3:

            distancia = 1
        else:

            self.algoritmo_iguales.calcula_similitud(p1, p2,False)
            distancia = abs(self.algoritmo_iguales.coste/maxima_longitud)
            if distancia >= self.tolerancia_desigualdad:
                distancia = 1
            elif distancia <= self.tolerancia_igualdad:
                distancia = 0


        return distancia


DISTANCIAS = {'DEFECTO': DistanciaPalabrasLV.__name__,
              'LT': DistanciaPalabras.__name__,
              'DT': Distancia.__name__,
              'LV': DistanciaPalabrasLV.__name__}
