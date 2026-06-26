# Chatbot Telegram - Gestión de Horas Extras (TPI Organización Empresarial)

**Trabajo Práctico Integrador** de la materia *Organización Empresarial* - Tecnicatura Universitaria en Programación (UTN).

Chatbot funcional en Telegram que automatiza la gestión de horas extras y transporte del personal. Desarrollado en Python con persistencia en archivos CSV.

---

## Modelado BPMN 2.0

El proceso de negocio está modelado en BPMN 2.0 con tres carriles:

- **Empleado**: solicita horas extras, consulta historial, cancela solicitudes y gestiona transporte
- **Chatbot/Sistema**: valida fechas disponibles, registra solicitudes, consulta base de datos
- **Supervisor**: revisa, aprueba o rechaza solicitudes y carga nuevas fechas disponibles

### Compuertas Lógicas (Gateways)

1. ¿Hay fechas disponibles? - Valida existencia de fechas en `fechas_disponibles.csv`
2. ¿Existen registros? - Verifica historial del empleado
3. ¿Tiene solicitudes activas? - Controla si hay solicitudes para cancelar
4. ¿Opción de fecha válida? - Valida selección numérica del empleado
5. ¿Solicita movilidad? - Bifurca transporte entre movilidad propia o de la empresa
6. ¿Dirección válida? - Valida formato de domicilio (mínimo 5 caracteres + número)

---

## Archivos del Proyecto

| Archivo | Descripción |
|---|---|
| `bot.py` | Código principal del chatbot de Telegram |
| `fechas_disponibles.csv` | Fechas programadas para realizar horas extras |
| `solicitudes_horas.csv` | Solicitudes de horas extras y estado de aprobación |
| `solicitudes_transporte.csv` | Solicitudes de transporte y movilidad |
| `Diagrama-BPMN` | Diagrama de procesos BPMN 2.0 |
| `BPMN.drawio` | Archivo editable del diagrama BPMN (draw.io) |
| `Informe.pdf` | Informe formal de entrega |
---

## Cómo usar

### 1. Crear el bot en Telegram

1. Buscá `@BotFather` en Telegram
2. Enviá `/newbot` y seguí las instrucciones
3. **Copiá el token** que te da

### 2. Configurar el token

En `bot.py` reemplazá:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
```

por tu token.

### 3. Ejecutar

```bash
python bot.py
```

### 4. Probar

Enviá `hola` o `/start` a tu bot en Telegram.

---

## Funcionalidades

### Menú Empleado

| Opción | Descripción |
|---|---|
| **1** - Solicitar Horas Extras | Muestra fechas disponibles, elegís una y se registra la solicitud |
| **2** - Ver mi Historial | Lista todas tus solicitudes con su estado |
| **3** - Cancelar solicitud | Da de baja una solicitud activa |
| **4** - Gestionar Transporte | Solicitás movilidad de la empresa o registrás movilidad propia |
| **5** - Salir | Finaliza la conversación |

### Menú Supervisor

Escribí `supervisor` en el chat para acceder:

| Opción | Descripción |
|---|---|
| **[número]** | Revisar y aprobar/rechazar una solicitud pendiente |
| **A** | Agregar nuevas fechas disponibles al sistema |
| **X** | Salir del modo supervisor |

---

## Máquina de Estados

El bot implementa una máquina de estados finita (FSM) para recordar en qué paso de la conversación está cada usuario:

- `INACTIVO` - Esperando saludo inicial
- `MENU` - Mostrando opciones principales
- `ELIGIENDO_FECHA` - Seleccionando fecha para horas extras
- `ELIGIENDO_BAJA` / `CONFIRMANDO_BAJA` - Proceso de cancelación
- `TRANSPORTE_TIPO` / `TRANSPORTE_DIRECCION` - Gestión de transporte
- `SUPERVISOR` / `SUPERVISOR_REVISANDO` - Aprobación de solicitudes
- `SUPERVISOR_NUEVA_FECHA` / `SUPERVISOR_NUEVA_FECHA_LABEL` - Carga de fechas

---

## Pruebas de Robustez (Camino Infeliz)

El bot maneja los siguientes errores de entrada del usuario:

- **Opción inválida en menú**: respuesta con mensaje de error y reenvío del menú
- **Texto en lugar de número**: captura `ValueError` y pide el formato correcto
- **Dirección sin número**: valida presencia de dígitos en el domicilio
- **Dirección demasiado corta**: mínimo 5 caracteres
- **Formato de fecha incorrecto**: validación AAAA-MM-DD en carga de fechas
- **Sin fechas disponibles**: mensaje claro y sugerencia de contactar al supervisor
- **Sin solicitudes activas**: no permite cancelar ni gestionar transporte sin horas previas

---

## Diccionario de Datos

### fechas_disponibles.csv

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| id | String | ID único de la fecha | DT001 |
| fecha | String | Fecha en formato AAAA-MM-DD | 2026-07-04 |
| label | String | Descripción para mostrar al usuario | Sábado 04/07 |

### solicitudes_horas.csv

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| id | String | ID único de solicitud | REC001 |
| usuario_id | String | ID de chat de Telegram | 123456789 |
| usuario_nombre | String | Nombre del empleado | Mariano Avendaño |
| fecha | String | Fecha solicitada | 2026-07-04 |
| label_fecha | String | Descripción de la fecha | Sábado 04/07 |
| horas | String | Cantidad de horas | 4 |
| estado | String | Estado de la solicitud | Solicitada / Aprobada / Rechazada / Baja Solicitada |
| supervisor | String | Estado de revisión del supervisor | Pendiente / Aprobado / Rechazado |

### solicitudes_transporte.csv

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| id | String | ID único de vale | TRP001 |
| usuario_id | String | ID de chat de Telegram | 123456789 |
| usuario_nombre | String | Nombre del empleado | Mariano Avendaño |
| fecha | String | Fecha del servicio | 2026-06-25 |
| tipo | String | Tipo de traslado | Movilidad propia / Solicitar movilidad |
| direccion | String | Dirección de destino | Av. Corrientes 1234 |
| timestamp | String | Fecha y hora del registro | 2026-06-25T20:30:00Z |

---

## Herramientas de IA Utilizadas

Este proyecto fue desarrollado con asistencia de **OpenCode (agente de coding autónomo)** como herramienta de IA para:

- Corrección del código Python del bot
- Reformateo y simplificación del código
- Generación de la documentación (README, informe Word)
- Corrección de errores (CSV corruption, rutas relativas, método `padStart`)

Los prompts aplicados incluyeron:
- "Corregí el error padStart por zfill"
- "Las fechas deben borrarse del listado al ser seleccionadas"
- "Agregá funciones al supervisor para cargar nuevas fechas"

---

