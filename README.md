# api-deploy
## Installation
### 1. Run locally
You need Python 3.12 or later and PostgreSQL 17

1.1 Create a database
For example:
```sql
CREATE DATABASE NAME_DATABASE;
```

1.2 Install the dependencies from the project root.
```powershell
python -m pip install -r requirements.txt
```

1.3 Copy .env.example to .env <br>
Edit `.env` and set each variable to its appropriate value.

1.4 Run the migrations. <br>
Only if there are no existing revisions, generate them with:
```powershell
python -m alembic revision --autogenerate -m "create tables"
```
Then review the revisions and, if everything looks correct, apply the migration.
```powershell
python -m alembic upgrade head
```
This will create the tables. <br>
1.5 Finally, start the service.
```powershell
uvicorn app.main:app --reload
```

### 2. Run locally with Docker Compose
From the project root

1.1 Build the project image.
```powershell
docker build -t fastapi:1.0.0 .
```

1.2 Copy .env.example to .env <br><br>
Edit `.env` and set each variable to its appropriate value.

1.3 Copy .env-db.example to .env-db <br>
Edit `.env-db` and set each variable to its appropriate value.

1.4 Run docker-compose.yml.
```powershell
docker-compose up -d --build
```

1.5 Run the migrations. <br>
Enter the API container:
```powershell
docker exec -it api_demo bash
```

Only if there are no existing revisions, generate them with:
```powershell
python -m alembic revision --autogenerate -m "create tables"
```
Then review the revisions and, if everything looks correct, apply the migration.
```powershell
python -m alembic upgrade head
```
This will create the tables. You can now exit the container.

## Verify the local API
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Process status: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Desplegar en Azure con Terraform
