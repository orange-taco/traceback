# Traceback Backend

## Docker Compose

Create a local environment file and fill in all values:

```sh
cp .env.example .env
```

Run the development stack:

```sh
docker compose -f docker-compose.yml -f docker-compose_dev.yml up --build
```

Render and validate the production configuration:

```sh
docker compose -f docker-compose.yml -f docker-compose_prod.yml config
```

The production overlay intentionally publishes no host ports. Route traffic to
the `app` service on port 8000 from infrastructure attached to the `backend`
network.
