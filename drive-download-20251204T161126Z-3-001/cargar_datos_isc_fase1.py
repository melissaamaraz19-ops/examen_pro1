"""
Script para cargar datos de prueba - FASE 1: 3 GRUPOS DEL 1ER CUATRIMESTRE
Ingeniería en Sistemas Computacionales - UPQ
"""
from app import create_app, db
from app.models import Turno, Docente, Materia, Grupo, DocenteMateria, Disponibilidad, MateriaGrupo

app = create_app()

def limpiar_datos():
    """Elimina todos los datos existentes"""
    with app.app_context():
        print("Limpiando datos existentes...")
        db.session.query(MateriaGrupo).delete()
        db.session.query(Disponibilidad).delete()
        db.session.query(DocenteMateria).delete()
        db.session.query(Materia).delete()
        db.session.query(Docente).delete()
        db.session.query(Grupo).delete()
        db.session.commit()
        print("Datos limpiados")

def cargar_grupos():
    """Carga 3 grupos del 1er cuatrimestre - turno matutino"""
    with app.app_context():
        print("\nCargando grupos del 1er cuatrimestre...")
        grupos = [
            Grupo(nombre="ISC-1A-M", turno=Turno.MATUTINO),
            Grupo(nombre="ISC-1B-M", turno=Turno.MATUTINO),
            Grupo(nombre="ISC-1C-M", turno=Turno.MATUTINO),
        ]
        db.session.bulk_save_objects(grupos)
        db.session.commit()
        print(f"✓ {len(grupos)} grupos cargados")

def cargar_materias():
    """Carga todas las materias del 1er cuatrimestre"""
    with app.app_context():
        print("\nCargando materias del 1er cuatrimestre...")
        materias = [
            # ========== 1ER CUATRIMESTRE ==========
            Materia(nombre="Inglés I", turno=Turno.MATUTINO, bloques_duracion=2),
            Materia(nombre="Valores del Ser", turno=Turno.MATUTINO, bloques_duracion=1),
            Materia(nombre="Herramientas Ofimáticas", turno=Turno.MATUTINO, bloques_duracion=2),
            Materia(nombre="Arquitectura de Computadoras", turno=Turno.MATUTINO, bloques_duracion=2),
            Materia(nombre="Introducción a la Ingeniería en Sistemas Computacionales", turno=Turno.MATUTINO, bloques_duracion=1),
            Materia(nombre="Álgebra Lineal", turno=Turno.MATUTINO, bloques_duracion=2),
            Materia(nombre="Fundamentos de Programación", turno=Turno.MATUTINO, bloques_duracion=2),
        ]
        db.session.bulk_save_objects(materias)
        db.session.commit()
        print(f"✓ {len(materias)} materias cargadas")

def cargar_docentes():
    """Carga 10 docentes para el 1er cuatrimestre"""
    with app.app_context():
        print("\nCargando docentes...")
        docentes = [
            # Inglés
            Docente(nombre="Mtra. Ana Victoria Flores", correo="avflores@upq.edu.mx"),
            Docente(nombre="Lic. María Elena Ruiz", correo="meruiz@upq.edu.mx"),
            
            # Habilidades Blandas
            Docente(nombre="Lic. Roberto Sánchez Mora", correo="rsanchez@upq.edu.mx"),
            
            # Programación
            Docente(nombre="Dr. Juan Alberto Pérez", correo="japerez@upq.edu.mx"),
            Docente(nombre="Ing. Laura Patricia Ramírez", correo="lpramirez@upq.edu.mx"),
            Docente(nombre="Mtro. Diego Morales Castro", correo="dmorales@upq.edu.mx"),
            
            # Matemáticas
            Docente(nombre="Dra. María Teresa González", correo="mtgonzalez@upq.edu.mx"),
            Docente(nombre="Mtro. Fernando Jiménez López", correo="fjimenez@upq.edu.mx"),
            
            # Hardware y Arquitectura
            Docente(nombre="Ing. Patricia López Martín", correo="plopez@upq.edu.mx"),
            Docente(nombre="Mtro. Javier Ruiz Gómez", correo="jruiz@upq.edu.mx"),
        ]
        db.session.bulk_save_objects(docentes)
        db.session.commit()
        print(f"✓ {len(docentes)} docentes cargados")

def asignar_materias_docentes():
    """Asigna materias que cada docente puede impartir"""
    with app.app_context():
        print("\nAsignando materias a docentes...")
        
        docentes = {d.nombre: d for d in Docente.query.all()}
        materias = {m.nombre: m for m in Materia.query.all()}
        
        asignaciones = [
            # Inglés (2 docentes para cubrir 3 grupos)
            ("Mtra. Ana Victoria Flores", ["Inglés I"]),
            ("Lic. María Elena Ruiz", ["Inglés I"]),
            
            # Habilidades Blandas
            ("Lic. Roberto Sánchez Mora", ["Valores del Ser"]),
            
            # Programación (3 docentes para 3 grupos con sesiones intensivas)
            ("Dr. Juan Alberto Pérez", ["Fundamentos de Programación"]),
            ("Ing. Laura Patricia Ramírez", ["Fundamentos de Programación"]),
            ("Mtro. Diego Morales Castro", ["Fundamentos de Programación"]),
            
            # Matemáticas (2 docentes)
            ("Dra. María Teresa González", ["Álgebra Lineal"]),
            ("Mtro. Fernando Jiménez López", ["Álgebra Lineal"]),
            
            # Hardware (2 docentes)
            ("Ing. Patricia López Martín", [
                "Arquitectura de Computadoras",
                "Herramientas Ofimáticas"
            ]),
            ("Mtro. Javier Ruiz Gómez", [
                "Arquitectura de Computadoras",
                "Introducción a la Ingeniería en Sistemas Computacionales"
            ]),
        ]
        
        count = 0
        for docente_nombre, lista_materias in asignaciones:
            docente = docentes[docente_nombre]
            for materia_nombre in lista_materias:
                materia = materias[materia_nombre]
                dm = DocenteMateria(docente_id=docente.id, materia_id=materia.id)
                db.session.add(dm)
                count += 1
        
        db.session.commit()
        print(f"✓ {count} asignaciones materia-docente creadas")

def cargar_disponibilidad():
    """Carga disponibilidad de todos los docentes"""
    with app.app_context():
        print("\nCargando disponibilidad de docentes...")
        
        docentes = {d.nombre: d for d in Docente.query.all()}
        
        # Disponibilidad por docente (amplia para permitir flexibilidad al GA)
        disponibilidades = {
            "Mtra. Ana Victoria Flores": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
            "Lic. María Elena Ruiz": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
            "Lic. Roberto Sánchez Mora": {
                "LUNES": [(1, 6)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 6)]
            },
            "Dr. Juan Alberto Pérez": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 6)]
            },
            "Ing. Laura Patricia Ramírez": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
            "Mtro. Diego Morales Castro": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
            "Dra. María Teresa González": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 6)]
            },
            "Mtro. Fernando Jiménez López": {
                "LUNES": [(1, 6)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
            "Ing. Patricia López Martín": {
                "LUNES": [(1, 8)], "MARTES": [(1, 8)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 6)], "VIERNES": [(1, 8)]
            },
            "Mtro. Javier Ruiz Gómez": {
                "LUNES": [(1, 8)], "MARTES": [(1, 6)], "MIERCOLES": [(1, 8)],
                "JUEVES": [(1, 8)], "VIERNES": [(1, 8)]
            },
        }
        
        count = 0
        for docente_nombre, disp_dict in disponibilidades.items():
            docente = docentes[docente_nombre]
            for dia, bloques_list in disp_dict.items():
                for b1, b2 in bloques_list:
                    disp = Disponibilidad(
                        docente_id=docente.id,
                        dia=dia,
                        turno=Turno.MATUTINO,
                        bloque_inicio=b1,
                        bloque_fin=b2
                    )
                    db.session.add(disp)
                    count += 1
        
        db.session.commit()
        print(f"✓ {count} disponibilidades cargadas")

def cargar_plan_estudios():
    """Asigna las mismas materias a los 3 grupos del 1er cuatrimestre"""
    with app.app_context():
        print("\nCargando plan de estudios...")
        
        grupos = Grupo.query.all()
        materias = {m.nombre: m for m in Materia.query.all()}
        
        # Todas las materias del 1er cuatrimestre con sus sesiones semanales
        materias_plan = [
            ("Inglés I", 2),
            ("Valores del Ser", 2),
            ("Herramientas Ofimáticas", 2),
            ("Arquitectura de Computadoras", 2),
            ("Introducción a la Ingeniería en Sistemas Computacionales", 2),
            ("Álgebra Lineal", 3),
            ("Fundamentos de Programación", 3),
        ]
        
        count = 0
        # Asignar las mismas materias a los 3 grupos
        for grupo in grupos:
            for materia_nombre, sesiones in materias_plan:
                materia = materias[materia_nombre]
                mg = MateriaGrupo(
                    grupo_id=grupo.id,
                    materia_id=materia.id,
                    sesiones_por_semana=sesiones
                )
                db.session.add(mg)
                count += 1
        
        db.session.commit()
        print(f"✓ {count} asignaciones de plan de estudios creadas")
        print(f"  (7 materias × 3 grupos = {count} asignaciones)")

def main():
    """Ejecuta toda la carga de datos"""
    print("="*70)
    print("CARGA DE DATOS - FASE 1: 3 GRUPOS DEL 1ER CUATRIMESTRE")
    print("Ingeniería en Sistemas Computacionales - UPQ")
    print("="*70)
    
    limpiar_datos()
    cargar_grupos()
    cargar_materias()
    cargar_docentes()
    asignar_materias_docentes()
    cargar_disponibilidad()
    cargar_plan_estudios()
    
    print("\n" + "="*70)
    print("✓ CARGA COMPLETA")
    print("="*70)
    print("\nEstadísticas:")
    with app.app_context():
        print(f"  - Grupos: {Grupo.query.count()} (todos del 1er cuatrimestre)")
        print(f"  - Materias: {Materia.query.count()}")
        print(f"  - Docentes: {Docente.query.count()}")
        print(f"  - Asignaciones Docente-Materia: {DocenteMateria.query.count()}")
        print(f"  - Disponibilidades: {Disponibilidad.query.count()}")
        print(f"  - Plan de estudios: {MateriaGrupo.query.count()}")
        
        # Mostrar resumen de carga horaria
        total_sesiones = sum([mg.sesiones_por_semana for mg in MateriaGrupo.query.all()])
        print(f"\nCarga horaria total:")
        print(f"  - Sesiones por grupo/semana: 16")
        print(f"  - Total sesiones sistema: {total_sesiones} (16 × 3 grupos)")
    
    print("\n" + "="*70)
    print("¡Listo para ejecutar experimentos!")
    print("="*70)
    print("\nPróximos pasos:")
    print("  1. python run.py")
    print("  2. Ir a http://localhost:5000")
    print("  3. Panel → Configurar GA:")
    print("     - Generaciones: 60")
    print("     - Población: 40")
    print("     - Elite: 6")
    print("     - Ámbito: MATUTINO")
    print("  4. Ver resultados en:")
    print("     - Tablero: Horarios por grupo")
    print("     - Experimentos: Métricas y gráficas")
    print("\nNOTA: Los 3 grupos tienen las MISMAS materias")
    print("      El desafío es asignar docentes sin conflictos")

if __name__ == "__main__":
    main()