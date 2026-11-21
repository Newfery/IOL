# Initial Structure — FastAPI + SQLAlchemy + Pydantic

Estructura base de un proyecto en capas (routers, services, repositories, models, schemas, dtos, mappers, middlewares).

## Importante: este repo es un TEMPLATE

**No clones este repo directamente ni intentes pushear.** El repo está protegido y solo el docente tiene permisos de escritura.

### Cómo trabajar con esta plantilla

1. Entrá al repo en GitHub.
2. Hacé click en el botón verde **"Use this template" → "Create a new repository"** (o, si no aparece, usá **"Fork"**).
3. Creá el nuevo repo en **tu cuenta personal** de GitHub.
4. Cloná **tu copia** (no la del docente):
   ```bash
   git clone https://github.com/<TU_USUARIO>/<TU_REPO>.git
   cd <TU_REPO>
   ```
5. A partir de ahí trabajás libremente sobre tu propio repo.

> Si intentás `git push` y te dice `permission denied`, es porque clonaste el repo del docente en lugar de tu fork/template. Volvé al paso 2.

---

## Setup

```bash
cd .\backend\
python -m venv venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
source venv/bin/activate          # Linux/Mac
# venv\Scripts\Activate.ps1       # Windows

pip install -r requirements.txt
cp .env.example .env               # editá con tus credenciales

uvicorn src.app:app --reload
```

Abrir http://localhost:8000/docs para ver Swagger.

El backend sirve el ícono del navegador desde `src/static/favicon.ico` en `/favicon.ico`.

## Cotizaciones con Yahoo Finance

El endpoint `GET /api/activos/cotizacion/{ticker}` consulta la última cotización
diaria disponible en Yahoo Finance. Por ejemplo:

```text
GET http://localhost:8000/api/activos/cotizacion/AAPL
GET http://localhost:8000/api/activos/cotizacion/GGAL.BA
```

Devuelve el último cierre, el cierre anterior, la variación porcentual y la fecha.
No requiere una API key ni modifica el precio guardado en la base de datos.

### Cargar activos en el catálogo

`/api/market/assets` muestra los registros activos de la tabla `activo`. Para
cargar acciones argentinas, CEDEARs, hasta 500 acciones estadounidenses de mayor
capitalización (con umbral de USD 10.000 millones) y ETFs principales, ejecutar
desde `backend/`:

```powershell
.\venv\Scripts\python.exe -m src.db.seeders.yfinance_assets
```

El sincronizador consulta Yahoo Finance, omite símbolos sin cotización, inserta
los nuevos y actualiza nombre, precio y variación de los existentes sin borrar
activos ni tenencias. Yahoo no ofrece un catálogo global exhaustivo; esta es una
selección amplia, no la totalidad de sus símbolos. Las acciones y ETFs de EE. UU.
se guardan en USD con sufijo `.US` para distinguirlos de CEDEARs con el mismo
ticker.

## Funcionalidades del broker

Las rutas de negocio se publican bajo `/api`:

- `POST /inversores`: recibe una contraseña obligatoria (mínimo 8 caracteres,
  máximo 72 bytes), la guarda con bcrypt y no permite reutilizarla entre
  inversores. El alta crea automáticamente una cuenta comitente con ambos
  saldos en cero. `PATCH /inversores/{id}/perfil` cambia su perfil de riesgo.
- `GET /activos?tipo=...&moneda=...` filtra el catálogo;
  `PATCH /activos/{id}/precio` actualiza el precio vigente.
- `POST /movimientos` registra depósitos y extracciones y actualiza el saldo
  de la cuenta en la misma transacción.
- `POST /operaciones` recibe `cuenta_id`, `activo_id`, `tipo` y `cantidad`;
  el precio, la comisión y el total se calculan en el servidor.
- `POST /cuentas/{id}/mep` recibe `monto_ars` y registra atómicamente la compra
  de AL30 y la venta de AL30D. El cambio informado es `precio AL30 / precio
  AL30D`; se aplica la comisión de 0,5% a cada pata.
- `GET /cuentas/{id}/cartera` informa tenencias y totales en ARS/USD por
  separado; composición porcentual por tipo se calcula dentro de cada moneda,
  sin convertir entre ellas.
- `GET /cuentas/{id}/operaciones` admite `fecha_desde`, `fecha_hasta`, `tipo`
  y `ticker`, y devuelve operaciones ordenadas por fecha y comisiones.
- `GET /activos/mas-operados` ordena por volumen de unidades negociadas en los
  últimos siete días; `GET /activos/mas-favoritos` ordena por cantidad de
  inversores que los marcaron. `GET /cuentas/{id}/ganancias-realizadas`
  agrupa el resultado de ventas ejecutadas por año.

Para instalaciones existentes, aplicar en orden las migraciones
[`001_inversor_password.sql`](src/db/migrations/001_inversor_password.sql),
[`002_grupos_dashboard.sql`](src/db/migrations/002_grupos_dashboard.sql) y
[`003_operacion_liquidacion.sql`](src/db/migrations/003_operacion_liquidacion.sql),
[`004_users.sql`](src/db/migrations/004_users.sql) y
[`005_us_assets_catalog.sql`](src/db/migrations/005_us_assets_catalog.sql).
La migración conserva los inversores actuales sin asignarles contraseñas.
Configurar `PASSWORD_FINGERPRINT_SECRET` con un secreto estable y distinto de
`JWT_SECRET`; si se omite, se deriva del `JWT_SECRET` configurado.

El frontend usa además `POST /api/auth/login` (devuelve `token` e `inversor`) y
rutas de mercado, cuenta, cartera, órdenes y grupos bajo `/api`. Los aportes
grupales se debitan del saldo ARS del inversor y se registran en `aporte_grupo`;
las claves de acceso del grupo se guardan con hash.

`GET /api/market/dolar` usa los precios de AL30/AL30D y GD30/GD30C del catálogo
cuando están disponibles; si falta alguna pata, consulta el dólar Bolsa y el
contado con liquidación en DolarAPI. Cada tasa se obtiene de forma independiente
y se devuelve como `null` si su fuente no está disponible.

Las operaciones administrativas, como `POST /api/dividendos/`, requieren un
token de administrador obtenido con `POST /api/auth/admin/login` usando una
cuenta de `users` provisionada con `is_admin=true`. El login de inversor no
autoriza operaciones administrativas; las cuentas de administrador no se crean
desde el registro público. Después de aplicar la migración 004, crear la
primera cuenta administrativa desde `backend/` con
`python -m src.db.seeders.create_admin`. Luego iniciar sesión en
`/api/auth/admin/login`, copiar el token y usar **Authorize** en Swagger antes
de ejecutar `POST /api/dividendos/`.

Las ventas ejecutadas acreditan el efectivo después del plazo del activo:
acciones y CEDEARs a 24 horas, bonos a 48. Hasta su vencimiento aparecen en
`GET /api/cuenta/plazos` y no se pueden usar para nuevas compras o aportes. El
backend las acredita automáticamente cuando el inversor consulta saldo, cuenta,
plazos o inicia una operación.

---

## Estructura de carpetas

```
src/
├── db/
│   ├── connection.py
│   ├── models/          # SQLAlchemy
│   ├── migrations/      # Alembic
│   └── seeders/
├── schemas/             # Pydantic (validación HTTP)
├── dtos/                # Pydantic (transporte entre capas)
├── mappers/             # Model ⇄ DTO
├── repositories/        # queries
├── services/            # lógica de negocio
├── routers/             # endpoints FastAPI
├── middlewares/
├── config/
├── utils/
├── app.py               # crea app FastAPI
└── main.py              # entry point
```

---

## Cómo está pensada la entrega

El módulo de **users** tiene un endpoint completo (`POST /users`) con todas las capas implementadas como ejemplo de la sintaxis.

El resto de los métodos (`GET`, `PUT`, `DELETE`) y los demás dominios (`products`, `auth`) están con `...` / `pass` / comentarios `TODO`. **Tu trabajo es completarlos** siguiendo el patrón del ejemplo.

---

## Reglas de la arquitectura

1. `routers` no tocan la BD.
2. `services` no tocan `Request` / `Response`.
3. `repositories` no tienen lógica de negocio.
4. `models` no salen del repository / service.
5. `schemas` solo en routers.
6. Al cliente siempre va un DTO, nunca un Model.
