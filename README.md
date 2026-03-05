# Generador de Recibos de Sueldo (Uruguay)

Este proyecto es una herramienta simple en Python para generar recibos de sueldo en formato PDF, adaptados al formato estándar de Uruguay (con copias original y duplicado en una misma hoja).

## Requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Recomendado para la gestión de dependencias)

## Instalación

1.  Clona el repositorio.
2.  Instala las dependencias usando `uv`:

    ```bash
    uv sync
    ```

    O si prefieres usar pip directamente (asegúrate de tener `reportlab` y `pyyaml` instalados):

    ```bash
    pip install reportlab pyyaml
    ```

## Uso

1.  **Configuración de Datos**:
    Edita el archivo `config/{month}.yaml` (ej. month = 2026-01) con la información del empleador, empleado y los detalles de la liquidación.


    Ejemplo de estructura:
    ```yaml
    # 2026-01.yaml
    empleador: "NOMBRE EMPLEADOR"
    direccion: "DIRECCIÓN"
    grupo: "21"
    bps: "0000000"
    rut: "000000000000"
    empleado: "APELLIDO, NOMBRE"
    ci: "0000000-0"
    fecha_ingreso: "dd/mm/aa"
    institucion: "NOMBRE BANCO"
    cuenta: "0000000"
    tipo_pago: "MENSUAL"
    lugar_pago: "MONTEVIDEO"
    forma_pago: "Transferencia Bancaria"
    ### Editar todos los meses a partir de acá
    periodo: "Enero 2026"
    fecha_pago: "5 de febrero de 2026"
    ingresos:
      "Sueldo Básico": 10000.00
      "Salario Vacacional": 3000.00
    ingresos_no_deducibles:
      - "Salario Vacacional"
    descuentos: # porcentajes
      "Fondo Social SD": 0.00
      "Aporte jubilatorio": 15.00
      "Seguro de enfermedad": 3.00
      "FRL": 0.10
    transporte: 510
    ```

2.  **Generar el Recibo**:
    Ejecuta el script principal:

    ```bash
    uv run main.py
    ```

    O con python directo:
    ```bash
    python main.py
    ```

3.  **Resultado**:
    El script generará un archivo PDF (por defecto `receipts/{month}.pdf`, configurable en el script) en el directorio raíz.
