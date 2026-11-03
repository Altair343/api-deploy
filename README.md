# api-deploy
## Instalacion
### 1. Ejecutar en local
Necesitas Python 3.12 o superior y PostgreSQL 17.

1.1 Crea una base de datos
por ejemplo:
```sql
CREATE DATABASE NAME_DATABASE;
```

1.2 Desde la raíz del proyecto instala los modulos
```powershell
python -m pip install -r requirements.txt
```

1.3 Copia .env.example a .env <br>
Edita `.env` y asigna a las variables sus respectivos valores

1.4 Ejecuta las migraciones <br>
Solo si no tiene revisiones las puedes generar con:
```powershell
python -m alembic revision --autogenerate -m "create tables"
```
posterior valida las revisiones y si todo esta bien Aplica la migración
```powershell
python -m alembic upgrade head
```
con esto se crearan las tablas

1.5 finalmente arranca el servicio
```powershell
uvicorn app.main:app --reload
```

### 2. Ejecutar en local con Docker Compose
 Desde la raíz del proyecto

1.1 Creamos la imagen del proyecto
```powershell
docker build -t fastapi:1.0.0 .
```

1.2 Copia .env.example a .env <br>
Edita `.env` y asigna a las variables sus respectivos valores

1.3 Copia .env-db.example a .env-db <br>
Edita `.env-db` y asigna a las variables sus respectivos valores

1.4 Ejecuta docker-compose.yml
```powershell
docker-compose up -d --build
```

1.5 Ejecuta las migraciones <br>
Solo si no tiene revisiones las puedes generar con:
```powershell
python -m alembic revision --autogenerate -m "create tables"
```
posterior valida las revisiones y si todo esta bien Aplica la migración
```powershell
python -m alembic upgrade head
```
con esto se crearan las tablas

## Verificar la API local
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Estado del proceso: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Desplegar en Azure con Terraform

