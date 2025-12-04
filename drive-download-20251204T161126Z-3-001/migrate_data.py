# migrate_data.py - Migrar datos de SQLite a PostgreSQL
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Docente, Materia, Grupo, DocenteMateria, Disponibilidad,
    MateriaGrupo, ReservaModulo, Horario, Experimento
)

# Configurar conexiones
sqlite_url = 'sqlite:///instance/horarios.db'
postgres_url = 'postgresql://flask_user:password123@localhost:5432/horarios'

sqlite_engine = create_engine(sqlite_url)
postgres_engine = create_engine(postgres_url)

SessionSQLite = sessionmaker(bind=sqlite_engine)
SessionPostgres = sessionmaker(bind=postgres_engine)

def migrate_table(model_class, session_sqlite, session_postgres):
    """Migra una tabla completa."""
    print(f"Migrando {model_class.__tablename__}...")
    items = session_sqlite.query(model_class).all()
    for item in items:
        # Crear una copia sin id para que se auto-incremente
        data = {c.name: getattr(item, c.name) for c in item.__table__.columns if c.name != 'id'}
        new_item = model_class(**data)
        session_postgres.add(new_item)
    session_postgres.commit()
    print(f"  → {len(items)} registros migrados.")

def main():
    session_sqlite = SessionSQLite()
    session_postgres = SessionPostgres()

    try:
        # Orden de migración para respetar foreign keys
        migrate_table(Docente, session_sqlite, session_postgres)
        migrate_table(Materia, session_sqlite, session_postgres)
        migrate_table(Grupo, session_sqlite, session_postgres)
        migrate_table(DocenteMateria, session_sqlite, session_postgres)
        migrate_table(Disponibilidad, session_sqlite, session_postgres)
        migrate_table(MateriaGrupo, session_sqlite, session_postgres)
        migrate_table(ReservaModulo, session_sqlite, session_postgres)
        migrate_table(Horario, session_sqlite, session_postgres)
        migrate_table(Experimento, session_sqlite, session_postgres)

        print("¡Migración completada exitosamente!")

    except Exception as e:
        print(f"Error durante la migración: {e}")
        session_postgres.rollback()
    finally:
        session_sqlite.close()
        session_postgres.close()

if __name__ == "__main__":
    main()
