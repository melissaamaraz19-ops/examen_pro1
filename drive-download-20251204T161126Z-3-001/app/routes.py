import os, json, io
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from sqlalchemy import func
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import defaultdict
import pandas as pd

from . import db
from .models import (
    Turno, Docente, Materia, DocenteMateria, Disponibilidad,
    Grupo, MateriaGrupo, ReservaModulo, Horario, DIAS, Experimento
)
from .genetico import generar_horario, get_ga_log

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

bp = Blueprint("main", __name__)

# ===================== RUTAS ORIGINALES =====================

# ---------------------- HOME ----------------------
@bp.route("/")
def index():
    c_doc = db.session.query(func.count(Docente.id)).scalar()
    c_mat = db.session.query(func.count(Materia.id)).scalar()
    c_grp = db.session.query(func.count(Grupo.id)).scalar()
    c_map = db.session.query(func.count(DocenteMateria.id)).scalar()
    c_disp = db.session.query(func.count(Disponibilidad.id)).scalar()
    c_plan = db.session.query(func.count(MateriaGrupo.id)).scalar()
    return render_template("index.html",
                           c_doc=c_doc, c_mat=c_mat, c_grp=c_grp,
                           c_map=c_map, c_disp=c_disp, c_plan=c_plan)

@bp.route("/generar", methods=["POST"])
def generar():
    gens  = int(request.form.get("gens", 60))
    tam   = int(request.form.get("tam", 40))
    elite = int(request.form.get("elite", 6))
    seed  = request.form.get("seed")
    scope = request.form.get("scope", "BOTH")
    turnos = [Turno.MATUTINO, Turno.VESPERTINO]
    if scope == "MATUTINO": turnos = [Turno.MATUTINO]
    if scope == "VESPERTINO": turnos = [Turno.VESPERTINO]

    generar_horario(
        generaciones=gens, tam=tam, elite=elite,
        seed=int(seed) if (seed and seed.isdigit()) else None,
        turnos=turnos, verbose=True, max_seconds=60, early_stop=12
    )
    flash("Horario generado.", "success")
    return redirect(url_for("main.ver_horario"))

# ---------------------- DOCENTES ----------------------
@bp.route("/docente/nuevo", methods=["GET","POST"])
def docente_nuevo():
    materias = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        d = Docente(nombre=request.form["nombre"].strip(),
                    correo=(request.form.get("correo","").strip() or None))
        db.session.add(d); db.session.commit()
        for mid in request.form.getlist("materias"):
            db.session.add(DocenteMateria(docente_id=d.id, materia_id=int(mid)))
        db.session.commit()
        flash("Docente creado.", "success")
        return redirect(url_for("main.docente_nuevo"))
    docentes = Docente.query.order_by(Docente.nombre).all()
    return render_template("docente_form.html", materias=materias, docentes=docentes)

@bp.route("/docente/<int:id>/editar", methods=["GET","POST"])
def docente_editar(id):
    d = Docente.query.get_or_404(id)
    materias = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        d.nombre = request.form["nombre"].strip()
        d.correo = request.form.get("correo","").strip() or None
        DocenteMateria.query.filter_by(docente_id=d.id).delete()
        for mid in request.form.getlist("materias"):
            db.session.add(DocenteMateria(docente_id=d.id, materia_id=int(mid)))
        db.session.commit()
        flash("Docente actualizado.", "success")
        return redirect(url_for("main.docente_nuevo"))
    impartibles = {dm.materia_id for dm in d.materias_impartibles}
    return render_template("docente_edit.html", docente=d, materias=materias, impartibles=impartibles)

@bp.route("/docente/<int:id>/borrar")
def docente_borrar(id):
    DocenteMateria.query.filter_by(docente_id=id).delete()
    Disponibilidad.query.filter_by(docente_id=id).delete()
    Horario.query.filter_by(docente_id=id).delete()
    Docente.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Docente eliminado.", "success")
    return redirect(url_for("main.docente_nuevo"))

# ---------------------- MATERIAS ----------------------
@bp.route("/materia/nueva", methods=["GET","POST"])
def materia_nueva():
    if request.method == "POST":
        m = Materia(
            nombre=request.form["nombre"].strip(),
            turno=Turno(request.form["turno"]),
            bloques_duracion=int(request.form.get("bloques_duracion",2))
        )
        db.session.add(m); db.session.commit()
        flash("Materia creada.", "success")
        return redirect(url_for("main.materia_nueva"))
    mats = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    return render_template("materia_form.html", materias=mats)

@bp.route("/materia/<int:id>/editar", methods=["GET","POST"])
def materia_editar(id):
    m = Materia.query.get_or_404(id)
    if request.method == "POST":
        m.nombre = request.form["nombre"].strip()
        m.turno = Turno(request.form["turno"])
        m.bloques_duracion = int(request.form.get("bloques_duracion",2))
        db.session.commit()
        flash("Materia actualizada.", "success")
        return redirect(url_for("main.materia_nueva"))
    return render_template("materia_edit.html", materia=m)

@bp.route("/materia/<int:id>/borrar")
def materia_borrar(id):
    DocenteMateria.query.filter_by(materia_id=id).delete()
    MateriaGrupo.query.filter_by(materia_id=id).delete()
    ReservaModulo.query.filter_by(materia_id=id).delete()
    Horario.query.filter_by(materia_id=id).delete()
    Materia.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Materia eliminada.", "success")
    return redirect(url_for("main.materia_nueva"))

# ---------------------- GRUPOS ----------------------
@bp.route("/grupo/nuevo", methods=["GET","POST"])
def grupo_nuevo():
    if request.method == "POST":
        g = Grupo(nombre=request.form["nombre"].strip(), turno=Turno(request.form["turno"]))
        db.session.add(g); db.session.commit()
        flash("Grupo creado.", "success")
        return redirect(url_for("main.grupo_nuevo"))
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    return render_template("grupo_form.html", grupos=grupos)

@bp.route("/grupo/<int:id>/editar", methods=["GET","POST"])
def grupo_editar(id):
    g = Grupo.query.get_or_404(id)
    if request.method == "POST":
        g.nombre = request.form["nombre"].strip()
        g.turno = Turno(request.form["turno"])
        db.session.commit()
        flash("Grupo actualizado.", "success")
        return redirect(url_for("main.grupo_nuevo"))
    return render_template("grupo_edit.html", grupo=g)

@bp.route("/grupo/<int:id>/borrar")
def grupo_borrar(id):
    MateriaGrupo.query.filter_by(grupo_id=id).delete()
    ReservaModulo.query.filter_by(grupo_id=id).delete()
    Horario.query.filter_by(grupo_id=id).delete()
    Grupo.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Grupo eliminado.", "success")
    return redirect(url_for("main.grupo_nuevo"))

# ---------------------- DISPONIBILIDAD ----------------------
@bp.route("/disponibilidad", methods=["GET","POST"])
def disponibilidad():
    docentes = Docente.query.order_by(Docente.nombre).all()
    if request.method == "POST":
        db.session.add(Disponibilidad(
            docente_id=int(request.form["docente_id"]),
            dia=request.form["dia"],
            turno=Turno(request.form["turno"]),
            bloque_inicio=int(request.form["b1"]),
            bloque_fin=int(request.form["b2"])
        ))
        db.session.commit()
        flash("Disponibilidad agregada.", "success")
        return redirect(url_for("main.disponibilidad"))
    disp = (Disponibilidad.query
            .join(Docente, Disponibilidad.docente_id == Docente.id)
            .order_by(Docente.nombre, Disponibilidad.dia, Disponibilidad.turno)
            .all())
    return render_template("disponibilidad_form.html", docentes=docentes, disp=disp)

@bp.route("/disponibilidad/<int:id>/editar", methods=["GET","POST"])
def disponibilidad_editar(id):
    r = Disponibilidad.query.get_or_404(id)
    docentes = Docente.query.order_by(Docente.nombre).all()
    if request.method == "POST":
        r.docente_id = int(request.form["docente_id"])
        r.dia = request.form["dia"]
        r.turno = Turno(request.form["turno"])
        r.bloque_inicio = int(request.form["b1"])
        r.bloque_fin = int(request.form["b2"])
        db.session.commit()
        flash("Disponibilidad actualizada.", "success")
        return redirect(url_for("main.disponibilidad"))
    return render_template("disponibilidad_edit.html", disp=r, docentes=docentes)

@bp.route("/disponibilidad/<int:id>/borrar")
def disponibilidad_borrar(id):
    Disponibilidad.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Disponibilidad eliminada.", "success")
    return redirect(url_for("main.disponibilidad"))

# ---------------------- PLAN (MateriaGrupo) ----------------------
@bp.route("/plan", methods=["GET","POST"])
def plan_grupo():
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    mats = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        db.session.add(MateriaGrupo(
            grupo_id=int(request.form["grupo_id"]),
            materia_id=int(request.form["materia_id"]),
            sesiones_por_semana=int(request.form["sesiones"])
        ))
        db.session.commit()
        flash("Plan agregado.", "success")
        return redirect(url_for("main.plan_grupo"))
    planes = (MateriaGrupo.query
              .join(Grupo, MateriaGrupo.grupo_id==Grupo.id)
              .join(Materia, MateriaGrupo.materia_id==Materia.id)
              .order_by(Grupo.nombre, Materia.nombre)
              .all())
    return render_template("plan_form.html", grupos=grupos, materias=mats, planes=planes)

@bp.route("/plan/<int:id>/editar", methods=["GET","POST"])
def plan_editar(id):
    p = MateriaGrupo.query.get_or_404(id)
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    materias = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        p.grupo_id = int(request.form["grupo_id"])
        p.materia_id = int(request.form["materia_id"])
        p.sesiones_por_semana = int(request.form["sesiones"])
        db.session.commit()
        flash("Plan actualizado.", "success")
        return redirect(url_for("main.plan_grupo"))
    return render_template("plan_edit.html", plan=p, grupos=grupos, materias=materias)

@bp.route("/plan/<int:id>/borrar")
def plan_borrar(id):
    MateriaGrupo.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Elemento del plan eliminado.", "success")
    return redirect(url_for("main.plan_grupo"))

# ---------------------- RESERVAS ----------------------
@bp.route("/reservas", methods=["GET","POST"])
def reservas():
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    mats = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        db.session.add(ReservaModulo(
            grupo_id=int(request.form["grupo_id"]),
            materia_id=int(request.form["materia_id"]),
            dia=request.form["dia"],
            turno=Turno(request.form["turno"]),
            bloque_inicio=int(request.form["b1"]),
            bloque_fin=int(request.form["b2"])
        ))
        db.session.commit()
        flash("Reserva creada.", "success")
        return redirect(url_for("main.reservas"))
    res = (ReservaModulo.query
           .join(Grupo, ReservaModulo.grupo_id==Grupo.id)
           .join(Materia, ReservaModulo.materia_id==Materia.id)
           .order_by(Grupo.nombre, ReservaModulo.dia, ReservaModulo.turno)
           .all())
    return render_template("reserva_form.html", grupos=grupos, materias=mats, reservas=res)

@bp.route("/reservas/<int:id>/editar", methods=["GET","POST"])
def reservas_editar(id):
    r = ReservaModulo.query.get_or_404(id)
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    materias = Materia.query.order_by(Materia.turno, Materia.nombre).all()
    if request.method == "POST":
        r.grupo_id = int(request.form["grupo_id"])
        r.materia_id = int(request.form["materia_id"])
        r.dia = request.form["dia"]
        r.turno = Turno(request.form["turno"])
        r.bloque_inicio = int(request.form["b1"])
        r.bloque_fin = int(request.form["b2"])
        db.session.commit()
        flash("Reserva actualizada.", "success")
        return redirect(url_for("main.reservas"))
    return render_template("reserva_edit.html", reserva=r, grupos=grupos, materias=materias)

@bp.route("/reservas/<int:id>/borrar")
def reservas_borrar(id):
    ReservaModulo.query.filter_by(id=id).delete()
    db.session.commit()
    flash("Reserva eliminada.", "success")
    return redirect(url_for("main.reservas"))

# ---------------------- VISUALIZACIÓN ----------------------
@bp.route("/ver_horario")
def ver_horario():
    q = (db.session.query(Horario, Materia, Docente, Grupo)
         .join(Materia, Horario.materia_id==Materia.id)
         .join(Docente, Horario.docente_id==Docente.id)
         .join(Grupo, Horario.grupo_id==Grupo.id)
         .order_by(Grupo.nombre, Horario.dia, Horario.bloque_inicio))
    data = [{
        "grupo": g.nombre, "dia": h.dia, "turno": h.turno.value,
        "bloque": f"{h.bloque_inicio}-{h.bloque_fin}",
        "materia": m.nombre, "docente": d.nombre
    } for h,m,d,g in q.all()]
    return render_template("horario_list.html", data=data)

@bp.route("/tablero")
def tablero():
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    return render_template("tablero.html", grupos=grupos, DIAS=DIAS)

@bp.route("/tablero/data")
def tablero_data():
    grupo_id = int(request.args.get("grupo_id"))
    g = Grupo.query.get_or_404(grupo_id)
    rows = (Horario.query.filter_by(grupo_id=grupo_id)
            .order_by(Horario.dia, Horario.bloque_inicio).all())
    out = []
    for h in rows:
        m = Materia.query.get(h.materia_id)
        d = Docente.query.get(h.docente_id)
        out.append(dict(dia=h.dia, turno=h.turno.value,
                        b1=h.bloque_inicio, b2=h.bloque_fin,
                        materia=m.nombre, docente=d.nombre))
    return jsonify({"grupo": g.nombre, "turno": g.turno.value, "items": out})

# ---------------------- EXPERIMENTOS ----------------------
def _ensure_dir(path): os.makedirs(path, exist_ok=True)

def _save_fig_to_static(fig, rel_path):
    static_root = os.path.join(os.path.dirname(__file__), "static")
    full_dir = os.path.join(static_root, os.path.dirname(rel_path))
    _ensure_dir(full_dir)
    fig.savefig(os.path.join(static_root, rel_path), bbox_inches="tight")
    plt.close(fig)

@bp.route("/experimentos", methods=["GET"])
def experimentos():
    rows = Experimento.query.order_by(Experimento.creado_en.desc()).all()
    return render_template("experimentos.html", rows=rows)

@bp.route("/experimentos/run", methods=["POST"])
def experimentos_run():
    gens  = int(request.form.get("gens", 60))
    tam   = int(request.form.get("tam", 40))
    elite = int(request.form.get("elite", 6))
    seed  = request.form.get("seed")
    scope = request.form.get("scope", "BOTH")
    turnos = [Turno.MATUTINO, Turno.VESPERTINO]
    if scope == "MATUTINO": turnos = [Turno.MATUTINO]
    if scope == "VESPERTINO": turnos = [Turno.VESPERTINO]

    gm = Grupo.query.filter_by(turno=Turno.MATUTINO).count()
    gv = Grupo.query.filter_by(turno=Turno.VESPERTINO).count()
    total = gm + gv if scope == "BOTH" else (gm if scope == "MATUTINO" else gv)

    generar_horario(
        generaciones=gens, tam=tam, elite=elite,
        seed=int(seed) if (seed and seed.isdigit()) else None,
        turnos=turnos, verbose=True, max_seconds=60, early_stop=12
    )

    log = get_ga_log()
    if not log:
        flash("No se obtuvieron datos del GA_LOG.", "error")
        return redirect(url_for("main.experimentos"))

    last = log[-1]
    best_final = float(last.get("best", 0))
    avg_final  = float(last.get("avg", 0))
    tiempo     = float(last.get("time_sec", 0))
    comp_last  = last.get("comp") or {}

    exp = Experimento(
        scope=scope, generaciones=gens, poblacion=tam, elite=elite,
        seed=int(seed) if (seed and seed.isdigit()) else None,
        num_grupos_total=total, num_grupos_m=gm, num_grupos_v=gv,
        best_final=best_final, avg_final=avg_final, tiempo_total=tiempo,
        conflictos_docente=int(comp_last.get("conflictos_docente", 0)),
        violacion_reserva=int(comp_last.get("violacion_reserva", 0)),
        violacion_disponibilidad=int(comp_last.get("violacion_disponibilidad", 0)),
        turno_incorrecto=int(comp_last.get("turno_incorrecto", 0)),
        exceso_sesiones=int(comp_last.get("exceso_sesiones", 0)),
        falta_sesiones=int(comp_last.get("falta_sesiones", 0)),
        log_json=json.dumps(log, ensure_ascii=False)
    )
    db.session.add(exp); db.session.commit()

    # Fitness
    gens_x = [e.get("generacion", i+1) for i, e in enumerate(log)]
    best_y = [float(e.get("best", 0)) for e in log]
    avg_y  = [float(e.get("avg", 0)) for e in log]

    fig1, ax1 = plt.subplots(figsize=(6,3))
    ax1.plot(gens_x, best_y, label="Best")
    ax1.plot(gens_x, avg_y,  label="Avg")
    ax1.set_title(f"Fitness (Exp {exp.id})")
    ax1.set_xlabel("Generación"); ax1.set_ylabel("Fitness")
    ax1.legend()
    rel1 = f"experimentos/exp_{exp.id}_fitness.png"
    _save_fig_to_static(fig1, rel1)

    # Restricciones
    keys = [
        "conflictos_docente","violacion_reserva","violacion_disponibilidad",
        "turno_incorrecto","exceso_sesiones","falta_sesiones",
        "exceso_bloques_dia"
    ]
    series = {k:[] for k in keys}
    for e in log:
        comp = e.get("comp") or {}
        for k in keys:
            series[k].append(float(comp.get(k, 0)))

    fig2, ax2 = plt.subplots(figsize=(6,3))
    hubo_algo = False
    for k in keys:
        if any(v != 0 for v in series[k]):
            ax2.plot(gens_x, series[k], label=k.replace("_"," "))
            hubo_algo = True
    if not hubo_algo:
        ax2.text(0.5, 0.5, "Sin violaciones registradas",
                 ha='center', va='center', transform=ax2.transAxes, color="gray")
    ax2.set_title(f"Restricciones (Exp {exp.id})")
    ax2.set_xlabel("Generación"); ax2.set_ylabel("Conteo")
    ax2.legend(fontsize="x-small", ncol=2)
    rel2 = f"experimentos/exp_{exp.id}_hard.png"
    _save_fig_to_static(fig2, rel2)

    exp.fig_fitness = rel1; exp.fig_hard = rel2
    db.session.commit()

    flash(f"Experimento {exp.id} ejecutado y graficado.", "success")
    return redirect(url_for("main.experimentos"))

@bp.route("/experimentos/<int:exp_id>/borrar", methods=["POST", "GET"])
def experimentos_borrar(exp_id):
    exp = Experimento.query.get_or_404(exp_id)

    def _try_remove(relpath):
        if not relpath:
            return
        static_root = os.path.join(os.path.dirname(__file__), "static")
        full = os.path.join(static_root, relpath)
        try:
            if os.path.exists(full):
                os.remove(full)
        except Exception:
            pass

    _try_remove(getattr(exp, "fig_fitness", None))
    _try_remove(getattr(exp, "fig_hard", None))

    db.session.delete(exp)
    db.session.commit()
    flash(f"Experimento {exp_id} eliminado.", "success")
    return redirect(url_for("main.experimentos"))


# ===================== NUEVAS FUNCIONALIDADES - 6 MEJORAS =====================

# ---------------------- MEJORA #1: IMPORTACIÓN MASIVA ----------------------
@bp.route("/importar", methods=["GET", "POST"])
def importar():
    """Importación masiva desde Excel"""
    if request.method == "POST":
        try:
            archivo = request.files.get('archivo')
            tipo = request.form.get('tipo')
            limpiar_antes = request.form.get('limpiar_antes') == 'on'
            
            if not archivo or not archivo.filename.endswith(('.xlsx', '.xls')):
                flash("Por favor sube un archivo Excel válido (.xlsx, .xls)", "error")
                return redirect(url_for('main.importar'))
            
            # Limpiar datos si se solicitó
            if limpiar_antes:
                _limpiar_datos_tipo(tipo)
            
            # Leer Excel
            df = pd.read_excel(archivo)
            
            # Procesar según tipo
            if tipo == 'materias':
                count = _importar_materias(df)
            elif tipo == 'docentes':
                count = _importar_docentes(df)
            elif tipo == 'grupos':
                count = _importar_grupos(df)
            elif tipo == 'disponibilidad':
                count = _importar_disponibilidad(df)
            elif tipo == 'plan':
                count = _importar_plan(df)
            elif tipo == 'completo':
                count = _importar_completo(archivo)
            else:
                flash("Tipo de importación no válido", "error")
                return redirect(url_for('main.importar'))
            
            flash(f"✅ Importados {count} registros correctamente", "success")
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f"❌ Error al importar: {str(e)}", "error")
            return redirect(url_for('main.importar'))
    
    return render_template("importar.html")

def _limpiar_datos_tipo(tipo):
    """Limpia datos según el tipo"""
    if tipo in ['materias', 'completo']:
        Materia.query.delete()
    if tipo in ['docentes', 'completo']:
        DocenteMateria.query.delete()
        Docente.query.delete()
    if tipo in ['grupos', 'completo']:
        Grupo.query.delete()
    if tipo in ['disponibilidad', 'completo']:
        Disponibilidad.query.delete()
    if tipo in ['plan', 'completo']:
        MateriaGrupo.query.delete()
    db.session.commit()

def _importar_materias(df):
    """Importa materias desde DataFrame"""
    count = 0
    for _, row in df.iterrows():
        m = Materia(
            nombre=str(row['nombre']).strip(),
            turno=Turno[str(row['turno']).upper()],
            bloques_duracion=int(row.get('bloques_duracion', 2))
        )
        db.session.add(m)
        count += 1
    db.session.commit()
    return count

def _importar_docentes(df):
    """Importa docentes con sus materias"""
    count = 0
    for _, row in df.iterrows():
        d = Docente(
            nombre=str(row['nombre']).strip(),
            correo=str(row.get('correo', '')).strip() or None
        )
        db.session.add(d)
        db.session.flush()
        
        # Materias impartibles
        if 'materias' in row and pd.notna(row['materias']):
            materias_nombres = [m.strip() for m in str(row['materias']).split(';')]
            for mat_nombre in materias_nombres:
                materia = Materia.query.filter_by(nombre=mat_nombre).first()
                if materia:
                    db.session.add(DocenteMateria(docente_id=d.id, materia_id=materia.id))
        count += 1
    db.session.commit()
    return count

def _importar_grupos(df):
    """Importa grupos"""
    count = 0
    for _, row in df.iterrows():
        g = Grupo(
            nombre=str(row['nombre']).strip(),
            turno=Turno[str(row['turno']).upper()]
        )
        db.session.add(g)
        count += 1
    db.session.commit()
    return count

def _importar_disponibilidad(df):
    """Importa disponibilidad de docentes"""
    count = 0
    for _, row in df.iterrows():
        docente = Docente.query.filter_by(nombre=str(row['docente']).strip()).first()
        if docente:
            d = Disponibilidad(
                docente_id=docente.id,
                dia=str(row['dia']).upper(),
                turno=Turno[str(row['turno']).upper()],
                bloque_inicio=int(row['bloque_inicio']),
                bloque_fin=int(row['bloque_fin'])
            )
            db.session.add(d)
            count += 1
    db.session.commit()
    return count

def _importar_plan(df):
    """Importa plan de estudios (MateriaGrupo)"""
    count = 0
    for _, row in df.iterrows():
        grupo = Grupo.query.filter_by(nombre=str(row['grupo']).strip()).first()
        materia = Materia.query.filter_by(nombre=str(row['materia']).strip()).first()
        
        if grupo and materia:
            p = MateriaGrupo(
                grupo_id=grupo.id,
                materia_id=materia.id,
                sesiones_por_semana=int(row['sesiones_por_semana'])
            )
            db.session.add(p)
            count += 1
    db.session.commit()
    return count

def _importar_completo(archivo):
    """Importa desde un archivo Excel con múltiples hojas"""
    xl = pd.ExcelFile(archivo)
    total = 0
    
    if 'Materias' in xl.sheet_names:
        total += _importar_materias(pd.read_excel(xl, 'Materias'))
    if 'Docentes' in xl.sheet_names:
        total += _importar_docentes(pd.read_excel(xl, 'Docentes'))
    if 'Grupos' in xl.sheet_names:
        total += _importar_grupos(pd.read_excel(xl, 'Grupos'))
    if 'Disponibilidad' in xl.sheet_names:
        total += _importar_disponibilidad(pd.read_excel(xl, 'Disponibilidad'))
    if 'Plan' in xl.sheet_names:
        total += _importar_plan(pd.read_excel(xl, 'Plan'))
    
    return total

@bp.route("/descargar_plantilla")
def descargar_plantilla():
    """Genera y descarga plantilla Excel"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    
    # Hoja Materias
    pd.DataFrame({
        'nombre': ['Inglés I', 'Valores del Ser', 'Herramientas Ofimáticas'],
        'turno': ['MATUTINO', 'MATUTINO', 'MATUTINO'],
        'bloques_duracion': [2, 2, 2]
    }).to_excel(writer, sheet_name='Materias', index=False)
    
    # Hoja Docentes
    pd.DataFrame({
        'nombre': ['Dr. Juan Pérez', 'Mtra. María López'],
        'correo': ['juan@ejemplo.com', 'maria@ejemplo.com'],
        'materias': ['Inglés I;Herramientas Ofimáticas', 'Valores del Ser']
    }).to_excel(writer, sheet_name='Docentes', index=False)
    
    # Hoja Grupos
    pd.DataFrame({
        'nombre': ['1A', '1B', '1C'],
        'turno': ['MATUTINO', 'MATUTINO', 'MATUTINO']
    }).to_excel(writer, sheet_name='Grupos', index=False)
    
    # Hoja Disponibilidad
    pd.DataFrame({
        'docente': ['Dr. Juan Pérez', 'Dr. Juan Pérez'],
        'dia': ['LUNES', 'MARTES'],
        'turno': ['MATUTINO', 'MATUTINO'],
        'bloque_inicio': [1, 1],
        'bloque_fin': [8, 8]
    }).to_excel(writer, sheet_name='Disponibilidad', index=False)
    
    # Hoja Plan
    pd.DataFrame({
        'grupo': ['1A', '1A', '1A'],
        'materia': ['Inglés I', 'Valores del Ser', 'Herramientas Ofimáticas'],
        'sesiones_por_semana': [2, 2, 2]
    }).to_excel(writer, sheet_name='Plan', index=False)
    
    writer.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'plantilla_horarios_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# ---------------------- MEJORA #2: VALIDACIÓN PRE-GA ----------------------
@bp.route("/validar")
def validar():
    """Página de validación"""
    return render_template("validar.html")

@bp.route("/api/validar")
def api_validar():
    """API de validación del sistema"""
    resultado = {
        'valido': True,
        'total_issues': 0,
        'docentes': {'ok': [], 'issues': []},
        'materias': {'ok': [], 'issues': []},
        'grupos': {'ok': [], 'issues': []},
        'disponibilidad': {'ok': [], 'issues': []},
        'plan': {'ok': [], 'issues': []},
        'reservas': {'ok': [], 'issues': []}
    }
    
    # Validar Docentes
    total_docentes = Docente.query.count()
    if total_docentes == 0:
        resultado['docentes']['issues'].append("No hay docentes registrados")
        resultado['valido'] = False
    else:
        resultado['docentes']['ok'].append(f"{total_docentes} docentes registrados")
        
        # Docentes sin materias
        docentes_sin_materias = []
        for d in Docente.query.all():
            if DocenteMateria.query.filter_by(docente_id=d.id).count() == 0:
                docentes_sin_materias.append(d.nombre)
        
        if docentes_sin_materias:
            resultado['docentes']['issues'].append(
                f"{len(docentes_sin_materias)} docentes sin materias asignadas: {', '.join(docentes_sin_materias[:3])}"
            )
    
    # Validar Materias
    total_materias = Materia.query.count()
    if total_materias == 0:
        resultado['materias']['issues'].append("No hay materias registradas")
        resultado['valido'] = False
    else:
        resultado['materias']['ok'].append(f"{total_materias} materias registradas")
        
        # Materias sin docentes
        materias_sin_docentes = []
        for m in Materia.query.all():
            if DocenteMateria.query.filter_by(materia_id=m.id).count() == 0:
                materias_sin_docentes.append(m.nombre)
        
        if materias_sin_docentes:
            resultado['materias']['issues'].append(
                f"{len(materias_sin_docentes)} materias sin docentes: {', '.join(materias_sin_docentes[:3])}"
            )
    
    # Validar Grupos
    total_grupos = Grupo.query.count()
    if total_grupos == 0:
        resultado['grupos']['issues'].append("No hay grupos registrados")
        resultado['valido'] = False
    else:
        resultado['grupos']['ok'].append(f"{total_grupos} grupos registrados")
        matutinos = Grupo.query.filter_by(turno=Turno.MATUTINO).count()
        vespertinos = Grupo.query.filter_by(turno=Turno.VESPERTINO).count()
        resultado['grupos']['ok'].append(f"Matutinos: {matutinos}, Vespertinos: {vespertinos}")
    
    # Validar Disponibilidad
    total_disp = Disponibilidad.query.count()
    if total_disp == 0:
        resultado['disponibilidad']['issues'].append("No hay disponibilidades registradas")
        resultado['valido'] = False
    else:
        resultado['disponibilidad']['ok'].append(f"{total_disp} registros de disponibilidad")
        
        # Docentes sin disponibilidad
        docentes_sin_disp = []
        for d in Docente.query.all():
            if Disponibilidad.query.filter_by(docente_id=d.id).count() == 0:
                docentes_sin_disp.append(d.nombre)
        
        if docentes_sin_disp:
            resultado['disponibilidad']['issues'].append(
                f"{len(docentes_sin_disp)} docentes sin disponibilidad: {', '.join(docentes_sin_disp[:3])}"
            )
    
    # Validar Plan
    total_plan = MateriaGrupo.query.count()
    if total_plan == 0:
        resultado['plan']['issues'].append("No hay plan de estudios configurado")
        resultado['valido'] = False
    else:
        resultado['plan']['ok'].append(f"{total_plan} asignaciones materia-grupo")
        
        # Grupos sin plan
        grupos_sin_plan = []
        for g in Grupo.query.all():
            if MateriaGrupo.query.filter_by(grupo_id=g.id).count() == 0:
                grupos_sin_plan.append(g.nombre)
        
        if grupos_sin_plan:
            resultado['plan']['issues'].append(
                f"{len(grupos_sin_plan)} grupos sin plan: {', '.join(grupos_sin_plan)}"
            )
            resultado['valido'] = False
    
    # Validar Reservas (opcional)
    total_reservas = ReservaModulo.query.count()
    if total_reservas > 0:
        resultado['reservas']['ok'].append(f"{total_reservas} reservas de módulos configuradas")
    else:
        resultado['reservas']['ok'].append("Sin reservas (opcional)")
    
    # Contar issues totales
    for categoria in ['docentes', 'materias', 'grupos', 'disponibilidad', 'plan', 'reservas']:
        resultado['total_issues'] += len(resultado[categoria]['issues'])
    
    if resultado['total_issues'] > 0:
        resultado['valido'] = False
    
    return jsonify(resultado)

# ---------------------- MEJORA #4: EXPORTACIÓN ----------------------
@bp.route("/exportar/excel")
def exportar_excel():
    """Exporta horarios a Excel"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    
    # Obtener horarios
    horarios = db.session.query(Horario, Materia, Docente, Grupo)\
        .join(Materia, Horario.materia_id==Materia.id)\
        .join(Docente, Horario.docente_id==Docente.id)\
        .join(Grupo, Horario.grupo_id==Grupo.id)\
        .order_by(Grupo.nombre, Horario.dia, Horario.bloque_inicio).all()
    
    # Crear DataFrame
    data = []
    for h, m, d, g in horarios:
        data.append({
            'Grupo': g.nombre,
            'Turno': g.turno.value,
            'Día': h.dia,
            'Bloque Inicio': h.bloque_inicio,
            'Bloque Fin': h.bloque_fin,
            'Materia': m.nombre,
            'Docente': d.nombre,
            'Correo Docente': d.correo or ''
        })
    
    df = pd.DataFrame(data)
    
    if len(df) > 0:
        # Hoja general
        df.to_excel(writer, sheet_name='Horarios', index=False)
        
        # Hoja por grupo
        for grupo_nombre in df['Grupo'].unique():
            df_grupo = df[df['Grupo'] == grupo_nombre]
            sheet_name = grupo_nombre[:31]  # Excel limit 31 chars
            df_grupo.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        pd.DataFrame({'Info': ['No hay horarios generados']}).to_excel(writer, sheet_name='Info', index=False)
    
    writer.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'horarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

# ---------------------- MEJORA #6: COMPARACIÓN DE EXPERIMENTOS ----------------------
@bp.route("/experimentos/comparar")
def experimentos_comparar():
    """Comparar múltiples experimentos"""
    exp_ids = request.args.getlist('exp_ids')
    todos = Experimento.query.order_by(Experimento.creado_en.desc()).all()
    
    comparacion = None
    if exp_ids:
        try:
            exp_ids = [int(x) for x in exp_ids[:5]]  # Máximo 5
            comparacion = _generar_comparacion(exp_ids)
        except Exception as e:
            flash(f"Error al comparar: {str(e)}", "error")
    
    return render_template(
        "experimentos_comparar.html",
        experimentos=todos,
        selected_ids=exp_ids,
        comparacion=comparacion
    )

def _generar_comparacion(exp_ids):
    """Genera comparación visual de experimentos"""
    exps = Experimento.query.filter(Experimento.id.in_(exp_ids)).all()
    
    if not exps:
        return None
    
    # Extraer datos de logs
    logs_data = {}
    for exp in exps:
        log = json.loads(exp.log_json)
        logs_data[exp.id] = {
            'generaciones': [e.get('generacion', i+1) for i, e in enumerate(log)],
            'best': [float(e.get('best', 0)) for e in log],
            'avg': [float(e.get('avg', 0)) for e in log]
        }
    
    # Crear gráficas
    _ensure_dir_static('experimentos/comparaciones')
    
    # 1. Gráfica de fitness
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    for exp in exps:
        data = logs_data[exp.id]
        ax1.plot(data['generaciones'], data['best'], 
                label=f'Exp #{exp.id} (Best)', linewidth=2)
    ax1.set_xlabel('Generación')
    ax1.set_ylabel('Fitness')
    ax1.set_title('Comparación de Fitness')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    fig_fitness = f'experimentos/comparaciones/comp_fitness_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    _save_fig_to_static_dpi(fig1, fig_fitness)
    
    # 2. Gráfica de convergencia
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    for exp in exps:
        data = logs_data[exp.id]
        convergencia = [data['best'][i] - data['avg'][i] for i in range(len(data['best']))]
        ax2.plot(data['generaciones'], convergencia, 
                label=f'Exp #{exp.id}', linewidth=2)
    ax2.set_xlabel('Generación')
    ax2.set_ylabel('Best - Avg')
    ax2.set_title('Convergencia (Diversidad)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    fig_conv = f'experimentos/comparaciones/comp_conv_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    _save_fig_to_static_dpi(fig2, fig_conv)
    
    # 3. Gráfica de restricciones
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    categorias = ['Conflictos', 'Reservas', 'Disponibilidad', 'Turno', 'Exceso', 'Falta']
    x = range(len(exps))
    width = 0.15
    
    for i, cat_attr in enumerate(['conflictos_docente', 'violacion_reserva', 
                                   'violacion_disponibilidad', 'turno_incorrecto',
                                   'exceso_sesiones', 'falta_sesiones']):
        valores = [getattr(e, cat_attr, 0) for e in exps]
        ax3.bar([p + width*i for p in x], valores, width, label=categorias[i])
    
    ax3.set_xlabel('Experimentos')
    ax3.set_ylabel('Violaciones')
    ax3.set_title('Restricciones Violadas por Experimento')
    ax3.set_xticks([p + width * 2.5 for p in x])
    ax3.set_xticklabels([f'#{e.id}' for e in exps])
    ax3.legend()
    
    fig_rest = f'experimentos/comparaciones/comp_rest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    _save_fig_to_static_dpi(fig3, fig_rest)
    
    # Estadísticas
    stats = {
        'mejor_avg': max(e.avg_final for e in exps),
        'peor_avg': min(e.avg_final for e in exps),
        'tiempo_promedio': sum(e.tiempo_total for e in exps) / len(exps),
        'mas_rapido': min(exps, key=lambda e: e.tiempo_total).id,
        'mejor_restricciones': min(exps, key=lambda e: (
            e.conflictos_docente + e.violacion_reserva + e.violacion_disponibilidad
        )).id
    }
    
    return {
        'experimentos': exps,
        'fig_fitness': fig_fitness,
        'fig_convergencia': fig_conv,
        'fig_restricciones': fig_rest,
        'stats': stats
    }

def _ensure_dir_static(rel_path):
    """Crea directorio en static si no existe"""
    static_root = os.path.join(os.path.dirname(__file__), "static")
    full_path = os.path.join(static_root, rel_path)
    os.makedirs(full_path, exist_ok=True)

def _save_fig_to_static_dpi(fig, rel_path):
    """Guarda figura en static con DPI alto"""
    static_root = os.path.join(os.path.dirname(__file__), "static")
    _ensure_dir_static(os.path.dirname(rel_path))
    fig.savefig(os.path.join(static_root, rel_path), bbox_inches="tight", dpi=150)
    plt.close(fig)

# ---------------------- MEJORA #5: TABLERO MEJORADO ----------------------
@bp.route("/tablero_mejorado")
def tablero_mejorado():
    """Tablero con vista mejorada de todos los grupos"""
    grupos = Grupo.query.order_by(Grupo.turno, Grupo.nombre).all()
    return render_template("tablero_mejorado.html", grupos=grupos)