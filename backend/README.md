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

## Funcionalidades del broker

Las rutas de negocio se publican bajo `/api`:

- `POST /inversores`: da de alta al inversor y crea automáticamente una cuenta
  comitente con ambos saldos en cero. `PATCH /inversores/{id}/perfil` cambia
  su perfil de riesgo.
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
