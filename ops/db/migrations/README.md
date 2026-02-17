Aplicación de migraciones (Postgres en Docker):

- Requisitos: Docker Desktop activo, variables del `.env` cargadas.
- Levantar servicios:
  - `docker compose -f ops/docker-compose.yml up -d`
- Aplicar migración inicial:
  - `docker exec -i aut_windmill_postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/0001_init.sql`

Nota: si no se monta automáticamente el archivo, copiarlo y ejecutarlo:
- `docker cp ops/db/migrations/0001_init.sql aut_windmill_postgres:/tmp/0001_init.sql`
- `docker exec -i aut_windmill_postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /tmp/0001_init.sql`
