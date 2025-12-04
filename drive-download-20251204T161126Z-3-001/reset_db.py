from app import create_app, db
from app.models import (
    Docente, Materia, Grupo, DocenteMateria, 
    Disponibilidad, MateriaGrupo, ReservaModulo, 
    Horario, Experimento
)

app = create_app()

def reset_database():
    """Limpia todas las tablas respetando foreign keys"""
    with app.app_context():
        print("🗑️  Limpiando base de datos...")
        
        # Eliminar en orden correcto (respetando foreign keys)
        print("  - Eliminando horarios...")
        Horario.query.delete()
        
        print("  - Eliminando experimentos...")
        Experimento.query.delete()
        
        print("  - Eliminando reservas...")
        ReservaModulo.query.delete()
        
        print("  - Eliminando planes de grupo...")
        MateriaGrupo.query.delete()
        
        print("  - Eliminando disponibilidades...")
        Disponibilidad.query.delete()
        
        print("  - Eliminando relaciones docente-materia...")
        DocenteMateria.query.delete()
        
        print("  - Eliminando docentes...")
        Docente.query.delete()
        
        print("  - Eliminando materias...")
        Materia.query.delete()
        
        print("  - Eliminando grupos...")
        Grupo.query.delete()
        
        db.session.commit()
        print("\n✅ Base de datos limpiada correctamente")
        print("📊 Resumen:")
        print(f"   - Docentes: {Docente.query.count()}")
        print(f"   - Materias: {Materia.query.count()}")
        print(f"   - Grupos: {Grupo.query.count()}")

if __name__ == "__main__":
    import sys
    
    respuesta = input("⚠️  ¿Estás seguro de querer limpiar la base de datos? (si/no): ")
    
    if respuesta.lower() in ['si', 's', 'yes', 'y']:
        reset_database()
    else:
        print("❌ Operación cancelada")
        sys.exit(0)