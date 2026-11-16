# tallyO

Multi-tenant ordering system with a modular Django backend and AngularJS
administration/storefront client.

## Start with Docker

```bash
cp .env.example .env
docker compose up --build
```

The customer and store administration frontend is available at
`http://localhost:4200`. The API is at `http://localhost:8000`, Django Admin at
`http://localhost:8000/admin/`, and the health endpoint at
`http://localhost:8000/health/`.

Create the first platform super admin in another terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

For local installation, testing, migrations, architecture, and daily commands,
see [Developer guide](docs/development.md).

Frontend structure, state management, security boundaries, and extension points
are documented in the [Frontend guide](docs/frontend.md).

For a presenter-ready walkthrough covering super admins, store owners, and
customers, see the [Demonstration guide](docs/demo-guide.md).

## Implemented modules

1. [Foundation, accounts, and stores](docs/modules/01-foundation-and-stores.md)
2. [Authentication and administration](docs/modules/02-authentication-and-administration.md)
3. [Catalog](docs/modules/03-catalog.md)
4. [Customers and orders](docs/modules/04-customers-and-orders.md)
5. [Daily reporting](docs/modules/05-daily-reporting.md)

See the [API reference](docs/api.md) for endpoint details.


