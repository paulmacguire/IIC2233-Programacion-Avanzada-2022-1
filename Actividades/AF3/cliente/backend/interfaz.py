"""
Ventana principal del cliente que se encarga de funcionar como backend de la
mayoria de ventanas, de conectar señales y de procesar los mensajes recibidos
por el cliente
"""
from PyQt5.QtCore import pyqtSignal, QObject

from frontend.ventana_carga import VentanaCarga
from frontend.ventana_login import VentanaLogin
from frontend.ventana_principal import VentanaPrincipal
from utils import guardar_archivo


class Interfaz(QObject):
    # senal_mostrar_ventana_carga = pyqtSignal()
    senal_preparar_ventana_principal = pyqtSignal(str, list, list, list)
    senal_abrir_ventana_principal = pyqtSignal()
    senal_login_rechazado = pyqtSignal()
    senal_tocar_musica = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.ventana_carga = VentanaCarga()
        self.ventana_login = VentanaLogin()
        self.ventana_principal = VentanaPrincipal()
        # -----------------------------------------
        self.descarga_actual = bytearray()

        #  ==========> CONEXIONES <==========

        # Señales ventana de carga
        self.ventana_carga.senal_enviar_inicio.connect(
                                        self.ventana_login.mostrar)

        # Señales ventana de login
        self.ventana_login.senal_enviar_login.connect(parent.enviar)

        # Señales ventana principal
        self.ventana_principal.senal_descargar_musica.connect(parent.enviar)

        # Señales interfaz
        self.senal_preparar_ventana_principal.connect(
            self.ventana_principal.preparar_ventana
        )
        self.senal_abrir_ventana_principal.connect(self.abrir_ventana_principal)
        self.senal_login_rechazado.connect(self.ventana_login.mostrar_error)
        self.senal_tocar_musica.connect(self.ventana_principal.tocar_musica)

    def mostrar_ventana_carga(self):
        self.ventana_carga.mostrar()

    def abrir_ventana_principal(self):
        self.ventana_login.ocultar()
        self.ventana_principal.mostrar()

    def manejar_mensaje(self, mensaje: dict):
        """
        Maneja un mensaje recibido desde el servidor.
        """
        try:
            comando = mensaje["comando"]
        except KeyError:
            return {}

        if comando == "respuesta_validacion_login":
            if mensaje["estado"] == "aceptado":
                nombre_usuario = mensaje["nombre_usuario"]
                canciones = mensaje["canciones"].split(",")
                rutas_caratulas = mensaje["rutas_caratulas"].split(",")
                usuarios = mensaje["usuarios"].split(",")
                self.senal_preparar_ventana_principal.emit(
                    nombre_usuario, canciones, rutas_caratulas, usuarios
                )
                self.senal_abrir_ventana_principal.emit()
            else:
                self.senal_login_rechazado.emit()

        elif comando == "respuesta_descarga_multimedia":
            self.ruta_musica = mensaje["ruta"]
            print("Archivo recibido con éxito", mensaje["ruta"])
            self.senal_tocar_musica.emit(self.ruta_musica)

        elif comando == "chunk":
            parametros = mensaje["argumentos"]
            chunk, largo = parametros["contenido"], parametros.get("largo", 0)
            chunk = bytes.fromhex(chunk)
            chunk = chunk[:largo]  # eliminamos el padding
            self.descarga_actual.extend(chunk)
            if largo < 8000:
                # El ultimo chunk será menor a 8000
                guardar_archivo(self.descarga_actual, mensaje["ruta"])
                self.descarga_actual = bytearray()
