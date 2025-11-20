# **Civic Knit**

**Lema/Slogan**: “Enlazando personas con su localidad | Engaging people with their community”  
Plataforma neutral de aporte cívico entre personas y su localidad

## **1. Situación Actual**

Los miembros de la comunidad a menudo tienen dificultades para encontrar información precisa y oportuna sobre políticas locales, eventos y servicios, en donde los canales tradicionales carecen de interactividad y personalización, lo que genera desinterés y desinformación.

## **2. ¿Cómo Revertir la Situación Actual?**

Creando una plataforma soportada en Inteligencia Artificial que de cause a la participación cívica que permita a las comunidades acceder a información del gobierno local, participar en discusiones y recibir actualizaciones personalizadas.

## **3. Descripción General**

**Civic Knit** es una plataforma centralizada diseñada para orientar, aprender y consultar información cívica verificada, libre de propaganda, ideologías, afinidades y corrientes políticas. Cualquier ciudadano puede hacer uso de la plataforma de forma anónima o crear una cuenta de acceso para personalizar su experiencia.

## **4. Objetivo Principal**

Ser la herramienta cercana a las personas en la que se brinde información relativa a su localidad, y cuyos fines son únicamente educativos e informativos. Esta no pretende influir en la toma de decisiones de los miembros de la comunidad ni guiar sus acciones de manera directa o indirecta, actuando solo como una fuente de información para que cada individuo ejerza de manera responsable la toma de sus propias decisiones basadas en su juicio, contexto y circunstancias particulares.

## **5. ¿Cómo Afrontar el Reto?**

- **Información electoral confusa**: explica cómo funciona una elección, qué aparece en la boleta y conceptos clave como padrón, voto nulo, actas o casillas.
- **Funciones del gobierno local**: aclara el papel de alcaldías, concejales y el presupuesto participativo.
- **Trámites básicos**: guías prácticas para RFC, INE, empadronamiento y servicios municipales.
- **Acceso disperso a oportunidades**: centraliza becas, ferias de empleo, eventos culturales y talleres.

## **6. Público Objetivo**

Miembros de comunidad que:

- Sean mayores de edad.
- Desean una plataforma ágil y de fácil acceso que ofrezca información concreta y neutral a través del uso de lenguaje natural.
- Son usuarios con experiencia o novatos en el uso de plataformas soportadas con tecnologías de Inteligencia Artificial.
- No se sienten atraídos para informarse de los asuntos de gobierno, representación, administración y recreación de su comunidad.
- Sienten vulnerados sus derechos y privacidad.
- Son internautas o usuarios de diferentes portales o plataformas que se sienten frustrados por la complejidad y el tiempo dedicado en allegarse de información.
- Desean entender su gobierno local, la experiencia, iniciativas, propuestas y el papel que juegan sus representantes actuales y futuros para con la comunidad.
- Votarán por primera vez y/o no comprenden bien el proceso electoral.
- Son migrantes o recién llegados y requieren orientación sobre trámites y servicios locales.

## **7. Aprovechar la IA para Potenciar la Participación Cívica**

### 7.1 Acceso centralizado a información

- Plataforma con chatbot **moderado**.
- Personalización e Identificación de audiencia por intereses, temas, edad, localidad, genero, lenguaje.
- Canales de comunicación: email, SMS, redes sociales y podcast de audio.

### 7.2 Información oportuna

- Extracción desde fuentes oficiales comprobadas.
- Comparaciones “antes vs ahora” en trámites.
- Actualización y precisión continua de la información.

### 7.3 Espacios seguros

- Entorno neutral y confiable con reglas claras.
- Redes sociales moderadas (ej. Mastodon). ⭐ implementación a futuro

## **8. Temas que Atiende**

- **Política local**: perfiles de representantes y candidatos, iniciativas, logros y declaraciones oficiales.
- **Eventos**: políticos, culturales, tecnológicos y especializados.
- **Servicios públicos**: agua, energía, residuos, infraestructura, salud, educación, cultura, deporte, seguridad, trámites administrativos y electorales, transporte, mercados y vivienda.

## **9. Principios y Lineamientos**

- Neutralidad absoluta.
- No sugiere o recomienda acerca de los temas consultados.
- No emite opiniones políticas ni predicciones electorales.
- Contenido claro e inclusivo.
- Lenguaje respetuoso y accesible para cualquier nivel socioeconómico y sociocultural.
- Garantizar la accesibilidad y usabilidad para usuarios con diversas capacidades (lectores de pantalla, contraste visual, dispositivos móviles).

## **10. Casos de Uso**

### Globales

#### Identificación, Autenticación y Privacidad

- **Modo anónimo**: no se solicitan datos personales. no se define perfil para temas de interés, canales de interacción, opcionalmente podrá definir etnia, idioma y género. obligadamente se obtendrá ubicación a través del navegador/ISP (cómo lo hace google o bing). 
- **Cuenta registrada**: se solicitarán datos personales. se define perfil temas de intéres, canales de interacción (personalizar secciones cívicas - considero que se puede personalizar en los intereses). Los datos históricos podrán ser eliminados en cualquier momento y nunca se usarán o compartirán con fines políticos o con terceros. obligadamente se obtendrá ubicación a través del navegador/ISP (cómo lo hace google o bing).
- Capacidad para entender y manejar 3 lenguajes: inglés - Estados Unidos, español México y francés Francia.

### Particulares

- **Caso 1**  
Usuario:“¿Qué hace un concejal [alcalde en México] en CDMX?”  
Civic Knit: Explica de forma breve y neutral las funciones del concejal (alcalde) y su rol en la alcaldía.  

- **Caso 2**  
Usuario: “¿Necesito renovar mi INE, qué documentos piden?”  
Civic Knit: Muestra requisitos actualizados, opciones de cita y diferencias entre reposición, corrección y renovación.

- **Caso 3**  
Usuario: “¿A quién le corresponde reparar la luz en mi calle?”  
Civic Knit: Indica que corresponde a la alcaldía y detalla el procedimiento de reporte.

- **Caso 4**  
Usuario: “Qué eventos gratuitos hay esta semana?”  
Civic Knit: Lista actividades verificadas y horarios, sin recomendar ninguna en particular.

📌 **Desarrollar el número de casos necesarios para cubrir los requerimientos**

## **11. Componentes (Secciones/Servicios)**

- **Gestión de sesión**: inicio, cierre y recuperación de contraseña.
- **Información centralizada**: con base de datos cívica.
- **Chatbot moderado** con IA responsable, etc.
    - **Moderación híbrida**: IA + reglas claras + supervisión humana.
- **Perfil**
    - **Temas de interese**.
    - **Canales de comunicación**: email, SMS, redes sociales, podcast.
- **Privacidad y Cookies**
- **Términos de uso**
- **Código de conducta**
