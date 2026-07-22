# Plan de Extracción y Poblado de Base de Datos (Endpoints ETL)

## 1. Arquitectura de Endpoints
Se crearán dos endpoints dedicados bajo un router específico (ej. `routers/etl.py`) para poder probarlos mediante Swagger UI. Ambos implementarán el patrón **Dry-Run** para evitar sobrescritura accidental de datos.

* `POST /api/etl/poblar_unidades_administrativas`
* `POST /api/etl/poblar_matriz_programatica`

**Parámetros requeridos en ambos:**
* `file` (UploadFile): El documento Excel.
* `ejercicio_id` (int): Para vincular la carga al año fiscal correcto.
* `confirmar_actualizacion` (bool): Default `False`. Controla si se guarda o solo se evalúa.

---

## 2. Motor de Diferencias (El "Diff Engine")
Antes de hacer cualquier inserción, el sistema debe cargar la información actual de la base de datos en memoria (diccionarios de Python) para comparar rápidamente con el Excel.

* **Identificadores Únicos (Claves):**
    * Unidades: `CatalogoUnidadesAdministrativas.clave` (columna "Número").
    * Programas: `CatalogoProgramas.clave` + `ejercicio_id`.
    * Componentes: `Componentes.clave` + `programa_id`.
    * Actividades: `Actividades.clave` + `componente_id`.
    * Metas mensuales: `ProgramacionMeta.actividad_id` + `mes`.
    * PMD: `CatalogoPMD.clave` y relación por (`actividad_id`, `pmd_id`).

* **Lógica de Evaluación por Fila:**
    1. ¿La clave existe en BD?
       * **NO:** Añadir al arreglo `nuevos_registros`.
       * **SÍ:** Comparar campos (Plazas, Nombre, Monto).
          * ¿Hay cambios? -> Añadir al arreglo `registros_a_modificar` (guardando valor viejo y nuevo).
          * ¿Son idénticos? -> Ignorar (Omitir).

---

## 3. Flujo del Endpoint 1: Unidades y Presupuesto
**Archivo esperado:** Proyecto Egresos (Pestaña: `Unidades`)

1.  **Lectura:** `pd.read_excel(file.file, sheet_name='Unidades', skiprows=4)`
2.  **Encabezados esperados:** `Número`, `Plazas`, `Nombre`, fuentes (`1.01`, `5.01`, `5.02`, `5.3`, `7.01`) y `Total Proyectado`.
3.  **Extracción de Fuentes:**
    * Identificar encabezados de financiamiento y mapearlos a `CatalogoFuentesFinanciamiento.clave` (crear si no existe).
4.  **Procesamiento de Unidades:**
    * Ignorar filas sin `Número`.
    * Comparar `clave` (Número), `plazas`, y `nombre`.
    * Generar el Diff.
5.  **Procesamiento de Presupuesto (Techos Financieros):**
    * Insertar/actualizar `TechoFinanciero` por (`ejercicio_id`, `unidad_administrativa_id`, `fuente_financiamiento_id`).
    * Convertir montos vacíos a 0.
    * `Total Proyectado` es derivado y NO se persiste.
6.  **Decisión Final:**
    * Si `confirmar_actualizacion == False`: Retornar JSON con el resumen (Nuevos, Modificados, Conflictos, Errores).
    * Si `confirmar_actualizacion == True`: Ejecutar `db.add_all()` para los nuevos y actualizar los objetos existentes. Llamar a `db.commit()`.

---

## 4. Flujo del Endpoint 2: Matriz Programática
**Archivo esperado:** Matriz programática (Pestaña: `Componentes y actividades`)

1.  **Lectura y Limpieza:**
    * `df = pd.read_excel(file.file, sheet_name='Componentes y actividades')`
    * `df[['CLAVE', 'PROGRAMA', 'EJECUTOR']] = df[['CLAVE', 'PROGRAMA', 'EJECUTOR']].ffill()` *(Para arreglar celdas combinadas)*.
    * La fila de TOTAL por programa es solo un separador visual (no se persiste). El total de programa es derivado.
2.  **Procesamiento Jerárquico (Top-Down):**
    * **Nivel 1 (Programas):** Buscar `CLAVE`. Comparar nombre y unidad ejecutora.
    * **Nivel 2 (Componentes):** Buscar `CLAVE` dentro del programa.
    * **Nivel 3 (Actividades):** Buscar `CLAVE`. Comparar descripción, líneas de acción PMD, y total meta.
    * **Nivel 4 (Metas Mensuales):** Comparar las 12 columnas. Si una actividad cambió su distribución de metas (ej. pasó de marzo a abril), registrar la modificación.
3.  **PMD (Línea de acción):**
    * La columna puede tener una o varias claves.
    * Separar por saltos de línea, limpiar espacios y remover punto final si existe (ej. `1.1.1.5.` -> `1.1.1.5`).
    * Crear/obtener `CatalogoPMD` por clave y relacionar con la actividad vía `inter_actividades_pmd`.
3.  **Decisión Final:**
    * Misma lógica de retorno o commit basada en `confirmar_actualizacion`.
