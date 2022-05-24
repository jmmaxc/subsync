import math


class Interpolacion():
    def __init__(self):
        self.n = 0
        self.acumulado_x = 0
        self.acumulado_y = 0
        self.producto = 0
        self.acumulado_x_2 = 0
        self.acumulado_y_2 = 0

    def incorpora(self, x, y):
        self.n += 1
        self.acumulado_x += x
        self.acumulado_y += y
        self.producto += x * y
        self.acumulado_x_2 += x * x
        self.acumulado_y_2 += y * y

    def get_ajuste(self, forzar_cero=False):
        if self.n is 0:
            return 0, 0, 0, 0

        media = self.acumulado_x / self.n

        if forzar_cero:
            n = 0
            m = self.producto / self.acumulado_x_2
            r = 0
        else:
            dx = self.n * self.acumulado_x_2 - self.acumulado_x * self.acumulado_x
            dy = self.n * self.acumulado_y_2 - self.acumulado_y * self.acumulado_y

            m = (self.n * self.producto - self.acumulado_x * self.acumulado_y) / dx
            n = (self.acumulado_y * self.acumulado_x_2 - self.acumulado_x - self.producto) / dx
            r = abs((self.n * self.producto - self.acumulado_y * self.acumulado_x) / \
                    math.sqrt(dx * dy))

        return m, n, r, media
