# Nexo IA — Pitch de hackathon

> **El gobierno de Durango ya tiene los servicios. Nexo IA es cómo el ciudadano
> los encuentra.**
>
> Documento de pitch. Borrador para refinar. Todo lo marcado como `[demo]` es lo que
> mostramos en vivo; lo marcado como `[roadmap]` es hacia dónde va.

---

## 1. El gancho (30 segundos)

> "Llevo semanas sin dormir bien y necesito hablar con un psicólogo, pero no sé a
> dónde ir ni si me alcanza."

Durango **sí** tiene esos servicios. Hay atención psicológica en la Secretaría de
Salud, en el DIF, en unidades municipales, en programas específicos. Hay líneas
de crisis. Mucho es gratuito o de cuota mínima.

Y aun así, esa persona no sabe que existen.

No porque la información esté oculta, sino porque está **repartida entre cinco
dependencias, cada una con su portal, su horario y su requisito**. Encontrarla
exige saber de antemano cuál es la dependencia correcta — que es exactamente lo
que la persona no sabe. **Le pedimos el dato que vino a buscar.**

Esa misma frase, escrita por WhatsApp a **Nexo IA**, devuelve en menos de un
minuto: qué unidades atienden salud mental cerca de ella, cuáles son gratuitas,
qué necesita llevar, en qué horario, y una cita agendada con folio. Con la fuente
oficial detrás de cada dato. Y si el mensaje sugiere riesgo, lo primero que
aparece es la línea de crisis con personas reales, no un formulario.

**No creamos un servicio nuevo. Hacemos que el que ya existe sea encontrable.**

> **Quién usa esto.** Nexo IA no es una app abierta al público general: es
> **infraestructura del gobierno de Durango**. Las dependencias que ya existen la
> usan para conectar con sus ciudadanos, centralizar su información y agilizar sus
> trámites. Dos tipos de usuario: **ciudadanos de Durango** y **personal de
> gobierno**. Ver §3.

---

## 2. El problema real (y por qué no es "hacer otro chatbot")

El problema no es que la información no exista. **Existe** — está publicada, en
PDFs, en portales, en reglamentos. El problema es que está **fragmentada por
institución en lugar de organizada por necesidad**.

El ciudadano llega con una necesidad ("mi hija necesita consulta y no tengo
IMSS"). El Estado responde con una estructura organizacional ("esa es otra
dependencia"). Entre esas dos cosas hay un abismo, y ese abismo lo cruza la
persona a pie, preguntando.

### Lo que cuesta ese abismo

| A quién | Qué le cuesta |
|---|---|
| **Ciudadano** | Visitas a la ventanilla equivocada, documentos incompletos, trámites abandonados a la mitad, días de trabajo perdidos |
| **Personal de ventanilla** | Contestar 40 veces la misma pregunta, recibir solicitudes incompletas, hacer de buscador humano |
| **Institución** | No saber qué le está preguntando la gente, no saber qué información está desactualizada, no poder medir la demanda real |
| **Desarrollador institucional** | Cada sistema nuevo es una integración desde cero, sin contrato ni estándar |

Y el costo invisible más caro: **la gente que simplemente ya no hace el trámite,
o que nunca se entera de que el servicio existía.** Ese abandono no aparece en
ninguna métrica actual. Una dependencia puede tener un programa excelente,
subutilizado, y no saber nunca que el problema era que nadie lo encontraba. En
Nexo IA eso sí se mide.

### Lo que Nexo IA **no** es

Esto define el proyecto tanto como lo que sí es:

- **No es una app pública más.** Es infraestructura para las dependencias que ya
  existen. No compite con ellas: las conecta.
- **No sustituye ningún sistema.** La Secretaría de Salud conserva su sistema; el
  municipio conserva el suyo. Nexo IA es la capa que los vuelve alcanzables desde
  una sola conversación.
- **No es un directorio.** Un directorio te da un teléfono. Nexo IA entiende tu
  caso, verifica los requisitos vigentes y **ejecuta** la gestión.
- **No está abierta al público general.** Dos audiencias: ciudadanos de Durango y
  personal de gobierno, cada uno con permisos distintos.

### Por qué un chatbot normal no lo resuelve

Un chatbot con un LLM encima te da una respuesta que *suena* correcta. En trámites
gubernamentales, una respuesta que suena correcta y está mal es **peor que no tener
respuesta**: mandas a alguien a una oficina a 40 km con los papeles equivocados.

El requisito no es "responder". Es **responder con respaldo, y poder demostrarlo
después**. Eso cambia por completo la arquitectura, y es la razón por la que Nexo
IA no es un wrapper de ChatGPT.

---

## 3. La propuesta de valor

Nexo IA tiene **un cliente y un beneficiario**: lo adopta el gobierno de Durango,
y quien lo siente es el ciudadano. El orden importa, porque el argumento de
adopción es institucional.

### Para la dependencia — quien adopta el sistema

Lo que gana una Secretaría, un municipio o un organismo al conectarse:

- **Su servicio se vuelve encontrable.** El programa que hoy conoce quien ya sabía
  de él, pasa a estar disponible para cualquiera que describa la necesidad que ese
  programa resuelve.
- **Deja de contestar lo mismo 500 veces.** Las consultas repetitivas se atienden
  solas, con la información oficial de la propia dependencia.
- **Ve su demanda real por primera vez.** Qué le preguntan, desde qué municipio,
  en qué horario, y —lo más valioso— **qué le preguntan que no supo contestar**.
- **Detecta su información vencida.** El sistema avisa qué fuentes están por
  expirar, en vez de que se entere por una queja.
- **No cambia su sistema.** Se conecta lo que ya tiene, mediante el MCP Mapper.
- **Cero pérdida de control:** define permisos por dominio, por operación y por
  rol; toda escritura queda auditada.

### Para el personal de ventanilla

Las solicitudes llegan completas y prevalidadas. Menos tiempo haciendo de buscador
humano, más tiempo resolviendo los casos que de verdad requieren criterio.

### Para el ciudadano de Durango — el resultado

Explicas tu necesidad como se la explicarías a un amigo, por WhatsApp, por
teléfono o en el portal, y recibes una ruta completa con fuentes: qué trámite es,
qué dependencia, qué documentos, cuánto cuesta, dónde y cuándo — y cuando hay
integración, la gestión hecha con folio.

### Para el área de sistemas del gobierno

Conectas un sistema existente registrando sus capacidades, no reescribiéndolo.
Cada integración nueva beneficia a todas las dependencias ya conectadas.

---

## 4. Cómo funciona, sin tecnicismos

### La idea central: un equipo, no un cerebro

La mayoría de los asistentes son **un** modelo respondiendo a todo. Nexo IA
funciona como **un equipo de trabajo con roles y jerarquía**, igual que una
oficina bien organizada. Cada agente tiene un trabajo, y —esto es lo importante—
**tiene prohibido hacer el trabajo de otro.**

Piénsalo como una ventanilla ideal:

| Rol en la oficina | Agente en Nexo IA | Qué hace |
|---|---|---|
| Quien te recibe en la puerta | **Clasificador** | Escucha qué necesitas y detecta el área, tu perfil y si traes varias necesidades juntas |
| El jefe de piso | **Supervisor** | Decide quién atiende tu caso, qué se puede hacer en paralelo y qué está permitido |
| El especialista del área | **Agente de dominio** | Sabe de vehículos, o de registro civil, o de ganadería — y **solo** de lo suyo |
| El auditor que revisa antes de firmar | **Verificador** | Comprueba que cada dato tenga una fuente vigente detrás. Si no la tiene, lo bloquea |
| El que saca cuentas | **Estimador** | Suma costos, cuenta pasos, calcula tiempos y detecta qué te falta |
| El único con permiso de firmar | **Agente transaccional** | Es el **único** que puede escribir en un sistema real: apartar cita, generar folio |
| Quien te lo explica | **Redactor** | Traduce todo al lenguaje que tú entiendes — no es lo mismo hablarle a un productor ganadero que a un despacho contable |
| El supervisor de calidad | **Juez (LLM-as-judge)** | Califica la respuesta *después* de darla, para saber si el sistema está mejorando |

### Las tres reglas que hacen que esto sea confiable

Esto es lo que más nos importa comunicar, porque es lo que nos separa de una demo
bonita:

**1. El que escribe no investiga.**
El agente que te redacta la respuesta final **no tiene acceso** al buscador ni a
los sistemas. Recibe una lista cerrada de hechos ya verificados y solo puede
reformularlos. Es imposible que "adorne" con datos que no existen, porque no
tiene de dónde sacarlos.

**2. Las cuentas las hace código, no la IA.**
Costos, sumas, conflictos de horario, permisos: todo eso se calcula con código
determinista. La IA interpreta y explica; **no calcula**. Si el sistema te dice
que son $3,480, esos $3,480 salieron de una suma auditable, no de un modelo
prediciendo el siguiente número.

**3. Nada se escribe sin confirmación y sin comprobante.**
Un solo agente puede ejecutar acciones reales, siempre con confirmación explícita
tuya, y **no declara éxito hasta recibir un folio verificable**. Si el sistema del
otro lado no contesta, te dice que no se hizo — no te dice "listo".

### Cómo generamos las pantallas: A2UI

Aquí hay una decisión de diseño de la que estamos orgullosos.

Cuando la IA quiere mostrarte algo — un checklist de documentos, un calendario de
citas, un comparador de trámites — **no genera código**. Genera una *descripción*
de la interfaz usando solo piezas de un catálogo aprobado (tarjetas, listas,
formularios, mapas, timelines), y esa descripción se valida antes de dibujarse.

¿Por qué importa? Porque "la IA genera HTML y lo ejecutamos" es una vulnerabilidad
con pasos extra. Con A2UI, **lo peor que puede pasar es que la interfaz no se
dibuje** — nunca que ejecute algo que no debía. Y como el catálogo es nuestro, la
accesibilidad y el diseño están garantizados de antemano, no dependen de lo que
al modelo se le ocurra esa vez.

Ventaja secundaria: la misma respuesta se adapta sola al canal. En el portal es
un checklist interactivo; en WhatsApp, los mismos datos se convierten en botones
y una lista numerada. Una sola lógica, todos los canales.

### Cómo conectamos sistemas: el MCP Mapper

Este es nuestro diferenciador de plataforma.

Normalmente, conectar el sistema de licencias de un municipio a un asistente es
un proyecto de semanas. Con el **MCP Mapper**, un administrador registra el
sistema (o importa su especificación técnica), el sistema propone
automáticamente las operaciones disponibles, se prueban en un entorno controlado,
se les asignan permisos y dominio, y **quedan publicadas como capacidades que los
agentes pueden usar** — con auditoría desde el primer uso.

Traducción para el jurado: **Nexo IA no se construye una vez. Crece cada vez que
alguien conecta un sistema nuevo, sin tocar el código de los agentes.**

---

## 5. Qué problemas ya resolvimos (no es solo un plan)

Esta sección importa: mucho de lo difícil ya está decidido y construido.

### Resuelto: la IA que inventa datos

**Problema:** los asistentes alucinan requisitos, costos y direcciones.
**Solución:** separación estricta entre *investigar*, *verificar* y *redactar*, más
un verificador independiente que bloquea toda afirmación sin fuente vigente. Cada
fuente tiene versión, fecha de vigencia, hash y responsable; una fuente vencida
deja de ser citable automáticamente.

### Resuelto: el interrogatorio interminable

**Problema:** los formularios y bots preguntan cosas que ya saben.
**Solución:** el **principio de preguntas mínimas**. Antes de preguntar, el sistema
intenta deducir del mensaje, el historial autorizado, el perfil y las respuestas
de los sistemas. Solo pregunta cuando falta un dato obligatorio, hay ambigüedad
real, se requiere consentimiento o la acción escribe en un sistema. Y cada dato
deducido queda marcado con su origen y nivel de confianza — un dato deducido
nunca se usa para una escritura sin confirmarse.

### Resuelto: "la IA hizo algo y no sabemos qué"

**Problema:** las decisiones de un sistema multiagente son una caja negra.
**Solución:** cada solicitud tiene un `trace_id` y **la ejecución completa se ve
como un grafo**, estilo n8n: qué agentes corrieron, qué se ejecutó en paralelo,
qué fuentes se consultaron, qué sistemas se llamaron, cuánto tardó cada paso, qué
modelo se usó y por qué, dónde hubo reintentos. No es un log para desarrolladores:
es una **pantalla del producto**.

### Resuelto: el costo y la dependencia de un solo proveedor

**Problema:** usar el modelo más caro para todo es insostenible.
**Solución:** un **router de modelos** que elige según la tarea — una clasificación
simple usa un modelo rápido y barato; el supervisor usa uno de razonamiento; el
juez usa deliberadamente uno *distinto* al que generó la respuesta, para que no se
califique a sí mismo. Y si un proveedor se cae o se satura, cambia solo y lo
registra.

### Resuelto: cuatro personas trabajando sin bloquearse

**Problema:** en un hackathon, el equipo se traba esperándose entre sí.
**Solución:** definimos los **contratos antes que las integraciones**. Frontend,
backend, agentes y base de datos trabajan contra esquemas tipados y datos de
prueba desde el día uno.

**Evidencia:** el núcleo Python ya corre con **870 pruebas automáticas en verde,
sin red, sin base de datos y sin credenciales**, en menos de cinco segundos. Encontramos y corregimos bugs reales antes
de tener una sola integración viva — entre ellos uno en el guardado de estado que
habría roto exactamente el flujo central de la demo, y que solo se manifestaba al
reanudar una conversación tras una confirmación. Está documentado en
[`docs/team/fase0_hallazgos.md`](./team/fase0_hallazgos.md).

---

## 6. La demo `[demo]`

### Recorrido 1 — Vehículos: "Quiero renovar mi licencia y saber si tengo adeudo"

Una frase, **dos intenciones**. El sistema las detecta juntas y ejecuta en
paralelo: busca requisitos en la base documental mientras consulta el adeudo y
localiza módulos. Devuelve una sola pantalla con adeudo, requisitos, documentos
faltantes, módulos cercanos y citas disponibles. Confirmas, y obtiene un folio.

**Qué mirar:** la respuesta consolidada, la lista de fuentes citadas, y el grafo
de ejecución mostrando lo que corrió en paralelo.

### Recorrido 2 — Salud: "Necesito hablar con un psicólogo y no sé a dónde ir"

El recorrido que mejor explica para qué sirve el sistema.

Aquí el usuario **no sabe el nombre del trámite, ni la dependencia, ni si tiene
derecho**. No puede llenar un formulario porque no sabe qué campo llenar. Es
justo el caso donde un portal tradicional falla: los portales exigen que ya sepas
a dónde ibas.

Nexo IA identifica que se trata de orientación en salud mental, consulta las
unidades que atienden ese servicio en Durango —Secretaría de Salud, DIF,
unidades municipales, programas vigentes—, cruza cuáles son gratuitas o de cuota
reducida, filtra por cercanía y horario, muestra qué necesita llevar y agenda la
cita con folio.

**Qué mirar:**
- **Cuántas preguntas hace el sistema:** las mínimas. Deduce municipio y perfil
  del contexto en vez de interrogar a alguien que ya está mal.
- **Que cada dato tenga fuente:** costo, requisito y horario citan el documento
  oficial de la dependencia que presta el servicio.
- **El tono del redactor:** la misma información se presenta distinto para alguien
  que pide ayuda que para un trámite administrativo.
- **La barrera de seguridad:** si el mensaje sugiere riesgo, lo primero que
  aparece es la **línea de crisis atendida por personas**, y el caso se escala a un
  humano. El sistema **no diagnostica, no interpreta síntomas y no sustituye a un
  profesional** — eso está limitado por diseño, no por configuración.

**Por qué elegimos este caso:** porque el servicio **ya existe y ya está pagado**.
El estado invierte en programas de salud mental que quedan subutilizados porque la
gente que los necesita no sabe que están ahí. Aquí el sistema no crea capacidad
nueva: **desbloquea la que ya se financió.** Ese es exactamente el argumento por el
que una dependencia debería conectarse.

### Recorrido 3 — Apertura de empresas: "Quiero abrir un negocio en Durango"

El contrapeso: un trámite complejo que cruza cuatro dependencias. El sistema
ordena los permisos por dependencia entre ellos (sin uso de suelo aprobado, la
licencia ni siquiera se recibe), acumula costos, detecta documentos faltantes y
arma un flujo interactivo paso a paso.

**Qué mirar:** las dependencias entre trámites — conocimiento que hoy solo existe
en la cabeza de alguien con experiencia.

### Recorrido 4 — El dashboard: la vista del gobierno

Cambiamos de sombrero: ahora somos la dependencia. **Este es el recorrido que le
habla al cliente real.**

Se ve la demanda por dominio y por municipio, las preguntas **sin respuesta** (lo
que la gente pregunta y no supimos contestar — la lista más valiosa del sistema,
porque es la demanda que hoy nadie mide), las fuentes por vencer, la latencia por
sistema conectado, el costo por solicitud y la calificación del juez.

**Qué mirar:** el administrador puede pedir una vista nueva en lenguaje natural
("compárame citas creadas contra citas completadas") y el sistema la genera —
consultando solo datos autorizados y agregados, nunca dando acceso libre a la
base de datos.

> **Honestidad sobre el alcance:** en la demo, las transacciones contra sistemas
> institucionales son **simuladas y están marcadas explícitamente como tales**.
> No tenemos —ni pretendemos tener— acceso a sistemas gubernamentales reales.
> Lo que sí es real: los contratos de esas operaciones son idénticos a los que
> usaría una integración productiva. El día que exista el convenio, se cambia el
> adaptador, no la arquitectura.

---

## 7. Hacia dónde va `[roadmap]`

### Corto plazo — completar la promesa
- **Los cinco dominios completos:** vehículos, registro civil, apertura de
  empresas, salud y ganadería.
- **Agente de voz.** El canal que más importa para quien no usa apps: llamas, te
  escucha, consulta, te contesta hablando y te manda el resumen por WhatsApp.
  Cierra la brecha digital en vez de ampliarla.
- **Mini-RAGs especializados:** en vez de "todo lo ganadero", separar sanidad,
  movilización, inventario y trazabilidad — respuestas más precisas y más baratas.

### Mediano plazo — que crezca sin nosotros
- **MCP Mapper abierto a instituciones:** que cada dependencia conecte su sistema
  sin depender del equipo original. El objetivo real: *tiempo para integrar un
  sistema nuevo medido en horas, no en meses.*
- **Detección automática de vacíos:** el sistema reporta solo qué preguntó la
  gente que no supo contestar, y qué fuentes están por vencer. La institución
  recibe una lista de tareas priorizada por demanda real.
- **Personalización profunda por perfil:** adulto mayor, productor rural,
  despacho contable, servidor público. Mismos hechos, distinta presentación.

### Largo plazo — la visión
- **Infraestructura compartida del estado de Durango.** Un municipio conecta su
  sistema de licencias y **los 39 municipios** heredan el patrón de integración.
  El valor de la red crece con cada dependencia que se suma: la que se conecta
  décima encuentra el camino hecho.
- **De reactivo a proactivo:** "tu verificación vence en 30 días, ¿te aparto
  cita?" — el trámite busca al ciudadano, no al revés. Solo es posible cuando las
  dependencias ya están conectadas.
- **Nexo IA como capa de interoperabilidad del estado**, no como otro portal. La
  pregunta del ciudadano deja de ser "¿en qué portal se hace esto?" y pasa a ser,
  simplemente, "¿qué necesitas?"
- **Modelo replicable a otros estados** una vez probado en Durango — la
  arquitectura no tiene nada específico de una entidad.

---

## 8. Por qué este equipo puede ejecutarlo

- **Arquitectura decidida, no improvisada.** Dos documentos técnicos completos:
  contratos entre módulos, plan por fases (MVP → Core → Pro → Extremo), plan de
  pruebas, plan de despliegue, riesgos con mitigación asignada.
- **Trabajo real ya en el repo:** núcleo tipado con 870 pruebas, portal y consola
  interna, renderer A2UI con catálogo validado, autenticación, esquemas de
  contratos versionados y fixtures por dominio.
- **Disciplina de estado.** Cada capacidad está marcada como `planeada`, `mock` o
  `implementada`. No decimos que algo funciona hasta que tiene una prueba que lo
  demuestre. Eso también es una decisión de producto.
- **Cuatro personas, cuatro frentes** —frontend, servicios base, base de datos,
  agentes— coordinados por contratos en vez de por reuniones.

---

## 9. El cierre

Durango ya tiene los servicios. Ya tiene los programas, las unidades, el
presupuesto ejercido y el personal. **Lo que no tiene es la capa que conecta todo
eso con la persona que lo necesita, en el momento en que lo necesita.**

Las dependencias no van a reorganizarse alrededor del ciudadano — no pueden, y no
deberían tener que hacerlo. Lo que sí puede existir es una capa que hable lenguaje
de personas de un lado y lenguaje de sistemas del otro, que **verifique todo lo
que afirma**, que **ejecute con permiso y deje comprobante**, y que **aprenda de
cada pregunta que no supo contestar**.

Nexo IA no le pide al gobierno de Durango que cambie cómo trabaja. Le pide que
**se conecte** — y a cambio le devuelve algo que hoy no tiene: saber qué le está
pidiendo su gente, y poder responderle en una sola conversación.

Eso es lo que construimos.

> **El gobierno de Durango ya tiene los servicios. Nexo IA es cómo el ciudadano
> los encuentra.**

---

## Anexo A — Frases para el escenario

Para el pitch hablado, por si sirven:

- "Durango ya tiene atención psicológica gratuita. El problema no es que falte el
  servicio: es que quien lo necesita no sabe que existe."
- "Le pedimos al ciudadano el dato que vino a buscar: cuál es la dependencia
  correcta."
- "Un servicio que nadie encuentra es presupuesto ejercido sin impacto. Nosotros
  no creamos capacidad nueva: desbloqueamos la que ya se pagó."
- "No le pedimos al gobierno que cambie sus sistemas. Le pedimos que los conecte."
- "Hoy, para hacer un trámite, el ciudadano tiene que ser su propio gestor. Nexo
  IA es ese gestor."
- "Un chatbot que se equivoca sobre un trámite es peor que no tener chatbot: le
  cuesta a alguien un día de trabajo y un viaje en vano."
- "El agente que te escribe la respuesta no tiene acceso a internet ni a los
  sistemas. Solo puede repetir hechos que otro agente ya verificó. No puede
  inventar aunque quisiera."
- "Las sumas las hace código. La IA explica, no calcula."
- "La IA no genera código de interfaz. Genera una descripción, y esa descripción
  se valida. Lo peor que puede pasar es que no se dibuje."
- "Cada respuesta es reconstruible. Podemos mostrarles exactamente por qué el
  sistema dijo lo que dijo."
- "La lista de preguntas que no supimos contestar es la parte más valiosa del
  dashboard. Es la demanda que hoy nadie está midiendo."
- "No pedimos que las instituciones cambien sus sistemas. Pedimos que los
  conecten."

## Anexo B — Preguntas difíciles del jurado

**"¿Esto no es solo ChatGPT con un prompt?"**
Un modelo suelto responde. Nosotros verificamos, calculamos con código, aplicamos
permisos, ejecutamos acciones con comprobante y dejamos traza auditable. Lo que
diferencia a Nexo IA no es el modelo — es todo lo que rodea al modelo. De hecho
usamos varios modelos distintos según la tarea, y el que juzga la calidad es
deliberadamente distinto del que respondió.

**"¿Qué pasa si la IA se equivoca en un trámite?"**
Tres barreras: el redactor no puede introducir datos nuevos porque no tiene
acceso a las fuentes; el verificador bloquea afirmaciones sin respaldo vigente; y
ninguna acción se ejecuta sin confirmación explícita del usuario. Cuando algo no
se puede verificar, el sistema lo dice — no rellena el hueco.

**"Si tocan salud mental, ¿qué pasa si alguien llega en crisis al asistente?"**
La pregunta correcta, y la respuesta está en la arquitectura, no en un parche.

El dominio de salud en Nexo IA está limitado por diseño a **orientación y
navegación de servicios**: te dice qué unidad atiende, dónde está, qué necesitas
y te agenda. **No diagnostica, no prescribe, no interpreta síntomas y no sustituye
a un profesional.** Ese límite está escrito en la propuesta desde antes de que
existiera una línea de código.

Cuando un mensaje sugiere riesgo, la conducta correcta no es que el sistema
"atienda": es **mostrar de inmediato la línea de crisis atendida por personas
reales y escalar a un humano**, antes que cualquier requisito o costo. El sistema
conecta con ayuda humana lo más rápido posible; no intenta ser esa ayuda.

Un sistema honesto reconoce dónde termina su competencia. Esa frontera es parte
del producto, no una limitación que pensemos quitar después.

**"¿Por qué el gobierno adoptaría esto en vez de mejorar sus portales?"**
Porque el problema no está dentro de ningún portal — está *entre* los portales.
Una dependencia puede tener el mejor sitio del país y aun así el ciudadano no
llegará si no sabía que era esa dependencia. Nexo IA no reemplaza esos portales:
los vuelve alcanzables desde una sola conversación, sin que ninguna dependencia
tenga que ceder el control de su sistema ni de sus datos.

**"¿Y si una dependencia no quiere conectarse?"**
El sistema funciona con las que sí. Cada integración es independiente y aporta
valor por sí sola, así que no hay un "todo o nada" que bloquee el arranque. Y el
dashboard vuelve visible la demanda insatisfecha en las áreas aún no conectadas
— que suele ser el mejor argumento para que la siguiente dependencia se sume.

**"¿Y si la información oficial cambia?"**
Cada fuente tiene versión, vigencia y responsable. Una fuente vencida se bloquea
automáticamente y aparece en el dashboard como pendiente de actualizar. El sistema
sabe cuándo *no* sabe.

**"¿Cómo lo conectan con sistemas reales que no tienen API?"**
El MCP Mapper acepta OpenAPI, esquemas JSON o configuración manual con un
adaptador. Para sistemas legados, el adaptador vive aislado y expone el mismo
contrato tipado que cualquier otra capacidad. Los agentes nunca saben —ni
necesitan saber— si detrás hay una API moderna o un sistema de 2004.

**"¿Es caro operarlo?"**
Por eso existe el router de modelos: cada tarea usa el modelo más barato que la
resuelve bien, y medimos costo por solicitud como métrica de primera clase, no
como reporte de fin de mes. La demo completa corre en Docker Compose sobre una
sola base de datos PostgreSQL.

**"¿Y la privacidad?"**
Minimización de datos, enmascaramiento, anonimización para analítica, retención
configurable, separación por institución y permisos por dominio, por herramienta
y por operación. Las escrituras y confirmaciones quedan en un registro que solo
se agrega, nunca se edita.
