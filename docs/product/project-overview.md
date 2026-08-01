# Nexo IA

## Hub universal de asistentes e integración institucional

## 1. Resumen ejecutivo

Nexo IA es una plataforma omnicanal de inteligencia artificial diseñada para conectar a ciudadanos, productores, empresas y personal institucional con servicios públicos y privados desde una sola interfaz.

El usuario no necesita conocer el nombre exacto de una dependencia, el sistema que debe utilizar ni el procedimiento correspondiente. Solo debe explicar su necesidad en lenguaje natural mediante WhatsApp, una llamada telefónica o un portal web. A partir de esa solicitud, Nexo IA identifica el dominio adecuado, consulta fuentes verificadas, utiliza las herramientas disponibles y genera una ruta clara con requisitos, costos, ubicación, tiempos, fuentes, documentos faltantes y acciones disponibles.

Cuando existe una integración con el sistema correspondiente, la plataforma también puede ejecutar acciones como consultar un adeudo, reservar una cita, registrar una solicitud, generar un folio, enviar un reporte o actualizar un registro.

Nexo IA incorpora una arquitectura multiagente, bases de conocimiento especializadas, un servidor MCP para ejecutar capacidades institucionales, un componente denominado MCP Mapper para integrar nuevos sistemas y una capa A2UI para generar interfaces dinámicas e interactivas.

La misma infraestructura alimenta un dashboard administrativo desde el cual las instituciones pueden consultar métricas, visualizar el flujo de los agentes, detectar necesidades no resueltas, supervisar integraciones y generar gráficas o interfaces personalizadas mediante lenguaje natural.

La propuesta busca crear una relación de beneficio mutuo:

- El ciudadano recibe orientación correcta y puede completar más trámites.
- La institución reduce consultas repetitivas y visitas incorrectas.
- El personal operativo recibe solicitudes más completas.
- Los responsables institucionales obtienen información sobre la demanda real.
- Los desarrolladores pueden incorporar sistemas progresivamente mediante MCP.
- La plataforma conserva trazabilidad sobre cada respuesta y operación.

---

## 2. Problema que resuelve

Actualmente, las instituciones públicas, dependencias, municipios, empresas y organismos especializados operan mediante portales, documentos, teléfonos y sistemas separados.

Para realizar una gestión, una persona normalmente debe descubrir:

- Qué institución le corresponde.
- Qué trámite necesita.
- Qué documentos debe presentar.
- Qué portal o sistema debe utilizar.
- Qué oficina debe visitar.
- Cuánto cuesta el procedimiento.
- Cuánto tiempo puede tardar.
- Si necesita una cita.
- Si el trámite puede realizarse en línea.
- Qué debe hacer cuando su caso involucra varias dependencias.
- Qué información sigue vigente.
- Qué pasos debe realizar primero.

Este problema se repite en áreas como:

- Control vehicular.
- Registro civil.
- Apertura de empresas.
- Servicios municipales.
- Salud.
- Gestión ganadera.
- Programas sociales.
- Protección civil.
- Educación.
- Servicios fiscales.
- Atención empresarial.

La consecuencia no es solamente una mala experiencia para el usuario. También provoca:

- Visitas a oficinas equivocadas.
- Solicitudes incompletas.
- Pérdida de tiempo.
- Saturación del personal.
- Repetición de preguntas.
- Errores en la orientación.
- Falta de trazabilidad.
- Duplicación de reportes.
- Dificultad para medir la demanda real.
- Desconocimiento de las necesidades que todavía no están cubiertas.
- Baja interoperabilidad entre sistemas institucionales.

Nexo IA transforma una solicitud informal en una ruta institucional verificable, adaptada al perfil y contexto del usuario.

---

## 3. Objetivo general

Desarrollar una plataforma universal de asistentes inteligentes que permita interpretar solicitudes en lenguaje natural, identificar el servicio o trámite correspondiente, recuperar información verificada, ejecutar capacidades institucionales mediante MCP y presentar los resultados en interfaces dinámicas y trazables.

---

## 4. Objetivos específicos

1. Unificar la atención mediante WhatsApp, llamadas telefónicas y una plataforma web.
2. Identificar automáticamente la dependencia, dominio, trámite o servicio adecuado.
3. Reducir al mínimo las preguntas realizadas al usuario, deduciendo información a partir del contexto disponible.
4. Consultar conocimiento documental mediante RAGs especializados por dominio.
5. Integrar sistemas externos mediante tools registradas en un servidor MCP.
6. Permitir que nuevos sistemas se incorporen mediante un MCP Mapper.
7. Ejecutar operaciones institucionales de lectura y escritura con permisos y auditoría.
8. Verificar que cada requisito, costo, ubicación y afirmación esté respaldado.
9. Generar interfaces dinámicas mediante A2UI según la necesidad del usuario.
10. Mostrar visualmente el flujo multiagente como un pipeline similar a n8n.
11. Seleccionar automáticamente el modelo de IA más adecuado para cada agente.
12. Generar dashboards, gráficas y vistas administrativas personalizadas.
13. Medir fidelidad, completitud, claridad, latencia, costo y éxito de las operaciones.
14. Mantener trazabilidad completa de agentes, fuentes, herramientas y decisiones.

---

## 5. Propuesta de valor

### Para el ciudadano

Nexo IA permite explicar una necesidad con palabras naturales y recibir:

- El trámite o servicio correcto.
- La dependencia responsable.
- Los documentos requeridos.
- Los costos.
- La oficina o plataforma correspondiente.
- Los tiempos aproximados.
- Una lista de pasos.
- Fuentes verificables.
- Citas disponibles.
- Un folio de confirmación cuando se ejecuta una acción.

### Para las instituciones

Nexo IA permite:

- Automatizar consultas frecuentes.
- Reducir visitas incorrectas.
- Disminuir solicitudes incompletas.
- Detectar trámites con mayor demanda.
- Identificar información faltante o desactualizada.
- Supervisar el desempeño de sistemas externos.
- Medir tiempos de atención.
- Analizar necesidades por zona.
- Detectar errores recurrentes.
- Integrar progresivamente sistemas existentes.
- Mantener auditoría de las respuestas generadas.

### Para desarrolladores y administradores

Nexo IA ofrece:

- Registro de capacidades mediante MCP.
- Importación de especificaciones OpenAPI.
- Configuración manual de integraciones.
- Generación de contratos de entrada y salida.
- Catálogo central de agentes, tools, fuentes y permisos.
- Constructor A2UI para interfaces dinámicas.
- Agente generador de prompts y definiciones de apoyo.
- Arquitectura modular preparada para crecer.

---

## 6. Canales de atención

El usuario podrá iniciar una interacción desde cuatro canales principales.

### 6.1 WhatsApp

Orientado a:

- Consultas rápidas.
- Envío de documentos.
- Seguimiento de trámites.
- Recepción de notificaciones.
- Consulta de folios.
- Confirmación de citas.
- Listas de requisitos.

Cuando el canal no permita presentar una interfaz compleja, Nexo IA convertirá la respuesta A2UI en una representación compatible, como botones, listas numeradas, mensajes interactivos o enlaces seguros al portal web.

### 6.2 Llamada telefónica

Un agente de voz podrá:

- Escuchar la solicitud.
- Transcribirla.
- Consultar el sistema.
- Formular únicamente preguntas indispensables.
- Responder verbalmente.
- Enviar posteriormente un resumen por WhatsApp o SMS.
- Transferir el caso cuando sea necesario.

### 6.3 Portal web

Permitirá:

- Conversaciones extensas.
- Carga de documentos.
- Visualización de fuentes.
- Formularios dinámicos.
- Checklists interactivos.
- Mapas y ubicaciones.
- Comparaciones.
- Historial de solicitudes.
- Seguimiento de citas.
- Representaciones A2UI detalladas.

### 6.4 Dashboard administrativo

Estará dirigido a:

- Administradores institucionales.
- Responsables de operación.
- Supervisores técnicos.
- Analistas.
- Desarrolladores de integraciones.
- Responsables de cumplimiento y auditoría.

---

## 7. Flujo general del sistema

```text
WhatsApp ──────────────┐
Llamada con IA ────────┼──► Gateway omnicanal
Portal web ────────────┘           │
                                   ▼
                         Gestor de contexto
                                   │
                                   ▼
                       Clasificador de necesidad
                                   │
                                   ▼
                         Supervisor multiagente
                                   │
                                   ▼
                       Router dinámico de modelos
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
          Agente de dominio   Verificador       Estimador
                 │                 │                 │
                 ▼                 └──────┬──────────┘
             Mini-RAG                    ▼
                 │              Objeto de hechos verificados
                 ▼                        │
        Catálogo de capacidades           ▼
                 │               Agente transaccional
                 ▼                        │
          Servidor MCP                    ▼
                 │               Constructor A2UI
                 ▼                        │
       Sistemas institucionales           ▼
                                  Redactor por audiencia
                                           │
                                           ▼
                              Respuesta omnicanal final
                                           │
                                           ▼
                              Evaluador LLM-as-judge
                                           │
                                           ▼
                               Métricas y auditoría
```

---

## 8. Principio de preguntas mínimas

Nexo IA deberá solicitar la menor cantidad posible de información al usuario.

Antes de formular una pregunta, el sistema intentará deducir la respuesta utilizando:

- El mensaje actual.
- El historial autorizado.
- El perfil del usuario.
- La ubicación aproximada autorizada.
- Los documentos enviados.
- Las respuestas de las tools.
- El catálogo institucional.
- Valores predeterminados seguros.
- Datos previamente confirmados.
- Relaciones entre trámites.

Una pregunta solo deberá realizarse cuando:

- Falte un dato obligatorio.
- Existan varias opciones igualmente probables.
- La deducción pueda provocar una operación incorrecta.
- Se requiera consentimiento.
- Se trate de un dato sensible.
- La acción implique escritura.
- Sea necesario confirmar un costo o cita.
- La información no pueda obtenerse mediante una tool autorizada.

El sistema no deberá preguntar información que ya posee o puede obtener automáticamente.

Cada dato deducido deberá registrar:

- Fuente de la deducción.
- Nivel de confianza.
- Si fue confirmado por el usuario.
- Si puede utilizarse para una operación de escritura.

---

## 9. Arquitectura de conocimiento

Nexo IA no dependerá permanentemente de un único RAG general.

Para la demostración podrá utilizarse una sola base vectorial, separada mediante colecciones o namespaces:

```text
vehiculos
registro_civil
ayuntamiento_empresas
salud
ganadero
```

Cada colección contendrá únicamente información relacionada con su dominio.

### 9.1 Catálogo central

El catálogo central almacenará:

- Dependencias.
- Dominios.
- Módulos.
- Servicios.
- Trámites.
- Fuentes documentales.
- Versiones.
- Fechas de vigencia.
- Relaciones entre trámites.
- Agentes responsables.
- Tools habilitadas.
- Roles autorizados.
- Esquemas de entrada y salida.
- Dependencias entre operaciones.
- Skills disponibles.
- Políticas de uso.
- Modelos permitidos.
- Componentes A2UI disponibles.

El supervisor consultará primero este catálogo para determinar qué dominio debe atender la solicitud.

Después delegará el trabajo al subagente correspondiente, que solamente podrá acceder a los documentos, skills y tools autorizados para su dominio.

### 9.2 Mini-RAGs especializados

A futuro, cada dominio podrá dividirse en RAGs más específicos.

Por ejemplo, el dominio ganadero podrá contener:

```text
ganadero_sanidad
ganadero_movilizacion
ganadero_inventario
ganadero_trazabilidad
ganadero_propietarios
```

Esta estrategia evita:

- Recuperar documentos irrelevantes.
- Saturar el contexto.
- Mezclar requisitos.
- Reindexar toda la plataforma.
- Dar acceso innecesario a información.
- Incrementar el costo de inferencia.
- Generar contradicciones entre dominios.

### 9.3 Ciclo de vida documental

Cada fuente deberá registrar:

- Institución responsable.
- URL o archivo de origen.
- Versión.
- Fecha de publicación.
- Fecha de vigencia.
- Fecha de última verificación.
- Dominio.
- Nivel de confianza.
- Responsable de actualización.
- Fragmentos indexados.
- Hash del documento.
- Estado: activo, vencido, sustituido o en revisión.

---

## 10. MCP Mapper: integrador universal de sistemas

El principal diferenciador técnico de Nexo IA será el MCP Mapper.

Su función será permitir que un desarrollador o administrador registre las capacidades de un sistema externo y las convierta en tools normalizadas disponibles para los agentes.

### 10.1 Información de una integración

El administrador podrá proporcionar:

- Nombre del sistema.
- Descripción.
- URL o adaptador.
- Método de autenticación.
- Especificación OpenAPI.
- Esquema JSON.
- Operaciones permitidas.
- Parámetros de entrada.
- Respuestas esperadas.
- Roles autorizados.
- Dominio correspondiente.
- Clasificación de lectura o escritura.
- Documentación.
- Ejemplos.
- Reglas.
- Restricciones.
- Límites de uso.
- Timeouts.
- Política de reintentos.
- Datos sensibles involucrados.

### 10.2 Flujo del MCP Mapper

```text
Registrar sistema
        │
        ▼
Importar OpenAPI, JSON o configuración manual
        │
        ▼
Analizar operaciones disponibles
        │
        ▼
Generar esquema MCP normalizado
        │
        ▼
Generar descripción y ejemplos
        │
        ▼
Validar parámetros y contratos
        │
        ▼
Clasificar lectura o escritura
        │
        ▼
Asignar dominio, agente, roles y permisos
        │
        ▼
Probar conexión
        │
        ▼
Ejecutar prueba controlada
        │
        ▼
Evaluar resultado
        │
        ▼
Registrar auditoría
        │
        ▼
Publicar tool para agentes autorizados
```

### 10.3 Separación de responsabilidades

Debe mantenerse una separación estricta:

- MCP registra y ejecuta capacidades.
- RAG almacena y recupera conocimiento documental.
- El catálogo central relaciona agentes, documentos, tools y módulos.
- Las skills definen cómo utilizar capacidades y conocimiento.
- A2UI representa información y captura datos.
- Los agentes razonan y coordinan.
- El código determinista ejecuta cálculos auditables.

Las tools no se almacenan dentro del RAG.

Las descripciones, manuales y ejemplos de las integraciones sí podrán indexarse para que los agentes comprendan cuándo y cómo utilizarlas.

### 10.4 Ejemplos de tools

#### Control vehicular

```text
consultar_adeudo_vehicular
consultar_requisitos_licencia
buscar_cita_licencia
reservar_cita_licencia
localizar_modulo_vehicular
```

#### Registro civil

```text
consultar_requisitos_acta
clasificar_tipo_correccion
localizar_oficialia
consultar_disponibilidad
solicitar_copia_acta
```

#### Ayuntamiento

```text
consultar_uso_suelo
consultar_requisitos_negocio
calcular_costos_apertura
consultar_proteccion_civil
registrar_solicitud_comercial
```

#### Salud

```text
localizar_unidad_salud
consultar_servicios_disponibles
consultar_requisitos_atencion
buscar_horarios
reservar_cita_orientacion
```

#### Ganadería

```text
consultar_animal
consultar_historial_sanitario
registrar_vacuna
consultar_movimientos
validar_requisitos_movilizacion
generar_alerta_sanitaria
```

---

## 11. Skills operativas

Cada skill deberá describir no solamente qué hace un agente, sino también el flujo optimizado que debe seguir.

Una skill podrá incluir:

- Objetivo.
- Dominio.
- Entradas.
- Salidas.
- Fuentes permitidas.
- Tools autorizadas.
- Secuencia recomendada.
- Acciones que pueden ejecutarse en paralelo.
- Datos reutilizables.
- Condiciones de reintento.
- Timeouts.
- Criterios de éxito.
- Reglas de verificación.
- Casos en los que debe preguntar.
- Casos en los que puede deducir.
- Política de errores.
- Reglas de escalamiento.
- Componentes A2UI recomendados.

### Ejemplo de flujo optimizado

Para renovar una licencia y consultar adeudos:

1. Detectar simultáneamente las intenciones de renovación y consulta de adeudo.
2. Reutilizar los datos del vehículo y del usuario.
3. Consultar requisitos en el RAG.
4. Consultar adeudos mediante MCP.
5. Buscar módulos y citas en paralelo.
6. Ejecutar el verificador y el estimador en paralelo.
7. Solicitar confirmación únicamente antes de reservar.
8. Generar una interfaz A2UI con:
   - Adeudos.
   - Requisitos.
   - Documentos faltantes.
   - Módulos.
   - Citas.
   - Botón de confirmación.
9. Registrar fuentes, tools, tiempos y resultado.

Esto reduce pasos, preguntas repetidas y latencia.

---

## 12. Sistema multiagente

### 12.1 Clasificador de necesidad

Responsabilidades:

- Interpretar la solicitud.
- Detectar intención.
- Identificar dominio.
- Identificar ubicación.
- Reconocer perfil.
- Detectar urgencia operativa.
- Separar múltiples necesidades.
- Identificar datos faltantes.
- Estimar confianza de clasificación.

No deberá:

- Inventar requisitos.
- Consultar sistemas externos.
- Ejecutar escrituras.
- Presentar una respuesta final.

### 12.2 Supervisor central

Responsabilidades:

- Consultar el catálogo.
- Crear el plan de ejecución.
- Delegar a subagentes.
- Decidir qué procesos pueden ejecutarse en paralelo.
- Aplicar permisos.
- Validar contratos JSON.
- Controlar reintentos.
- Controlar timeouts.
- Resolver contradicciones.
- Evitar que una solicitud llegue al dominio incorrecto.
- Detener una operación insegura.
- Consolidar los resultados.

### 12.3 Router dinámico de modelos

Seleccionará el modelo más apropiado para cada tarea según:

- Complejidad.
- Longitud del contexto.
- Tipo de agente.
- Carga actual.
- Latencia esperada.
- Costo.
- Nivel de riesgo.
- Necesidad de razonamiento.
- Modalidad de entrada.
- Disponibilidad del proveedor.
- Requisitos de privacidad.

Ejemplo:

```text
Clasificación sencilla          → modelo rápido y económico
Extracción estructurada         → modelo pequeño especializado
Supervisor complejo             → modelo de razonamiento
Redacción                       → modelo general
Visión de documentos            → modelo multimodal
Verificación crítica            → modelo de alta precisión
LLM-as-judge                    → modelo distinto al generador
```

El router podrá cambiar automáticamente de modelo cuando:

- Exista sobrecarga.
- Se exceda un timeout.
- El proveedor no esté disponible.
- El contexto supere la capacidad.
- La primera salida no cumpla el contrato.
- La tarea requiera mayor precisión.

Cada cambio deberá registrarse con:

- Modelo solicitado.
- Modelo utilizado.
- Motivo del cambio.
- Latencia.
- Costo estimado.
- Resultado.

### 12.4 Navegador de dominio

Existirá uno por área:

- Vehículos.
- Registro civil.
- Ayuntamiento y empresas.
- Salud.
- Ganadería.

Responsabilidades:

- Consultar el mini-RAG.
- Identificar el trámite correcto.
- Localizar la dependencia o unidad.
- Recuperar requisitos.
- Identificar relaciones con otros trámites.
- Proponer tools aplicables.
- Devolver hechos estructurados con fuentes.

### 12.5 Verificador

Responsabilidades:

- Comprobar que cada afirmación esté respaldada.
- Validar requisitos.
- Validar costos.
- Validar ubicaciones.
- Revisar vigencia de fuentes.
- Comparar respuestas de tools y documentos.
- Detectar contradicciones.
- Bloquear información no fundamentada.
- Marcar hechos inciertos.
- Verificar el resultado de las escrituras.

### 12.6 Estimador

Responsabilidades:

- Calcular pasos.
- Estimar tiempos.
- Sumar costos.
- Identificar documentos faltantes.
- Estimar dificultad.
- Proponer un orden de ejecución.
- Detectar dependencias.
- Calcular posibles visitas o interacciones.

El cálculo deberá realizarse con código determinista siempre que sea posible.

El estimador y el verificador se ejecutarán en paralelo.

### 12.7 Agente transaccional

Será el único agente autorizado para realizar operaciones de escritura.

Podrá:

- Reservar citas.
- Crear folios.
- Registrar solicitudes.
- Enviar reportes.
- Actualizar registros.
- Confirmar gestiones.
- Registrar vacunas.
- Iniciar trámites.

No confirmará una operación hasta obtener:

- Identificador.
- Folio.
- UUID.
- Código de confirmación.
- Respuesta verificable.
- Resultado simulado explícitamente marcado como mock.

Las acciones críticas podrán requerir confirmación humana.

### 12.8 Redactor por audiencia

Adaptará los hechos verificados para:

- Ciudadanos.
- Adultos mayores.
- Productores ganaderos.
- Empresas.
- Servidores públicos.
- Personal técnico.
- Usuarios con baja alfabetización digital.

No consultará directamente el RAG ni las tools.

Recibirá un objeto cerrado de hechos verificados para evitar que la personalización introduzca información nueva.

### 12.9 Analista de señales

Trabajará con información agregada para generar:

- Métricas.
- Tendencias.
- Reportes.
- Alertas.
- Hallazgos.
- Recomendaciones operativas.

Los cálculos, agrupaciones, umbrales y deduplicaciones se ejecutarán mediante código.

El agente interpretará los resultados, pero no modificará los valores calculados.

### 12.10 Evaluador LLM-as-judge

Calificará:

- Dominio seleccionado.
- Trámite identificado.
- Tool utilizada.
- Fidelidad a fuentes.
- Completitud.
- Claridad.
- Ausencia de datos inventados.
- Adaptación al perfil.
- Éxito de la acción.
- Calidad de la interfaz A2UI.
- Cantidad de preguntas realizadas.
- Cumplimiento de permisos.

Preferentemente utilizará un modelo diferente al que generó la respuesta.

### 12.11 Agente generador de prompts

Este agente apoyará al MCP Mapper, al constructor A2UI y a los administradores.

Podrá generar:

- Prompts para agentes.
- Instrucciones de tools.
- Descripciones MCP.
- Ejemplos de uso.
- Contratos JSON.
- Esquemas de validación.
- Casos de prueba.
- Prompts para extraer parámetros.
- Instrucciones para construir interfaces.
- Reglas de verificación.
- Plantillas para nuevas skills.

Sus salidas no se publicarán automáticamente.

Antes de activarse deberán pasar por:

- Validación de esquema.
- Revisión de seguridad.
- Prueba controlada.
- Aprobación administrativa cuando corresponda.
- Registro de versión.

---

## 13. Doble verificación y prevención de alucinaciones

Cada agente deberá ejecutar una autoverificación antes de devolver su resultado.

La autoverificación comprobará:

- Que no se agregaron datos no presentes.
- Que los valores provienen de una fuente.
- Que las referencias son válidas.
- Que el contrato de salida se cumple.
- Que no se confundieron dominios.
- Que no se afirmó el éxito de una acción sin confirmación.
- Que se respetaron los permisos.
- Que las deducciones están marcadas.

Después, el verificador independiente revisará el resultado consolidado.

El flujo será:

```text
Generación
    │
    ▼
Autoverificación del agente
    │
    ▼
Validación estructural
    │
    ▼
Verificador independiente
    │
    ▼
Evaluación LLM-as-judge
```

No se trata de pedir a todos los agentes que repitan el trabajo completo, sino de aplicar verificaciones específicas en cada etapa.

---

## 14. A2UI: interfaces dinámicas generadas por IA

A2UI será la capa encargada de convertir datos y acciones en interfaces interactivas.

La IA no generará código arbitrario para ejecutarlo directamente en el navegador. En su lugar, producirá un esquema declarativo validado contra un catálogo de componentes permitidos.

### 14.1 Componentes disponibles

El registro A2UI podrá incluir:

- Texto.
- Tarjetas.
- Tablas.
- Listas.
- Checklists.
- Formularios.
- Campos de fecha.
- Selectores.
- Botones.
- Alertas.
- Timeline.
- Mapas.
- Métricas.
- Gráficas.
- Comparadores.
- Visores de documentos.
- Estados de citas.
- Flujos de pasos.
- Confirmaciones.
- Descargas.
- Paneles de fuentes.

### 14.2 A2UI para usuarios

Ejemplos de interfaces generadas:

- Checklist de documentos.
- Tarjetas de oficinas cercanas.
- Calendario de citas.
- Formulario con campos faltantes.
- Comparación de trámites.
- Resumen de costos.
- Línea de tiempo del procedimiento.
- Mapa de dependencias.
- Confirmación de una operación.
- Seguimiento de folio.

### 14.3 A2UI para el flujo del sistema

El sistema generará una representación visual similar al editor de flujos de n8n.

Podrá mostrar:

- Nodo de entrada.
- Clasificador.
- Supervisor.
- Agentes activados.
- Procesos paralelos.
- Consultas RAG.
- Tools MCP.
- Reintentos.
- Errores.
- Latencias.
- Decisiones.
- Modelo utilizado.
- Verificación.
- Resultado final.

Cada ejecución podrá verse como un grafo.

Ejemplo:

```text
Entrada
  │
  ▼
Clasificador
  │
  ▼
Supervisor
  ├───────────────┐
  ▼               ▼
Agente dominio    Consulta de perfil
  │
  ├───────────────┐
  ▼               ▼
RAG              Tool MCP
  │               │
  └───────┬───────┘
          ▼
     Consolidación
      ├───────────┐
      ▼           ▼
 Verificador   Estimador
      └─────┬─────┘
            ▼
      Constructor A2UI
            │
            ▼
        Respuesta
```

### 14.4 A2UI administrativo dinámico

Un administrador podrá escribir solicitudes como:

- “Muéstrame las consultas de ganadería por municipio.”
- “Genera una gráfica de errores por sistema durante los últimos siete días.”
- “Compara las citas creadas con las citas completadas.”
- “Crea una tabla de preguntas sin respuesta.”
- “Muéstrame los trámites con mayor abandono.”
- “Diseña un panel para revisar la latencia de las tools.”

El sistema convertirá la solicitud en:

1. Una intención analítica.
2. Una consulta autorizada.
3. Una transformación determinista.
4. Un esquema A2UI.
5. Una interfaz validada.

La IA no accederá directamente a tablas sin restricciones.

La capa analítica aplicará:

- Control de acceso.
- Campos permitidos.
- Consultas parametrizadas.
- Límites.
- Agregación.
- Anonimización.
- Validación de métricas.
- Registro de auditoría.

---

## 15. Dashboard administrativo

El dashboard tendrá dos perspectivas principales.

### 15.1 Operación institucional

Mostrará:

- Consultas por dominio.
- Solicitudes más frecuentes.
- Consultas sin respuesta.
- Tasa de acciones completadas.
- Citas generadas.
- Tiempo promedio de resolución.
- Zonas con mayor demanda.
- Documentos faltantes.
- Sistemas con más errores.
- Tools más utilizadas.
- Conversaciones atendidas.
- Llamadas atendidas.
- Tasa de abandono.
- Nivel de satisfacción.
- Casos escalados.
- Tendencias por periodo.
- Costos acumulados.

### 15.2 Supervisión técnica

Mostrará:

- Timeline de agentes.
- Ejecuciones paralelas.
- Tools MCP invocadas.
- Latencia por tool.
- Reintentos.
- Timeouts.
- Errores.
- Fuentes utilizadas.
- Resultado del verificador.
- Calificación LLM-as-judge.
- Costos de inferencia.
- Modelo utilizado por agente.
- Cambios automáticos de modelo.
- Versión del RAG.
- Versión de las fuentes.
- Acciones de escritura.
- Confirmaciones.
- Contratos JSON.
- Deducciones realizadas.
- Preguntas formuladas.
- Esquema A2UI generado.

---

## 16. Módulos de demostración

### 16.1 Vehículos

Caso:

> “Quiero renovar mi licencia y saber si tengo algún adeudo.”

El sistema deberá:

1. Identificar dos intenciones.
2. Recuperar requisitos de renovación.
3. Consultar adeudos mediante una tool.
4. Localizar módulos.
5. Consultar citas.
6. Mostrar costos.
7. Identificar documentos faltantes.
8. Proponer una cita.
9. Reservarla después de la confirmación.
10. Mostrar el folio.

### 16.2 Registro civil

Caso:

> “Necesito corregir un error en mi acta de nacimiento.”

El sistema deberá:

1. Identificar si corresponde copia, aclaración o corrección.
2. Solicitar únicamente el dato indispensable para diferenciar el procedimiento.
3. Mostrar requisitos.
4. Localizar la oficialía.
5. Mostrar costos y tiempos.
6. Generar una ruta.
7. Permitir iniciar una solicitud simulada.

### 16.3 Ayuntamiento y apertura de empresas

Caso:

> “Quiero abrir una taquería en Durango.”

El sistema deberá:

1. Identificar el tipo de establecimiento.
2. Relacionar permisos.
3. Ordenar las dependencias.
4. Mostrar requisitos por trámite.
5. Calcular costos acumulados.
6. Detectar dependencias entre trámites.
7. Mostrar tiempos.
8. Generar un flujo interactivo.
9. Consultar citas.
10. Iniciar una solicitud cuando sea posible.

### 16.4 Salud

Caso:

> “No tengo IMSS y necesito llevar a mi hija a consulta.”

El sistema deberá:

1. Identificar la necesidad de orientación.
2. Consultar instituciones disponibles.
3. Localizar la unidad adecuada.
4. Mostrar requisitos.
5. Consultar canales y horarios.
6. Agendar una cita cuando exista una integración.
7. Mostrar fuentes.

Este módulo se limitará a orientación y navegación de servicios.

No deberá:

- Diagnosticar.
- Prescribir medicamentos.
- Sustituir a profesionales.
- Interpretar síntomas como diagnóstico.
- Afirmar una urgencia clínica sin protocolos autorizados.

### 16.5 Ganadería

Caso:

> “Necesito registrar una vacuna y saber si el animal puede movilizarse.”

El sistema deberá:

1. Identificar al animal.
2. Consultar su historial.
3. Recuperar requisitos sanitarios.
4. Verificar reglas de movilización.
5. Registrar la vacuna mediante una tool.
6. Obtener confirmación.
7. Mostrar restricciones o documentos faltantes.
8. Generar una alerta si existe un riesgo sanitario.

---

## 17. Seguridad y gobierno de datos

Nexo IA aplicará seguridad por diseño.

### 17.1 Autenticación y autorización

- Control de acceso basado en roles.
- Permisos por dominio.
- Permisos por tool.
- Permisos por operación.
- Separación entre lectura y escritura.
- Confirmación adicional para acciones críticas.
- Tokens de corta duración.
- Credenciales almacenadas de forma segura.

### 17.2 Privacidad

- Minimización de datos.
- Consentimiento.
- Enmascaramiento.
- Anonimización para analítica.
- Retención configurable.
- Eliminación controlada.
- Separación de datos por institución.
- Cifrado en tránsito y reposo.

### 17.3 Prevención de abuso

- Límites de uso.
- Validación de parámetros.
- Listas de operaciones permitidas.
- Sandboxing de adaptadores.
- Protección contra prompt injection.
- Filtrado de contenido recuperado.
- Detección de instrucciones maliciosas en documentos.
- Bloqueo de ejecución arbitraria.
- Revisión de tools nuevas.

### 17.4 Auditoría

Cada ejecución registrará:

- Usuario o sesión.
- Canal.
- Solicitud.
- Dominio.
- Agentes utilizados.
- Modelos.
- Fuentes.
- Tools.
- Parámetros autorizados.
- Respuestas.
- Acciones.
- Confirmaciones.
- Folios.
- Errores.
- Tiempos.
- Costos.
- Evaluaciones.

---

## 18. Observabilidad y logging

Para el hackathon se utilizará logging estructurado JSONL.

Ejemplo:

```json
{
  "trace_id": "trace-001",
  "timestamp": "2026-07-30T02:00:00-06:00",
  "channel": "web",
  "domain": "vehiculos",
  "agent": "verificador",
  "model": "reasoning-model",
  "event": "agent_completed",
  "latency_ms": 1280,
  "sources": ["doc-licencias-v3"],
  "tools": ["consultar_adeudo_vehicular"],
  "status": "success",
  "grounded": true
}
```

El sistema deberá permitir reconstruir el flujo completo mediante un `trace_id`.

---

## 19. Métricas de evaluación

### Calidad

- Precisión del dominio.
- Precisión del trámite.
- Fidelidad a fuentes.
- Completitud.
- Claridad.
- Tasa de datos inventados.
- Adaptación al perfil.
- Calidad del esquema A2UI.

### Operación

- Tasa de acciones completadas.
- Tasa de tools exitosas.
- Tasa de citas confirmadas.
- Cantidad de folios generados.
- Tasa de conflictos.
- Tiempo promedio de resolución.
- Cantidad de preguntas por solicitud.
- Porcentaje de datos deducidos correctamente.

### Rendimiento

- Latencia total.
- Latencia por agente.
- Latencia por tool.
- Tiempo de recuperación RAG.
- Uso de tokens.
- Costo por solicitud.
- Porcentaje de cambios de modelo.
- Porcentaje de ejecución paralela.

### Integración

- Tools registradas.
- Tools validadas.
- Sistemas conectados.
- Errores por integración.
- Tiempo para registrar una nueva integración.
- Porcentaje de contratos válidos.

---

## 20. Alcance para el hackathon

### Core

- Portal web funcional.
- Integración básica con WhatsApp.
- Supervisor central.
- Mínimo tres agentes especializados.
- Cinco dominios demostrables.
- RAG local dividido por namespaces.
- Servidor MCP con tools reales o mockeadas.
- Respuestas estructuradas con fuentes.
- Logging JSONL.
- Dashboard con métricas básicas.
- Visualización del pipeline.
- A2UI con componentes predefinidos.
- Inicio mediante un solo comando.
- Repositorio documentado.

### Pro

- Agente telefónico.
- Reservación de citas.
- Acciones de escritura mediante MCP.
- Manejo de conflictos.
- Generación de folios.
- MCP Mapper funcional.
- Registro de una integración de demostración.
- Router automático de modelos.
- Formularios A2UI dinámicos.
- Dashboard personalizado mediante lenguaje natural.

### Extremo

- Verificador y estimador en paralelo.
- Personalización por perfil.
- Mini-RAGs especializados.
- Detección de contradicciones.
- Evaluación LLM-as-judge.
- Métricas de fidelidad.
- Panel técnico de trazabilidad.
- Actualización controlada del corpus.
- Integración dinámica de un sistema externo.
- Doble verificación.
- Constructor visual del flujo.
- Agente generador de prompts.
- Cambio de modelos según carga y complejidad.
- Comparación entre costo, latencia y precisión.
- Generación segura de interfaces administrativas.

---

## 21. Arquitectura técnica recomendada

Para el hackathon se recomienda un monolito modular desplegado mediante Docker Compose.

No es conveniente construir cinco microservicios completamente independientes durante la primera versión.

Cada dominio deberá tener:

```text
/domains
  /vehiculos
    agent
    rag
    tools
    schemas
    prompts
    tests
  /registro_civil
  /ayuntamiento
  /salud
  /ganadero
```

Componentes principales:

```text
/apps
  /web
  /admin

/backend
  /gateway
  /supervisor
  /model-router
  /agents
  /a2ui
  /mcp-mapper
  /analytics
  /audit

/catalog
  agents
  tools
  sources
  skills
  permissions
  ui-components

/data
  documents
  vector-store
  mocks
  logs
```

### Tecnologías posibles

- Frontend: Next.js o React.
- Backend: FastAPI.
- Orquestación: Python.
- Base de datos: PostgreSQL.
- Vector store: Qdrant, Chroma o pgvector.
- MCP: servidor propio compatible con el protocolo.
- Voz: proveedor STT/TTS intercambiable.
- WhatsApp: proveedor oficial o sandbox.
- Métricas: PostgreSQL y agregaciones deterministas.
- Despliegue: Docker Compose.
- Validación: Pydantic y JSON Schema.
- Observabilidad: logs JSONL y trazas.

---

## 22. Flujo de una solicitud completa

Ejemplo:

> “Quiero abrir una taquería en Durango.”

### Paso 1. Entrada

El gateway recibe:

- Mensaje.
- Canal.
- Sesión.
- Perfil autorizado.
- Ubicación disponible.

### Paso 2. Clasificación

El clasificador produce:

```json
{
  "domain": "ayuntamiento_empresas",
  "intent": "abrir_negocio",
  "business_type": "taqueria",
  "location": "Durango",
  "missing_required_fields": [],
  "confidence": 0.95
}
```

### Paso 3. Planificación

El supervisor determina:

- Consultar RAG de apertura de empresas.
- Consultar catálogo de permisos.
- Ejecutar estimador.
- Consultar disponibilidad de citas.
- Ejecutar verificador en paralelo.
- Preparar una interfaz A2UI.

### Paso 4. Selección de modelos

El router asigna:

- Clasificación: modelo rápido.
- Navegación: modelo general.
- Supervisor: modelo de razonamiento.
- Verificación: modelo de alta precisión.
- Redacción: modelo económico.

### Paso 5. Recuperación

El agente de dominio recupera:

- Uso de suelo.
- Licencia de funcionamiento.
- Protección civil.
- Requisitos sanitarios.
- Dependencias.
- Fuentes.

### Paso 6. Tools

El servidor MCP consulta:

- Costos.
- Oficinas.
- Horarios.
- Disponibilidad.
- Citas.

### Paso 7. Paralelismo

El verificador valida las afirmaciones mientras el estimador calcula:

- Orden.
- Costos.
- Tiempo.
- Documentos faltantes.

### Paso 8. Consolidación

El supervisor genera un objeto de hechos verificados.

### Paso 9. A2UI

El constructor genera:

- Resumen.
- Flujo de permisos.
- Checklist.
- Tabla de costos.
- Timeline.
- Botones de cita.
- Fuentes.

### Paso 10. Respuesta

El redactor adapta el lenguaje al perfil.

### Paso 11. Evaluación

El LLM-as-judge califica la respuesta.

### Paso 12. Auditoría

Se almacenan la traza, fuentes, tools, modelos, latencia y costo.

---

## 23. Estrategia de demostración

La demostración deberá mostrar tanto la experiencia del usuario como la arquitectura.

### Escena 1. Solicitud ciudadana

Un usuario escribe desde el portal o WhatsApp:

> “Quiero renovar mi licencia y saber si debo algo.”

### Escena 2. Pipeline visual

El dashboard muestra en tiempo real:

- Clasificación.
- Selección del dominio.
- Modelo elegido.
- Consulta RAG.
- Tool MCP.
- Verificador y estimador en paralelo.
- Constructor A2UI.

### Escena 3. Respuesta interactiva

El usuario recibe:

- Adeudo.
- Requisitos.
- Checklist.
- Costos.
- Oficinas.
- Citas disponibles.

### Escena 4. Acción

El usuario selecciona una cita.

El agente transaccional realiza la operación y devuelve un folio.

### Escena 5. MCP Mapper

El administrador importa una especificación de un sistema nuevo.

El Mapper:

- Detecta una operación.
- Genera la tool.
- Valida el esquema.
- Ejecuta una prueba.
- Publica la capacidad.

### Escena 6. Dashboard dinámico

El administrador solicita:

> “Genera una gráfica de las consultas más frecuentes por dominio.”

El sistema genera una interfaz A2UI con datos reales de la demostración.

---

## 24. Riesgos y mitigaciones

### Información desactualizada

Mitigación:

- Versionado.
- Fechas de vigencia.
- Revisión periódica.
- Bloqueo de fuentes vencidas.

### Alucinaciones

Mitigación:

- RAG especializado.
- Contratos estructurados.
- Autoverificación.
- Verificador.
- LLM-as-judge.
- Fuentes obligatorias.

### Operaciones incorrectas

Mitigación:

- Agente transaccional exclusivo.
- Confirmación.
- Permisos.
- Idempotencia.
- Folios.
- Auditoría.

### Sobrecarga o latencia

Mitigación:

- Router de modelos.
- Ejecución paralela.
- Caché.
- Timeouts.
- Reintentos.
- Modelos alternativos.

### Integraciones inseguras

Mitigación:

- Validación.
- Clasificación lectura/escritura.
- Pruebas controladas.
- Sandboxing.
- Roles.
- Aprobación.

### Interfaces inválidas

Mitigación:

- A2UI declarativo.
- Registro cerrado de componentes.
- Validación de esquemas.
- Sin ejecución de código arbitrario.

---

## 25. Entregables

1. Repositorio funcional.
2. README con arquitectura, instalación y demostración.
3. Archivo de dependencias.
4. Script de arranque de una línea.
5. Portal web.
6. Dashboard administrativo.
7. RAG local por namespaces.
8. Servidor MCP.
9. Tools mockeadas.
10. MCP Mapper de demostración.
11. Pipeline multiagente.
12. Constructor A2UI.
13. Visualizador de flujo.
14. Logging JSONL.
15. Casos de prueba.
16. Métricas de evaluación.
17. Video o guion de demostración.

---

## 26. Criterios de éxito del prototipo

El prototipo se considerará exitoso cuando:

- Clasifique correctamente al menos cuatro de cinco casos principales.
- Identifique el trámite correcto.
- Muestre requisitos respaldados.
- Utilice la tool adecuada.
- Ejecute una acción con folio.
- Muestre el flujo multiagente.
- Ejecute verificador y estimador en paralelo.
- Genere una interfaz A2UI.
- Registre una nueva tool mediante el MCP Mapper.
- Genere una gráfica administrativa mediante lenguaje natural.
- Mantenga trazabilidad.
- No confirme acciones sin respuesta verificable.
- Reduzca preguntas innecesarias.

---

## 27. Propuesta de valor en una frase

**Nexo IA es la plataforma unificada que conecta al gobierno y a las instituciones con las personas, convirtiendo una solicitud en lenguaje natural en una ruta verificable, una interfaz interactiva y, cuando existe una integración disponible, una acción confirmada.**

---

## 28. Pitch breve

Nexo IA es un hub universal de asistentes que conecta a ciudadanos, productores y empresas con servicios públicos y privados desde WhatsApp, llamadas y web.

Un supervisor multiagente identifica la necesidad, selecciona automáticamente el modelo de IA más adecuado, consulta conocimiento verificado en RAGs especializados y utiliza tools MCP para buscar información, consultar sistemas, reservar citas o ejecutar operaciones.

Para la demostración integra vehículos, registro civil, apertura de empresas, salud y gestión ganadera.

Además, incorpora un MCP Mapper que permite registrar nuevas capacidades, una capa A2UI que genera formularios, checklists, gráficas y flujos interactivos, y un dashboard que muestra demanda, desempeño, fuentes, errores, costos y trazabilidad completa del pipeline.

Nexo IA no solo responde preguntas: conecta sistemas, ejecuta acciones y transforma las necesidades reales de las personas en información útil para las instituciones.

---

## 29. Cierre

Nexo IA propone una capa de interoperabilidad inteligente sobre los sistemas institucionales existentes.

No busca reemplazar inmediatamente los portales, bases de datos o procesos actuales. Su objetivo es conectarlos progresivamente mediante contratos, adaptadores y tools MCP, ofreciendo al usuario un único punto de entrada.

La combinación de agentes especializados, mini-RAGs, MCP, A2UI, selección dinámica de modelos, evaluación automática y analítica institucional permite construir una solución escalable, verificable y aplicable tanto al sector público como al privado.

El resultado es una plataforma en la que las personas pueden expresar lo que necesitan sin comprender previamente la estructura institucional, mientras las organizaciones obtienen una forma controlada de automatizar servicios, integrar sistemas y conocer las necesidades reales de sus usuarios.
