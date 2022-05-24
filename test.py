import gestor_prueba

def main(fichero_configuracion):
    gst_prueba = gestor_prueba.GestorPrueba(fichero_configuracion)
    for prueba in gst_prueba.get_pruebas():
        prueba.inicia_transcripcion()
        prueba.fin_transcripcion()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test manager')
    parser.add_argument("config_file",
                        help="test configuration json file")

    args = parser.parse_args()


    main(args.config_file)

