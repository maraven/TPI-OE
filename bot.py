# ============================================================
# CHATBOT DE TELEGRAM - GESTION DE HORAS EXTRAS
# ============================================================
# Este bot permite a los empleados de una empresa solicitar
# horas extras, ver su historial, cancelar solicitudes,
# y gestionar transporte. Tambien tiene un modo SUPERVISOR
# para aprobar o rechazar solicitudes y cargar nuevas fechas.
#
# Los datos se guardan en archivos CSV.
# ============================================================

# -----------------------------------------------------------
# LIBRERIAS
# -----------------------------------------------------------
import urllib.request
import urllib.parse
import json
import csv
import os
import time

# -----------------------------------------------------------
# CONFIGURACION
# -----------------------------------------------------------
CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_FECHAS = os.path.join(CARPETA_ACTUAL, "fechas_disponibles.csv")
ARCHIVO_HORAS = os.path.join(CARPETA_ACTUAL, "solicitudes_horas.csv")
ARCHIVO_TRANSPORTE = os.path.join(CARPETA_ACTUAL, "solicitudes_transporte.csv")

TOKEN = "8688956089:AAGF1PQsP_EhwOEsqVNY2QNljORK73vQAEU"
URL_API = "https://api.telegram.org/bot" + TOKEN + "/"

# -----------------------------------------------------------
# ESTADOS DE LA CONVERSACION
# -----------------------------------------------------------
ESTADO_INACTIVO = "INACTIVO"
ESTADO_MENU = "MENU"
ESTADO_ELIGIENDO_FECHA = "ELIGIENDO_FECHA"
ESTADO_ELIGIENDO_BAJA = "ELIGIENDO_BAJA"
ESTADO_CONFIRMANDO_BAJA = "CONFIRMANDO_BAJA"
ESTADO_TRANSPORTE_TIPO = "TRANSPORTE_TIPO"
ESTADO_TRANSPORTE_DIRECCION = "TRANSPORTE_DIRECCION"
ESTADO_SUPERVISOR = "SUPERVISOR"
ESTADO_SUPERVISOR_REVISANDO = "SUPERVISOR_REVISANDO"
ESTADO_SUPERVISOR_NUEVA_FECHA = "SUPERVISOR_NUEVA_FECHA"
ESTADO_SUPERVISOR_NUEVA_FECHA_LABEL = "SUPERVISOR_NUEVA_FECHA_LABEL"

# -----------------------------------------------------------
# VARIABLE GLOBAL
# -----------------------------------------------------------
estados_usuario = {}

# ============================================================
# FUNCIONES AUXILIARES (las mas basicas)
# ============================================================

def tiene_numero(texto):
    """Verifica si un texto tiene al menos un digito."""
    for letra in texto:
        if letra.isdigit():
            return True
    return False


def leer_csv(nombre_archivo):
    """Lee un CSV y devuelve una lista de diccionarios."""
    if not os.path.exists(nombre_archivo):
        return []
    archivo = open(nombre_archivo, "r", encoding="utf-8")
    lector = csv.DictReader(archivo)
    datos = list(lector)
    archivo.close()
    return datos


def guardar_csv(nombre_archivo, campos, datos_fila):
    """Agrega una fila al final de un CSV."""
    archivo_existe = os.path.exists(nombre_archivo)
    archivo = open(nombre_archivo, "a", newline="", encoding="utf-8")
    escritor = csv.DictWriter(archivo, fieldnames=campos)
    if not archivo_existe:
        escritor.writeheader()
    escritor.writerow(datos_fila)
    archivo.close()


def borrar_del_csv(nombre_archivo, campo, valor):
    """Borra filas de un CSV donde campo == valor."""
    datos = leer_csv(nombre_archivo)
    if len(datos) == 0:
        return
    columnas = list(datos[0].keys())
    datos_nuevos = []
    for fila in datos:
        if fila[campo] != valor:
            datos_nuevos.append(fila)
    archivo = open(nombre_archivo, "w", newline="", encoding="utf-8")
    escritor = csv.DictWriter(archivo, fieldnames=columnas)
    escritor.writeheader()
    for fila in datos_nuevos:
        escritor.writerow(fila)
    archivo.close()


def proximo_id(archivo, prefijo):
    """Genera un ID autoincremental tipo REC001, TRP002, etc."""
    datos = leer_csv(archivo)
    numero = len(datos) + 1
    return prefijo + str(numero).zfill(3)


def actualizar_estado_csv(id_solicitud, nuevo_estado, nuevo_supervisor):
    """Cambia el estado de una solicitud en solicitudes_horas.csv."""
    datos = leer_csv(ARCHIVO_HORAS)
    for i in range(len(datos)):
        if datos[i]["id"] == id_solicitud:
            datos[i]["estado"] = nuevo_estado
            datos[i]["supervisor"] = nuevo_supervisor
            break
    if len(datos) > 0:
        archivo = open(ARCHIVO_HORAS, "w", newline="", encoding="utf-8")
        escritor = csv.DictWriter(archivo, fieldnames=list(datos[0].keys()))
        escritor.writeheader()
        for fila in datos:
            escritor.writerow(fila)
        archivo.close()


def enviar_mensaje(chat_id, texto):
    """Envia un mensaje a un chat de Telegram."""
    url = URL_API + "sendMessage"
    datos = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    try:
        peticion = urllib.request.Request(url, data=datos)
        respuesta = urllib.request.urlopen(peticion)
        return json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:
        print("Error al enviar mensaje:", error)
        return None

# ============================================================
# FUNCIONES DE MENU
# ============================================================

def mostrar_menu(chat_id):
    """Muestra el menu principal al usuario."""
    estados_usuario[chat_id] = {
        "estado": ESTADO_MENU,
        "datos": {}
    }
    mensaje = (
        "--- GESTION DE HORAS EXTRAS ---\n"
        "Elegi una opcion:\n\n"
        "1. Solicitar Horas Extras\n"
        "2. Ver mi Historial\n"
        "3. Cancelar una solicitud\n"
        "4. Gestionar Transporte\n"
        "5. Salir"
    )
    enviar_mensaje(chat_id, mensaje)


def mostrar_menu_supervisor(chat_id):
    """Muestra el menu del supervisor con las solicitudes pendientes."""
    estados_usuario[chat_id] = {
        "estado": ESTADO_SUPERVISOR,
        "datos": {}
    }

    solicitudes = leer_csv(ARCHIVO_HORAS)

    pendientes = []
    for s in solicitudes:
        if s["supervisor"] == "Pendiente":
            pendientes.append(s)

    mensaje = "--- MODO SUPERVISOR ---\n\n"

    if len(pendientes) == 0:
        mensaje = mensaje + "No hay solicitudes pendientes.\n\n"
    else:
        mensaje = mensaje + "Solicitudes pendientes:\n"
        for i in range(len(pendientes)):
            p = pendientes[i]
            mensaje = mensaje + str(i + 1) + ". " + p["usuario_nombre"] + " - " + p["label_fecha"] + " (" + p["estado"] + ")\n"
        mensaje = mensaje + "\n"

    mensaje = mensaje + "Opciones:\n"
    mensaje = mensaje + "[numero] Revisar una solicitud\n"
    mensaje = mensaje + "A. Agregar nueva fecha disponible\n"
    mensaje = mensaje + "X. Salir del modo supervisor"

    estados_usuario[chat_id]["datos"]["pendientes"] = pendientes
    enviar_mensaje(chat_id, mensaje)

# ============================================================
# FUNCION PRINCIPAL: procesar_mensaje
# ============================================================

def procesar_mensaje(chat_id, nombre, texto):
    """Procesa cada mensaje que llega del usuario segun su estado."""

    texto = texto.strip()
    texto_min = texto.lower()

    # --- INICIO DE CONVERSACION ---
    if texto_min in ["/start", "hola", "menu", "menú", "reiniciar"]:
        enviar_mensaje(chat_id, "¡Hola! Bienvenido al sistema de gestion de horas extras.")
        mostrar_menu(chat_id)
        return

    # --- MODO SUPERVISOR ---
    if texto_min == "supervisor":
        mostrar_menu_supervisor(chat_id)
        return

    # --- INICIALIZAR ESTADO ---
    if chat_id not in estados_usuario:
        estados_usuario[chat_id] = {
            "estado": ESTADO_INACTIVO,
            "datos": {}
        }

    estado = estados_usuario[chat_id]["estado"]
    print("[" + nombre + "] Estado: " + estado + " | Mensaje: " + texto)

    # ============================================================
    # MENU PRINCIPAL
    # ============================================================
    if estado == ESTADO_MENU:

        if texto == "1":
            fechas = leer_csv(ARCHIVO_FECHAS)
            if len(fechas) == 0:
                enviar_mensaje(chat_id, "No hay horas extras disponibles en este momento. Pedile al supervisor que cargue fechas nuevas (escribiendo 'supervisor' y eligiendo opcion A).")
                mostrar_menu(chat_id)
            else:
                mensaje = "Fechas disponibles:\n\n"
                for i in range(len(fechas)):
                    mensaje = mensaje + str(i + 1) + ". " + fechas[i]["label"] + "\n"
                mensaje = mensaje + "\nEscribi el numero de la fecha que queres:"
                estados_usuario[chat_id]["datos"]["fechas"] = fechas
                estados_usuario[chat_id]["estado"] = ESTADO_ELIGIENDO_FECHA
                enviar_mensaje(chat_id, mensaje)

        elif texto == "2":
            solicitudes = leer_csv(ARCHIVO_HORAS)
            mis_solicitudes = []
            for s in solicitudes:
                if s["usuario_id"] == str(chat_id):
                    mis_solicitudes.append(s)
            if len(mis_solicitudes) == 0:
                enviar_mensaje(chat_id, "No tenes solicitudes registradas.")
            else:
                mensaje = "Mi Historial:\n\n"
                for s in mis_solicitudes:
                    mensaje = mensaje + "- " + s["label_fecha"] + " | " + s["horas"] + "hs | " + s["estado"] + " | Supervisor: " + s["supervisor"] + "\n"
                enviar_mensaje(chat_id, mensaje)
            mostrar_menu(chat_id)

        elif texto == "3":
            solicitudes = leer_csv(ARCHIVO_HORAS)
            activas = []
            for s in solicitudes:
                if s["usuario_id"] == str(chat_id):
                    if s["estado"] != "Rechazada" and s["estado"] != "Baja Aprobada":
                        activas.append(s)
            if len(activas) == 0:
                enviar_mensaje(chat_id, "No tenes solicitudes activas para cancelar.")
                mostrar_menu(chat_id)
            else:
                mensaje = "Seleccione la solicitud que quiere cancelar:\n\n"
                for i in range(len(activas)):
                    mensaje = mensaje + str(i + 1) + ". " + activas[i]["label_fecha"] + " (" + activas[i]["estado"] + ")\n"
                estados_usuario[chat_id]["datos"]["activas"] = activas
                estados_usuario[chat_id]["estado"] = ESTADO_ELIGIENDO_BAJA
                enviar_mensaje(chat_id, mensaje)

        elif texto == "4":
            solicitudes = leer_csv(ARCHIVO_HORAS)
            tiene_horas = False
            for s in solicitudes:
                if s["usuario_id"] == str(chat_id):
                    tiene_horas = True
                    break
            if not tiene_horas:
                enviar_mensaje(chat_id, "No tenes horas extras solicitadas. Primero tenes que pedir horas extras (opcion 1) para poder gestionar el transporte.")
                mostrar_menu(chat_id)
            else:
                mensaje = "GESTION DE TRANSPORTE\n\n1. Solicitar movilidad de la empresa\n2. Voy en movilidad propia"
                estados_usuario[chat_id]["estado"] = ESTADO_TRANSPORTE_TIPO
                enviar_mensaje(chat_id, mensaje)

        elif texto == "5":
            enviar_mensaje(chat_id, "Gracias por usar el sistema. ¡Hasta luego!")
            estados_usuario[chat_id]["estado"] = ESTADO_INACTIVO

        else:
            enviar_mensaje(chat_id, "Opcion invalida. Escribi 1, 2, 3, 4 o 5.")
            mostrar_menu(chat_id)

    # ============================================================
    # ELIGIENDO FECHA (opcion 1)
    # ============================================================
    elif estado == ESTADO_ELIGIENDO_FECHA:

        fechas = estados_usuario[chat_id]["datos"].get("fechas", [])

        try:
            opcion = int(texto)

            if opcion >= 1 and opcion <= len(fechas):

                fecha_elegida = fechas[opcion - 1]
                etiqueta = fecha_elegida["label"]

                horas = 4
                if "Domingo" in etiqueta:
                    horas = 6
                elif "Miercoles" in etiqueta or "Miércoles" in etiqueta:
                    horas = 2

                id_solicitud = proximo_id(ARCHIVO_HORAS, "REC")

                guardar_csv(ARCHIVO_HORAS,
                    ["id", "usuario_id", "usuario_nombre", "fecha", "label_fecha", "horas", "estado", "supervisor"],
                    {
                        "id": id_solicitud,
                        "usuario_id": str(chat_id),
                        "usuario_nombre": nombre,
                        "fecha": fecha_elegida["fecha"],
                        "label_fecha": etiqueta,
                        "horas": str(horas),
                        "estado": "Solicitada",
                        "supervisor": "Pendiente"
                    }
                )

                borrar_del_csv(ARCHIVO_FECHAS, "id", fecha_elegida["id"])

                enviar_mensaje(chat_id, "¡Solicitud registrada con exito!\n\nFecha: " + etiqueta + "\nHoras: " + str(horas) + "hs\nEstado: Solicitada (pendiente de aprobacion del supervisor)")
                mostrar_menu(chat_id)

            else:
                enviar_mensaje(chat_id, "Numero invalido. Elegi un numero de la lista.")
                mensaje = "Fechas disponibles:\n\n"
                for i in range(len(fechas)):
                    mensaje = mensaje + str(i + 1) + ". " + fechas[i]["label"] + "\n"
                mensaje = mensaje + "\nEscribi el numero de la fecha que queres:"
                enviar_mensaje(chat_id, mensaje)

        except ValueError:
            enviar_mensaje(chat_id, "Por favor escribi SOLO el numero (ej: 1, 2, 3...)")

    # ============================================================
    # ELIGIENDO BAJA (opcion 3 - paso 1)
    # ============================================================
    elif estado == ESTADO_ELIGIENDO_BAJA:

        activas = estados_usuario[chat_id]["datos"].get("activas", [])

        try:
            opcion = int(texto)
            if opcion >= 1 and opcion <= len(activas):
                solicitud = activas[opcion - 1]
                estados_usuario[chat_id]["datos"]["cancelar"] = solicitud
                estados_usuario[chat_id]["estado"] = ESTADO_CONFIRMANDO_BAJA
                enviar_mensaje(chat_id, "¿Estas seguro que queres cancelar " + solicitud["label_fecha"] + "?\n\n1. Si\n2. No")
            else:
                enviar_mensaje(chat_id, "Numero invalido.")
        except ValueError:
            enviar_mensaje(chat_id, "Escribi un numero valido.")

    # ============================================================
    # CONFIRMANDO BAJA (opcion 3 - paso 2)
    # ============================================================
    elif estado == ESTADO_CONFIRMANDO_BAJA:

        if texto == "1":
            solicitud = estados_usuario[chat_id]["datos"]["cancelar"]
            id_baja = proximo_id(ARCHIVO_HORAS, "REC")
            guardar_csv(ARCHIVO_HORAS,
                ["id", "usuario_id", "usuario_nombre", "fecha", "label_fecha", "horas", "estado", "supervisor"],
                {
                    "id": id_baja,
                    "usuario_id": str(chat_id),
                    "usuario_nombre": nombre,
                    "fecha": solicitud["fecha"],
                    "label_fecha": solicitud["label_fecha"],
                    "horas": solicitud["horas"],
                    "estado": "Baja Solicitada",
                    "supervisor": "Pendiente"
                }
            )
            enviar_mensaje(chat_id, "Solicitud de baja registrada. Queda pendiente de aprobacion del supervisor.")
            mostrar_menu(chat_id)
        elif texto == "2":
            enviar_mensaje(chat_id, "Cancelacion descartada.")
            mostrar_menu(chat_id)
        else:
            enviar_mensaje(chat_id, "Escribi 1 para confirmar o 2 para cancelar.")

    # ============================================================
    # TRANSPORTE TIPO (opcion 4 - paso 1)
    # ============================================================
    elif estado == ESTADO_TRANSPORTE_TIPO:

        if texto == "1":
            estados_usuario[chat_id]["estado"] = ESTADO_TRANSPORTE_DIRECCION
            enviar_mensaje(chat_id, "Ingresa tu direccion de domicilio (ej: Av. Corrientes 1234):")
        elif texto == "2":
            id_transporte = proximo_id(ARCHIVO_TRANSPORTE, "TRP")
            guardar_csv(ARCHIVO_TRANSPORTE,
                ["id", "usuario_id", "usuario_nombre", "fecha", "tipo", "direccion", "timestamp"],
                {
                    "id": id_transporte,
                    "usuario_id": str(chat_id),
                    "usuario_nombre": nombre,
                    "fecha": time.strftime("%Y-%m-%d"),
                    "tipo": "Movilidad propia",
                    "direccion": "N/A",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
            enviar_mensaje(chat_id, "Se registro que vas en movilidad propia.")
            mostrar_menu(chat_id)
        else:
            enviar_mensaje(chat_id, "Opcion invalida. Escribi 1 o 2.")

    # ============================================================
    # TRANSPORTE DIRECCION (opcion 4 - paso 2)
    # ============================================================
    elif estado == ESTADO_TRANSPORTE_DIRECCION:

        if len(texto) < 5:
            enviar_mensaje(chat_id, "La direccion es muy corta. Ingresa una direccion valida (ej: Av. Corrientes 1234):")
        elif not tiene_numero(texto):
            enviar_mensaje(chat_id, "La direccion debe tener un numero de altura. Ingresala de nuevo (ej: Av. Corrientes 1234):")
        else:
            id_transporte = proximo_id(ARCHIVO_TRANSPORTE, "TRP")
            guardar_csv(ARCHIVO_TRANSPORTE,
                ["id", "usuario_id", "usuario_nombre", "fecha", "tipo", "direccion", "timestamp"],
                {
                    "id": id_transporte,
                    "usuario_id": str(chat_id),
                    "usuario_nombre": nombre,
                    "fecha": time.strftime("%Y-%m-%d"),
                    "tipo": "Solicitar movilidad",
                    "direccion": texto,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
            enviar_mensaje(chat_id, "Solicitud de movilidad registrada con exito.")
            mostrar_menu(chat_id)

    # ============================================================
    # SUPERVISOR
    # ============================================================
    elif estado == ESTADO_SUPERVISOR:

        if texto.upper() == "A":
            estados_usuario[chat_id]["estado"] = ESTADO_SUPERVISOR_NUEVA_FECHA
            enviar_mensaje(chat_id, "Ingresa la fecha en formato AAAA-MM-DD (ej: 2026-07-15):")
            return

        if texto.upper() == "X":
            enviar_mensaje(chat_id, "Saliendo del modo supervisor.")
            mostrar_menu(chat_id)
            return

        pendientes = estados_usuario[chat_id]["datos"].get("pendientes", [])
        try:
            opcion = int(texto)
            if opcion >= 1 and opcion <= len(pendientes):
                solicitud = pendientes[opcion - 1]
                estados_usuario[chat_id]["datos"]["revisando"] = solicitud
                estados_usuario[chat_id]["estado"] = ESTADO_SUPERVISOR_REVISANDO
                mensaje = "Revisando solicitud:\n\n"
                mensaje = mensaje + "Empleado: " + solicitud["usuario_nombre"] + "\n"
                mensaje = mensaje + "Fecha: " + solicitud["label_fecha"] + "\n"
                mensaje = mensaje + "Estado: " + solicitud["estado"] + "\n\n"
                mensaje = mensaje + "1. Aprobar\n2. Rechazar\n3. Volver"
                enviar_mensaje(chat_id, mensaje)
            else:
                enviar_mensaje(chat_id, "Numero invalido. Escribi un numero, A para agregar fecha, o X para salir.")
        except ValueError:
            enviar_mensaje(chat_id, "Escribi un numero, A para agregar fecha, o X para salir.")

    # ============================================================
    # SUPERVISOR REVISANDO
    # ============================================================
    elif estado == ESTADO_SUPERVISOR_REVISANDO:

        solicitud = estados_usuario[chat_id]["datos"]["revisando"]

        if texto == "1":
            if solicitud["estado"] == "Baja Solicitada":
                actualizar_estado_csv(solicitud["id"], "Baja Aprobada", "Aprobado")
            else:
                actualizar_estado_csv(solicitud["id"], "Aprobada", "Aprobado")
            enviar_mensaje(chat_id, "Solicitud APROBADA.")
            mostrar_menu_supervisor(chat_id)

        elif texto == "2":
            if solicitud["estado"] == "Baja Solicitada":
                actualizar_estado_csv(solicitud["id"], "Baja Rechazada", "Rechazado")
            else:
                actualizar_estado_csv(solicitud["id"], "Rechazada", "Rechazado")
            enviar_mensaje(chat_id, "Solicitud RECHAZADA.")
            mostrar_menu_supervisor(chat_id)

        elif texto == "3":
            mostrar_menu_supervisor(chat_id)
        else:
            enviar_mensaje(chat_id, "Escribi 1, 2 o 3.")

    # ============================================================
    # SUPERVISOR NUEVA FECHA
    # ============================================================
    elif estado == ESTADO_SUPERVISOR_NUEVA_FECHA:

        if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
            enviar_mensaje(chat_id, "Formato incorrecto. Ingresa la fecha como AAAA-MM-DD (ej: 2026-07-15):")
            return

        try:
            anio = int(texto[0:4])
            mes = int(texto[5:7])
            dia = int(texto[8:10])
        except:
            enviar_mensaje(chat_id, "Fecha invalida. Ingresa la fecha como AAAA-MM-DD (ej: 2026-07-15):")
            return

        estados_usuario[chat_id]["datos"]["nueva_fecha"] = texto
        estados_usuario[chat_id]["estado"] = ESTADO_SUPERVISOR_NUEVA_FECHA_LABEL
        enviar_mensaje(chat_id, "Ingresa una descripcion para la fecha (ej: Sabado 15/07):")

    # ============================================================
    # SUPERVISOR NUEVA FECHA LABEL
    # ============================================================
    elif estado == ESTADO_SUPERVISOR_NUEVA_FECHA_LABEL:

        fecha = estados_usuario[chat_id]["datos"]["nueva_fecha"]
        label = texto
        id_fecha = proximo_id(ARCHIVO_FECHAS, "DT")

        guardar_csv(ARCHIVO_FECHAS,
            ["id", "fecha", "label"],
            {
                "id": id_fecha,
                "fecha": fecha,
                "label": label
            }
        )

        enviar_mensaje(chat_id, "Fecha agregada con exito: " + label + " (" + fecha + ")")
        mostrar_menu_supervisor(chat_id)

    # ============================================================
    # INACTIVO
    # ============================================================
    elif estado == ESTADO_INACTIVO:
        enviar_mensaje(chat_id, "Escribi 'hola' o 'menu' para empezar.")

# ============================================================
# FUNCION PRINCIPAL DEL BOT
# ============================================================

def iniciar_polling():
    """Bucle infinito que pregunta a Telegram si hay mensajes nuevos."""

    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("ERROR: Configura tu TOKEN en bot.py primero.")
        return

    print("Carpeta del proyecto: " + CARPETA_ACTUAL)
    print("Archivo de fechas: " + ARCHIVO_FECHAS)
    print("Archivo de horas: " + ARCHIVO_HORAS)
    print("Archivo de transporte: " + ARCHIVO_TRANSPORTE)

    fechas = leer_csv(ARCHIVO_FECHAS)
    print("Fechas disponibles cargadas: " + str(len(fechas)))

    print("\nBot de Telegram iniciado. Esperando mensajes...")

    ultimo_id = 0

    while True:
        url = URL_API + "getUpdates?offset=" + str(ultimo_id + 1) + "&timeout=30"
        try:
            peticion = urllib.request.Request(url)
            respuesta = urllib.request.urlopen(peticion)
            datos = json.loads(respuesta.read().decode("utf-8"))

            if datos.get("ok") and datos.get("result"):
                for update in datos["result"]:
                    ultimo_id = update["update_id"]
                    mensaje = update.get("message")
                    if mensaje and "text" in mensaje:
                        chat_id = mensaje["chat"]["id"]
                        nombre = mensaje["from"].get("first_name", "Usuario")
                        texto = mensaje["text"]
                        print("Mensaje de " + nombre + ": " + texto)
                        procesar_mensaje(chat_id, nombre, texto)

        except Exception as error:
            print("Error:", error)
            time.sleep(5)

        time.sleep(0.5)

# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    iniciar_polling()
