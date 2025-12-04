import random, time
from collections import defaultdict
from .models import (
    db, Turno, DIAS, Docente, Materia, Grupo,
    MateriaGrupo, DocenteMateria, Disponibilidad,
    ReservaModulo, Horario
)

GA_LOG = []
def get_ga_log():
    return GA_LOG[:]

def _bloques_turno(turno: Turno):
    return list(range(1, 9))

def _reservas_map():
    R = defaultdict(list)
    for r in ReservaModulo.query.all():
        R[(r.grupo_id, r.dia, r.turno.value)].append((r.bloque_inicio, r.bloque_fin, r.materia_id))
    return R

def _disp_docente_map():
    D = defaultdict(list)
    for d in Disponibilidad.query.all():
        D[(d.docente_id, d.dia, d.turno.value)].append((d.bloque_inicio, d.bloque_fin))
    return D

def _materias_por_docente():
    M = defaultdict(set)
    for dm in DocenteMateria.query.all():
        M[dm.docente_id].add(dm.materia_id)
    return M

def _planes():
    P = []
    for p in MateriaGrupo.query.all():
        m = Materia.query.get(p.materia_id)
        g = Grupo.query.get(p.grupo_id)
        P.append((g.id, m.id, p.sesiones_por_semana, m.bloques_duracion, g.turno.value))
    return P

def _docentes():
    return Docente.query.all()

def _fitness(ind):
    pen = 0
    by_g_dia = defaultdict(list)
    by_d_doc = defaultdict(list)
    by_g_m_d = defaultdict(list)
    by_docente = defaultdict(int)

    for (g,dia,turno,b1,b2,mat,doc) in ind:
        by_g_dia[(g,dia,turno)].append((b1,b2,mat,doc))
        by_d_doc[(doc,dia,turno)].append((b1,b2,mat,g))
        by_g_m_d[(g,mat,dia)].append((b1,b2))
        by_docente[doc] += (b2 - b1 + 1)

    for key, slots in by_g_dia.items():
        slots.sort()
        g,dia,turno = key
        for (b1,b2,mat,doc) in slots:
            for (rb1,rb2,rmat) in RESERVAS.get((g,dia,turno), []):
                if not (b2 < rb1 or b1 > rb2) and rmat != mat:
                    pen += 10
        for i in range(len(slots)):
            b1,b2,_,_ = slots[i]
            for j in range(i+1,len(slots)):
                c1,c2,_,_ = slots[j]
                if not (b2 < c1 or b1 > c2):
                    pen += 5

    for key, slots in by_d_doc.items():
        slots.sort()
        for i in range(len(slots)):
            b1,b2,_,_ = slots[i]
            for j in range(i+1,len(slots)):
                c1,c2,_,_ = slots[j]
                if not (b2 < c1 or b1 > c2):
                    pen += 6

    for (g,dia,turno,b1,b2,mat,doc) in ind:
        ok = any(b1 >= db1 and b2 <= db2 for (db1,db2) in DISP.get((doc,dia,turno), []))
        if not ok:
            pen += 8
        if MATERIAS[mat]["turno"] != turno:
            pen += 4

    count = defaultdict(int)
    for (g,_,_,_,_,mat,_) in ind:
        count[(g,mat)] += 1
    for (g,mat,ses,dur,turno) in PLANES:
        if count[(g,mat)] > ses:
            pen += (count[(g,mat)] - ses) * 3
        elif count[(g,mat)] < ses:
            pen += (ses - count[(g,mat)]) * 3

    for key, lst in by_g_m_d.items():
        total_blocks = sum((b2-b1+1) for (b1,b2) in lst)
        exceso = max(0, total_blocks - 2)
        if exceso > 0:
            pen += exceso * 7

    for key, slots in by_g_dia.items():
        slots.sort()
        for i in range(len(slots) - 1):
            _, b2_actual, mat_actual, _ = slots[i]
            b1_siguiente, _, mat_siguiente, _ = slots[i+1]
            if mat_actual == mat_siguiente and b1_siguiente == b2_actual + 1:
                bloques_consecutivos = b2_actual - slots[i][0] + 1 + (slots[i+1][1] - b1_siguiente + 1)
                if bloques_consecutivos > 2:
                    pen += (bloques_consecutivos - 2) * 5

    for doc, total_bloques in by_docente.items():
        horas = total_bloques * 0.83
        if horas > 35:
            pen += int((horas - 35) * 10)

    return -pen

def _metrics(ind):
    m = {
        "conflictos_docente": 0,
        "violacion_reserva": 0,
        "violacion_disponibilidad": 0,
        "turno_incorrecto": 0,
        "exceso_sesiones": 0,
        "falta_sesiones": 0,
        "exceso_bloques_dia": 0,
        "exceso_bloques_consecutivos": 0,
        "exceso_horas_semanales": 0,
    }

    by_g_dia = defaultdict(list)
    by_d_doc = defaultdict(list)
    by_g_m_d = defaultdict(list)
    by_docente = defaultdict(int)

    for (g,dia,turno,b1,b2,mat,doc) in ind:
        by_g_dia[(g,dia,turno)].append((b1,b2,mat,doc))
        by_d_doc[(doc,dia,turno)].append((b1,b2,mat,g))
        by_g_m_d[(g,mat,dia)].append((b1,b2))
        by_docente[doc] += (b2 - b1 + 1)

    for key, slots in by_g_dia.items():
        slots.sort()
        g,dia,turno = key
        for (b1,b2,mat,doc) in slots:
            for (rb1,rb2,rmat) in RESERVAS.get((g,dia,turno), []):
                if not (b2 < rb1 or b1 > rb2) and rmat != mat:
                    m["violacion_reserva"] += 1

    for key, slots in by_d_doc.items():
        slots.sort()
        for i in range(len(slots)):
            b1,b2,_,_ = slots[i]
            for j in range(i+1,len(slots)):
                c1,c2,_,_ = slots[j]
                if not (b2 < c1 or b1 > c2):
                    m["conflictos_docente"] += 1

    for (g,dia,turno,b1,b2,mat,doc) in ind:
        ok = any(b1 >= db1 and b2 <= db2 for (db1,db2) in DISP.get((doc,dia,turno), []))
        if not ok:
            m["violacion_disponibilidad"] += 1
        if MATERIAS[mat]["turno"] != turno:
            m["turno_incorrecto"] += 1

    count = defaultdict(int)
    for (g,_,_,_,_,mat,_) in ind:
        count[(g,mat)] += 1
    for (g,mat,ses,dur,turno) in PLANES:
        if count[(g,mat)] > ses:
            m["exceso_sesiones"] += (count[(g,mat)] - ses)
        elif count[(g,mat)] < ses:
            m["falta_sesiones"] += (ses - count[(g,mat)])

    for key, lst in by_g_m_d.items():
        total_blocks = sum((b2-b1+1) for (b1,b2) in lst)
        exceso = max(0, total_blocks - 2)
        m["exceso_bloques_dia"] += exceso

    for key, slots in by_g_dia.items():
        slots.sort()
        for i in range(len(slots) - 1):
            _, b2_actual, mat_actual, _ = slots[i]
            b1_siguiente, _, mat_siguiente, _ = slots[i+1]
            if mat_actual == mat_siguiente and b1_siguiente == b2_actual + 1:
                bloques_consecutivos = b2_actual - slots[i][0] + 1 + (slots[i+1][1] - b1_siguiente + 1)
                if bloques_consecutivos > 2:
                    m["exceso_bloques_consecutivos"] += (bloques_consecutivos - 2)

    for doc, total_bloques in by_docente.items():
        horas = total_bloques * 0.83
        if horas > 35:
            m["exceso_horas_semanales"] += 1

    return m

def _random_individuo():
    IND = []
    demandas = []
    for (g,mat,ses,dur,turno) in PLANES:
        for _ in range(ses):
            demandas.append((g,mat,dur,turno))
    random.shuffle(demandas)

    for (g,mat,dur,turno) in demandas:
        dias = DIAS[:]; random.shuffle(dias)
        posibles_docs = [d.id for d in DOCENTES if mat in MATXDOC[d.id]]
        random.shuffle(posibles_docs)
        placed = False

        for dia in dias:
            starts = [b for b in _bloques_turno(Turno[turno]) if b+dur-1 <= 8]
            random.shuffle(starts)
            for b1 in starts:
                b2 = b1 + dur - 1
                bad = False
                for (rb1,rb2, rmat) in RESERVAS.get((g,dia,turno), []):
                    if not (b2 < rb1 or b1 > rb2) and rmat != mat:
                        bad = True; break
                if bad: continue

                for doc in posibles_docs:
                    okd = any(b1 >= db1 and b2 <= db2 for (db1,db2) in DISP.get((doc,dia,turno), []))
                    if not okd: continue

                    total_blocks = sum((x[4]-x[3]+1) for x in IND if x[0]==g and x[1]==dia and x[5]==mat)
                    if total_blocks + dur > 2:
                        continue

                    IND.append((g,dia,turno,b1,b2,mat,doc))
                    placed = True
                    break
                if placed: break
            if placed: break

        if not placed:
            doc = (posibles_docs[0] if posibles_docs else random.choice([d.id for d in DOCENTES]))
            IND.append((g, random.choice(DIAS), turno, 1, dur, mat, doc))
    return IND

def _crossover(a, b, rate=0.5):
    n = min(len(a), len(b))
    cut = int(n * rate)
    return a[:cut] + b[cut:]

def _mutate(ind, pm=0.15):
    out = []
    for (g,dia,turno,b1,b2,mat,doc) in ind:
        if random.random() < pm:
            op = random.choice(["dia","bloque","doc"])
            if op == "dia":
                dia = random.choice(DIAS)
            elif op == "bloque":
                dur = b2 - b1 + 1
                starts = [x for x in range(1,9) if x+dur-1 <= 8]
                b1 = random.choice(starts); b2 = b1 + dur - 1
            else:
                posibles = [d for d in DOCENTES if mat in MATXDOC[d.id]]
                if posibles:
                    doc = random.choice(posibles).id
        out.append((g,dia,turno,b1,b2,mat,doc))
    return out

def _to_horario(ind):
    Horario.query.delete()
    for (g,dia,turno,b1,b2,mat,doc) in ind:
        h = Horario(
            grupo_id=g, materia_id=mat, docente_id=doc, dia=dia,
            turno=Turno[turno], bloque_inicio=b1, bloque_fin=b2
        )
        db.session.add(h)
    db.session.commit()

def generar_horario(generaciones=60, tam=40, elite=6, seed=None,
                    turnos=None, verbose=True, max_seconds=60, early_stop=12):
    global GA_LOG, RESERVAS, DISP, MATXDOC, PLANES, DOCENTES, MATERIAS

    if seed is not None:
        random.seed(seed)
    t0 = time.time()

    RESERVAS = _reservas_map()
    DISP = _disp_docente_map()
    MATXDOC = _materias_por_docente()
    PLANES = _planes()
    DOCENTES = _docentes()
    MATERIAS = {m.id: {"dur": m.bloques_duracion, "turno": m.turno.value} for m in Materia.query.all()}

    pobl = [_random_individuo() for _ in range(tam)]
    GA_LOG = []
    best, best_score, stall = None, -10**9, 0

    for gen in range(1, generaciones+1):
        scores = [_fitness(ind) for ind in pobl]
        ranked = sorted(zip(scores, pobl), key=lambda x: x[0], reverse=True)
        best_ind = ranked[0][1]
        best_val = ranked[0][0]
        avg_val  = sum(scores)/len(scores)

        comp = _metrics(best_ind)
        GA_LOG.append({
            "generacion": gen,
            "best": float(best_val),
            "avg": float(avg_val),
            "comp": comp,
            "time_sec": time.time() - t0
        })

        pobl = [x[1] for x in ranked[:elite]]

        if best_val > best_score:
            best_score = best_val; best = best_ind; stall = 0
        else:
            stall += 1

        lim = max(2, elite*2)
        while len(pobl) < tam:
            p1 = random.choice(ranked[:lim])[1]
            p2 = random.choice(ranked[:lim])[1]
            child = _crossover(p1, p2, rate=random.uniform(0.3, 0.7))
            child = _mutate(child, pm=0.15)
            pobl.append(child)

        if (time.time()-t0) > max_seconds or stall >= early_stop:
            break

    if best:
        _to_horario(best)
    return best, best_score