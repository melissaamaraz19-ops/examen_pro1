# 🎓 Sistema de Horarios con Algoritmos Genéticos

Sistema automatizado para la generación de horarios académicos utilizando algoritmos genéticos, desarrollado como proyecto de tesis para Ingeniería en Sistemas Computacionales - Universidad Politécnica de Querétaro (UPQ).

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [Uso del Sistema](#-uso-del-sistema)
- [Carga de Datos de Prueba](#-carga-de-datos-de-prueba)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Restricciones Implementadas](#-restricciones-implementadas)
- [Tecnologías](#-tecnologías)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

- **Generación automática de horarios** usando algoritmos genéticos
- **9 restricciones duras** implementadas:
  - Conflictos de docente (un docente en dos lugares simultáneamente)
  - Violación de reservas de módulos
  - Violación de disponibilidad del docente
  - Asignación de turno incorrecto
  - Exceso/falta de sesiones por semana
  - Máximo 2 bloques por día por materia
  - Máximo 2 bloques consecutivos por materia
  - Máximo 35 horas semanales por docente
  - Choques de grupo
- **Visualización interactiva** de horarios por grupo
- **Sistema de experimentos** con métricas y gráficas
- **Exportación a Excel** de horarios generados
- **Dashboard de validación** pre-ejecución
- **Comparación de experimentos**

---

## 🔧 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** ([Descargar](https://www.python.org/downloads/))
- **PostgreSQL 12+** ([Descargar](https://www.postgresql.org/download/)) o SQLite (incluido con Python)
- **Git** ([Descargar](https://git-scm.com/downloads))
- **pip** (gestor de paquetes de Python, viene con Python)

### Verificar instalación:

```bash
python --version    # Debe mostrar Python 3.8 o superior
pip --version       # Debe mostrar pip
git --version       # Debe mostrar git
psql --version      # Debe mostrar PostgreSQL (opcional)
```

---

## 📥 Instalación

### 1. Clonar el Repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/BOWadapter/ag.git

# Entrar al directorio del proyecto
cd ag
```

### 2. Crear Entorno Virtual

```bash
# En Linux/Mac
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

**Deberías ver `(venv)` al inicio de tu terminal.**

### 3. Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt
```

**Dependencias principales:**

- Flask 2.3+
- SQLAlchemy 2.0+
- Flask-Migrate 4.0+
- matplotlib 3.8+
- psycopg2-binary 2.9+ (para PostgreSQL)
- openpyxl 3.1+ (para exportación Excel)

---

## ⚙️ Configuración

### 1. Variables de Entorno

```bash
# Crear archivo .env en la raíz del proyecto
touch .env

# Editar el archivo
nano .env
```

**Contenido del `.env`:**

```env
# Clave secreta de Flask (genera una aleatoria)
SECRET_KEY=tu_clave_secreta_super_segura_aqui

# Base de datos (elige una opción)

# Opción A: PostgreSQL (Producción)
DATABASE_URL=postgresql://usuario:password@localhost:5432/horarios_db

# Opción B: SQLite (Desarrollo/Pruebas) - Más simple
# DATABASE_URL=sqlite:///horarios.db
```

**Generar SECRET_KEY segura:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Configurar Base de Datos PostgreSQL (Opcional)

Si usas PostgreSQL:

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Crear base de datos
CREATE DATABASE horarios_db;

# Crear usuario
CREATE USER usuario_horarios WITH PASSWORD 'tu_password';

# Dar permisos
GRANT ALL PRIVILEGES ON DATABASE horarios_db TO usuario_horarios;

# Salir
\q
```

### 3. Inicializar Base de Datos

```bash
# Inicializar migraciones (solo primera vez)
flask db init

# Crear migración inicial
flask db migrate -m "Migración inicial"

# Aplicar migraciones
flask db upgrade
```

---

## 🚀 Ejecución

### Iniciar el Servidor de Desarrollo

```bash
# Asegúrate de tener el entorno virtual activado
# Deberías ver (venv) en la terminal

# Ejecutar aplicación
python run.py
```

**Salida esperada:**

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Abrir la Aplicación

Abre tu navegador en:

```
http://localhost:5000
```

o

```
http://127.0.0.1:5000
```

---

## 📖 Uso del Sistema

### Flujo de Trabajo Completo

#### 1. **Registrar Catálogos Base**

##### a) Crear Grupos

```
Navbar → Catálogos → Grupos
- Nombre: ISC-1A-M
- Turno: MATUTINO
→ Guardar
```

Repetir para ISC-1B-M, ISC-1C-M, etc.

##### b) Crear Materias

```
Navbar → Catálogos → Materias
- Nombre: Fundamentos de Programación
- Turno: MATUTINO
- Bloques por sesión: 2
→ Guardar
```

##### c) Crear Docentes

```
Navbar → Catálogos → Docentes
- Nombre: Dr. Juan Alberto Pérez
- Correo: jperez@upq.edu.mx
- Materias impartibles: [Seleccionar materias]
→ Guardar
```

#### 2. **Configurar Disponibilidad**

```
Navbar → Disponibilidad
- Docente: Dr. Juan Alberto Pérez
- Día: LUNES
- Turno: MATUTINO
- Bloque inicio: 1
- Bloque fin: 8
→ Agregar
```

Repetir para cada día y docente.

#### 3. **Definir Plan de Estudios**

```
Navbar → Plan
- Grupo: ISC-1A-M
- Materia: Fundamentos de Programación
- Sesiones/semana: 3
→ Agregar
```

Repetir para todas las materias de cada grupo.

#### 4. **Crear Reservas (Opcional)**

```
Navbar → Reservas
- Grupo: ISC-1A-M
- Materia: Inglés I
- Día: LUNES
- Turno: MATUTINO
- Bloques: 1-2
→ Agregar
```

#### 5. **Generar Horario**

##### Opción A: Desde Panel Principal

```
1. Ir a Panel (home)
2. Configurar parámetros:
   - Generaciones: 60
   - Población: 40
   - Elite: 6
   - Seed: (opcional)
   - Ámbito: MATUTINO
3. Clic en "Generar"
4. Esperar 30-60 segundos
```

##### Opción B: Desde Experimentos

```
1. Navbar → Experimentos
2. Configurar parámetros
3. Clic en "Ejecutar experimento"
4. Se guardará en historial de experimentos
```

#### 6. **Visualizar Resultados**

##### Ver Horario Lista

```
Navbar → Ver horario
- Muestra tabla con todas las asignaciones
- Grupo, Día, Turno, Bloques, Materia, Docente
```

##### Ver Tablero Visual

```
Navbar → Tablero
- Vista de calendario por grupo
- Seleccionar grupo del dropdown
- Clic en "Cargar"
- Ver horario en cuadrícula
```

##### Ver Experimentos

```
Navbar → Experimentos
- Historial de ejecuciones
- Métricas: Best fitness, Avg fitness, Tiempo
- Gráficas: Fitness, Restricciones
- Comparar múltiples experimentos
```

#### 7. **Exportar Horarios**

```
Tablero → Botón "Exportar a Excel"
- Descarga archivo .xlsx
- Una hoja por grupo
- Formato calendario
```

---

## 📊 Carga de Datos de Prueba

### FASE 1: 3 Grupos del 1er Cuatrimestre

```bash
# Ejecutar script de carga automática
python cargar_datos_isc_fase1.py
```

**Esto carga:**

- 3 grupos: ISC-1A-M, ISC-1B-M, ISC-1C-M
- 7 materias del 1er cuatrimestre ISC-UPQ
- 10 docentes con disponibilidad
- Plan de estudios completo

**Después:**

```bash
# Iniciar aplicación
python run.py

# Ir a http://localhost:5000
# Panel → Generar horario
```

### Crear Más Datos de Prueba

Para **5 grupos** o **9 grupos**, contacta al desarrollador para obtener los scripts correspondientes.

---

## 📁 Estructura del Proyecto

```
ag/
│
├── app/
│   ├── __init__.py              # Inicialización de Flask
│   ├── models.py                # Modelos de base de datos
│   ├── routes.py                # Rutas y controladores
│   ├── genetico.py              # Algoritmo genético
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Estilos personalizados
│   │   └── experimentos/        # Gráficas generadas
│   │
│   └── templates/
│       ├── base.html            # Plantilla base
│       ├── index.html           # Dashboard principal
│       ├── tablero.html         # Visualización de horarios
│       ├── experimentos.html    # Historial de experimentos
│       └── ...                  # Formularios CRUD
│
├── migrations/                  # Migraciones de base de datos
│   └── versions/
│
├── run.py                       # Punto de entrada
├── requirements.txt             # Dependencias
├── .env                         # Variables de entorno (no subir a git)
├── .gitignore                   # Archivos ignorados por git
├── cargar_datos_isc_fase1.py   # Script de carga de datos
└── README.md                    # Este archivo
```

---

## 🔒 Restricciones Implementadas

### Restricciones Duras (Hard Constraints)

| #   | Restricción                     | Penalización | Descripción                                           |
| --- | ------------------------------- | ------------ | ----------------------------------------------------- |
| 1   | **Conflictos de docente**       | 6            | Un docente no puede estar en dos lugares a la vez     |
| 2   | **Violación de reservas**       | 10           | Respetar módulos reservados para materias específicas |
| 3   | **Violación de disponibilidad** | 8            | Docentes solo en sus horarios disponibles             |
| 4   | **Turno incorrecto**            | 4            | Materias en su turno correspondiente                  |
| 5   | **Exceso de sesiones**          | 3/sesión     | No exceder sesiones planificadas por semana           |
| 6   | **Falta de sesiones**           | 3/sesión     | Cumplir sesiones mínimas por semana                   |
| 7   | **Exceso bloques/día**          | 7/bloque     | Máximo 2 bloques por día por materia                  |
| 8   | **Bloques consecutivos**        | 5/bloque     | Máximo 2 bloques consecutivos por materia             |
| 9   | **Horas semanales**             | 10/hora      | Máximo 35 horas por semana por docente                |

**Función objetivo:** Minimizar penalizaciones (fitness negativo)

**Óptimo:** Fitness = 0 (sin violaciones)

---

## 🛠️ Tecnologías

### Backend

- **Flask 2.3+** - Framework web
- **SQLAlchemy 2.0+** - ORM
- **PostgreSQL 12+** - Base de datos (producción)
- **SQLite** - Base de datos (desarrollo)
- **Flask-Migrate** - Migraciones

### Frontend

- **Bootstrap 5.3** - Framework CSS
- **JavaScript (Vanilla)** - Interactividad
- **Jinja2** - Motor de plantillas

### Algoritmo Genético

- **Python 3.8+** - Lenguaje base
- **Random** - Generación aleatoria
- **Collections** - Estructuras de datos

### Visualización

- **Matplotlib 3.8+** - Gráficas
- **HTML Canvas** - Tablero visual

### Exportación

- **openpyxl 3.1+** - Archivos Excel

---

## 🗺️ Roadmap

### ✅ Completado

- [x] Algoritmo genético básico
- [x] 9 restricciones implementadas
- [x] Interfaz web funcional
- [x] Sistema de experimentos
- [x] Visualización de horarios
- [x] Exportación a Excel
- [x] Migración a PostgreSQL

### 🚧 En Progreso

- [ ] Dashboard de validación pre-ejecución
- [ ] Indicadores de progreso en tiempo real
- [ ] Mejoras UX/UI (Fase 1)

### 📋 Por Hacer

- [ ] Pruebas con 5 grupos
- [ ] Pruebas con 9 grupos
- [ ] Pruebas con múltiples cuatrimestres
- [ ] Sistema de usuarios y roles
- [ ] API REST
- [ ] Exportación a PDF
- [ ] Sincronización con Google Calendar
- [ ] Modo comparación de experimentos
- [ ] Reportes analíticos avanzados

---

## 🤝 Contribuir

### Reportar Bugs

Si encuentras un error:

1. Ve a [Issues](https://github.com/BOWadapter/ag/issues)
2. Crea un nuevo issue
3. Describe el problema detalladamente
4. Incluye pasos para reproducir

### Solicitar Funcionalidades

1. Ve a [Issues](https://github.com/BOWadapter/ag/issues)
2. Usa la etiqueta "enhancement"
3. Describe la funcionalidad deseada

### Pull Requests

1. Fork del repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es software académico desarrollado como tesis de grado.

**Universidad Politécnica de Querétaro (UPQ)**  
Ingeniería en Sistemas Computacionales

---

## 👤 Autor

**Desarrollador:** [Tu Nombre]  
**Asesor:** [Nombre del Asesor]  
**Universidad:** Universidad Politécnica de Querétaro  
**Año:** 2025

---

## 📞 Contacto y Soporte

- **GitHub Issues:** [https://github.com/BOWadapter/ag/issues](https://github.com/BOWadapter/ag/issues)
- **Email:** [tu_email@upq.edu.mx]

---

## 🙏 Agradecimientos

- Universidad Politécnica de Querétaro
- Profesores y asesores del programa ISC
- Comunidad de código abierto de Flask y SQLAlchemy

---

## 📚 Referencias

1. Holland, J. H. (1992). Adaptation in Natural and Artificial Systems
2. Goldberg, D. E. (1989). Genetic Algorithms in Search, Optimization, and Machine Learning
3. Even, S., Itai, A., & Shamir, A. (1976). On the Complexity of Timetable and Multicommodity Flow Problems

---

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub**

---

_Última actualización: Noviembre 2025_
