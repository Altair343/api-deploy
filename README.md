# api-deploy
## Installation
### 1. Run locally
You need:
- Python 3.12 or later
- PostgreSQL 17

1.1 Create a database
For example:
```sql
CREATE DATABASE NAME_DATABASE;
```

1.2 Install the dependencies from the project root.
```powershell
python -m pip install -r requirements.txt
```

1.3 Copy `.env.example` to `.env` <br>
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
You need:
- Docker

From the project root

1.1 Build the project image.
```powershell
docker build -t fastapi:1.0.0 .
```

1.2 Copy `.env.example` to `.env` <br><br>
Edit `.env` and set each variable to its appropriate value.

1.3 Copy `.env-db.example` to `.env-db` <br>
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

## Deploy to Azure with Terraform
You need:
- Terraform
- Docker
- azure-cli

1.1 Navigate to infrastructure/terraform: <br>

1.2 Copy `terraform.tfvars.example` to `terraform.tfvars` <br><br>
Edit `terraform.tfvars.example` and set each variable to its appropriate value.

1.3 Run:
```powershell
terraform init
terraform validate
terraform plan
terraform apply
```

1.4 Once it finishes, you should see output like this:
```
Outputs:
acr_name = "fastapidemoyrs7u8"
acr_server = "fastapidemoyrs7u8.azurecr.io"
postgres_db = "fastapidb"
postgres_hostname = "fastapi-pg-yrs7u8.postgres.demo.az"
resource_group_name = "fastapi-rg"

```
1.4.1 If you lost the output
To get $acr_name:
```powershell
terraform output -raw acr_name
```
and to get $acr_server:
```powershell
terraform output -raw acr_server
```

1.5 Build the project image. <br>
From the project root <br>
Use the following naming format:: <br>
acr_server/name_image:tag <br>
For example: <br>
fastapidemoyrs7u8.azurecr.io/fastapi:1.0.0 <br>

and run:
```powershell
docker build -t fastapidemoyrs7u8.azurecr.io/fastapi:1.0.0 .
```

1.6 Log in to ACR using the $acr_name obtained in step 1.3.
```powershell
az acr login --name fastapidemoyrs7u8
```

1.7 Push the image.
```powershell
docker push fastapidemoyrs7u8.azurecr.io/fastapi:1.0.0
```

1.8 Return to infrastructure/terraform:
Set deploy_app = true in `terraform.tfvars`, review the plan, and apply it:
```powershell
terraform plan
terraform apply
```

1.9 Access the container using the following command format
```powershell
az containerapp exec --name "your-proyec-api"  --resource-group "your-resource-group"  --container "name-container"  --command "/bin/sh"
```
For example:
```powershell
az containerapp exec --name "fastapi-api"  --resource-group "fastapi-rg"  --container "fastapi"  --command "/bin/sh"
```

1.10 Run the migrations.
Only if there are no existing revisions, generate them with:
```powershell
python -m alembic revision --autogenerate -m "create tables"
```
Then review the revisions and, if everything looks correct, apply the migration.
```powershell
python -m alembic upgrade head
```
This will create the tables. You can now exit the container.


1.11 Once step 1.7 finishes, the output includes two new values, $api_url and $swagger_url, which you can use to access the API.
```
Outputs:
acr_name = "fastapidemoyrs7u8"
acr_server = "fastapidemoyrs7u8.azurecr.io"
api_url = "https://fastapi-api.demo.io"
postgres_db = "fastapidb"
postgres_hostname = "fastapi-pg-yrs7u8.postgres.demo.az"
resource_group_name = "fastapi-rg"
swagger_url = "https://fastapi-api.demo.io/docs"
```