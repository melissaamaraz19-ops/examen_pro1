from . import db
from enum import Enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime

DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]

class Turno(Enum):
    MATUTINO = "MATUTINO"
    VESPERTINO = "VESPERTINO"

class Docente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120))
    materias_impartibles = db.relationship("DocenteMateria", backref="docente", cascade="all, delete-orphan")

class Materia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(140), nullable=False, unique=True)
    turno = db.Column(SAEnum(Turno, name="turno"), nullable=False)
    bloques_duracion = db.Column(db.Integer, default=2)

class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    turno = db.Column(SAEnum(Turno, name="turno"), nullable=False)

class DocenteMateria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey("docente.id"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materia.id"), nullable=False)

class Disponibilidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey("docente.id"), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    turno = db.Column(SAEnum(Turno, name="turno"), nullable=False)
    bloque_inicio = db.Column(db.Integer, nullable=False)
    bloque_fin = db.Column(db.Integer, nullable=False)
    docente = db.relationship("Docente")

class MateriaGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materia.id"), nullable=False)
    sesiones_por_semana = db.Column(db.Integer, nullable=False, default=1)
    grupo = db.relationship("Grupo")
    materia = db.relationship("Materia")

class ReservaModulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materia.id"), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    turno = db.Column(SAEnum(Turno, name="turno"), nullable=False)
    bloque_inicio = db.Column(db.Integer, nullable=False)
    bloque_fin = db.Column(db.Integer, nullable=False)
    grupo = db.relationship("Grupo")
    materia = db.relationship("Materia")

class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materia.id"), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey("docente.id"), nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    turno = db.Column(SAEnum(Turno, name="turno"), nullable=False)
    bloque_inicio = db.Column(db.Integer, nullable=False)
    bloque_fin = db.Column(db.Integer, nullable=False)
    grupo = db.relationship("Grupo")
    materia = db.relationship("Materia")
    docente = db.relationship("Docente")

class Experimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    scope = db.Column(db.String(20))
    generaciones = db.Column(db.Integer)
    poblacion = db.Column(db.Integer)
    elite = db.Column(db.Integer)
    seed = db.Column(db.Integer, nullable=True)
    num_grupos_total = db.Column(db.Integer, default=0)
    num_grupos_m = db.Column(db.Integer, default=0)
    num_grupos_v = db.Column(db.Integer, default=0)
    best_final = db.Column(db.Float, default=0.0)
    avg_final = db.Column(db.Float, default=0.0)
    tiempo_total = db.Column(db.Float, default=0.0)
    conflictos_docente = db.Column(db.Integer, default=0)
    violacion_reserva = db.Column(db.Integer, default=0)
    violacion_disponibilidad = db.Column(db.Integer, default=0)
    turno_incorrecto = db.Column(db.Integer, default=0)
    exceso_sesiones = db.Column(db.Integer, default=0)
    falta_sesiones = db.Column(db.Integer, default=0)
    exceso_bloques_dia = db.Column(db.Integer, default=0)
    exceso_bloques_consecutivos = db.Column(db.Integer, default=0)
    exceso_horas_semanales = db.Column(db.Integer, default=0)
    fig_fitness = db.Column(db.String(255))
    fig_hard = db.Column(db.String(255))
    log_json = db.Column(db.Text)