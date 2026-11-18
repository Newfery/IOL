from decimal import Decimal
from uuid import uuid4

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models.aporte_grupo_model import AporteGrupo
from src.db.models.activos_model import Activo
from src.db.models.cuenta_model import Cuenta
from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.grupo_inversor_model import GrupoInversor
from src.db.models.inversor_model import Inversor
from src.db.models.operacion_model import Operacion
from src.db.models.tenencia_grupo_model import TenenciaGrupo
from src.middlewares.auth_middleware import get_current_inversor
from src.schemas.frontend_schema import (
    GroupContributionRequest,
    GroupCredentialsRequest,
    GroupOperationRequest,
    OrderRequest,
)
from src.services.operacion_service import OperacionService
from src.services.cotizacion_service import CotizacionService
from src.utils.errors import NotFoundError
from src.utils.hash import hash_password, verify_password

router = APIRouter(tags=["frontend"])


def _group_payload(db: Session, group: GrupoDeInversion) -> dict:
    memberships = db.query(GrupoInversor, Inversor).join(
        Inversor, Inversor.id == GrupoInversor.inversor_id
    ).filter(GrupoInversor.grupo_id == group.id).all()
    totals = dict(db.query(AporteGrupo.inversor_id, func.coalesce(func.sum(AporteGrupo.monto), 0))
                  .filter(AporteGrupo.grupo_id == group.id)
                  .group_by(AporteGrupo.inversor_id).all())
    holdings = db.query(TenenciaGrupo, Activo).join(
        Activo, Activo.id == TenenciaGrupo.activo_id
    ).filter(TenenciaGrupo.grupo_id == group.id).all()
    return {
        "id": str(group.id), "name": group.nombre, "code": group.codigo_union,
        "cash": float(group.plata_disponible),
        "members": [{"name": investor.nombre, "contributed": float(totals.get(investor.id, 0))}
                    for _, investor in memberships],
        "holdings": [{"symbol": asset.ticker, "qty": float(holding.cantidad),
                      "avgPrice": float(holding.precio_promedio)} for holding, asset in holdings],
    }


@router.get("/market/assets")
def market_assets(db: Session = Depends(get_db)):
    assets = db.query(Activo).filter(Activo.activo.is_(True)).order_by(Activo.ticker).all()
    type_names = {"accion": "Acción", "cedear": "CEDEAR", "bono": "Bono"}
    result = []
    for asset in assets:
        change = 0.0
        try:
            market_symbol = asset.ticker if "." in asset.ticker else f"{asset.ticker}.BA"
            quote = CotizacionService.obtener(market_symbol)
            if quote.variacion_porcentual is not None:
                change = float(quote.variacion_porcentual)
        except Exception:
            # Se conserva el último precio guardado si el proveedor no está disponible.
            pass
        result.append({"symbol": asset.ticker, "name": asset.nombre,
                       "price": float(asset.precio_actual), "change": change,
                       "type": type_names.get(asset.tipo, "FCI")})
    return result


@router.get("/market/assets/{symbol}/history")
def market_asset_history(symbol: str):
    ticker = symbol.strip().upper()
    market_symbol = ticker if "." in ticker else f"{ticker}.BA"
    try:
        history = yf.Ticker(market_symbol).history(period="1y", interval="1d", auto_adjust=False)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="No se pudo consultar el historial") from exc
    if history.empty or "Close" not in history:
        raise NotFoundError(f"No se encontraron cotizaciones para {ticker}")
    return [{"date": date.isoformat(), "price": float(price)}
            for date, price in history["Close"].dropna().items()]


@router.get("/market/dolar")
def market_dolar(db: Session = Depends(get_db)):
    by_ticker = {a.ticker: Decimal(str(a.precio_actual)) for a in db.query(Activo).filter(
        Activo.ticker.in_(["AL30", "AL30D", "GD30", "GD30C"]), Activo.activo.is_(True)
    ).all()}
    mep = by_ticker.get("AL30") and by_ticker.get("AL30D")
    ccl = by_ticker.get("GD30") and by_ticker.get("GD30C")
    if not mep or not ccl:
        raise NotFoundError("No están cargados los bonos necesarios para calcular MEP y CCL")
    return {"mep": float(by_ticker["AL30"] / by_ticker["AL30D"]),
            "ccl": float(by_ticker["GD30"] / by_ticker["GD30C"])}


@router.get("/inversores/{inversor_id}/cuenta")
def account_for_inversor(inversor_id: int, db: Session = Depends(get_db),
                         current: Inversor = Depends(get_current_inversor)):
    if current.id != inversor_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    account = db.query(Cuenta).filter(Cuenta.inversor_id == inversor_id).first()
    if account is None:
        raise NotFoundError("Cuenta no encontrada")
    return account


@router.get("/account/balance")
def account_balance(db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    if account is None:
        raise NotFoundError("Cuenta no encontrada")
    return {"ars": float(account.saldo_ars), "usd": float(account.saldo_usd)}


@router.get("/cuenta/plazos")
def account_plazos(db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    if account is None:
        raise NotFoundError("Cuenta no encontrada")
    pending = db.query(Operacion).filter(Operacion.cuenta_id == account.id,
        Operacion.estado == "pendiente").all()
    committed = {"ARS": Decimal("0"), "USD": Decimal("0")}
    for op in pending:
        asset = db.query(Activo).filter(Activo.id == op.activo_id).first()
        if asset:
            committed[str(asset.moneda)] += Decimal(str(op.total))
    return [
        {"label": "Disponible para operar", "detalle": "Liquidación inmediata",
         "ars": max(0, float(account.saldo_ars) - float(committed["ARS"])),
         "usd": max(0, float(account.saldo_usd) - float(committed["USD"]))},
        {"label": "En liquidación (24 hs)", "detalle": "Operaciones con liquidación a 24 hs", "ars": 0, "usd": 0},
        {"label": "En liquidación (48 hs)", "detalle": "Operaciones con liquidación a 48 hs", "ars": 0, "usd": 0},
    ]


@router.get("/ordenes/pendientes")
def pending_orders(db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    if account is None:
        raise NotFoundError("Cuenta no encontrada")
    rows = db.query(Operacion, Activo).join(Activo, Activo.id == Operacion.activo_id).filter(
        Operacion.cuenta_id == account.id, Operacion.estado == "pendiente").all()
    return [{"desc": f"{op.tipo.title()} {asset.ticker} x{op.cantidad}",
             "ars": float(op.total) if asset.moneda == "ARS" else 0,
             "usd": float(op.total) if asset.moneda == "USD" else 0} for op, asset in rows]


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    if account is None:
        raise NotFoundError("Cuenta no encontrada")
    from src.db.models.tenencia_model import Tenencia
    holdings = db.query(Tenencia, Activo).join(Activo, Activo.id == Tenencia.activo_id).filter(
        Tenencia.cuenta_id == account.id).all()
    return [{"symbol": asset.ticker, "qty": float(holding.cantidad),
             "avgPrice": float(holding.precio_promedio)} for holding, asset in holdings]


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderRequest, db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    symbol, side = payload.symbol, payload.side
    qty, price = payload.qty, payload.price
    if side not in ("buy", "sell") or qty <= 0 or price <= 0:
        raise HTTPException(status_code=422, detail="Orden inválida")
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    asset = db.query(Activo).filter(Activo.ticker == symbol, Activo.activo.is_(True)).first()
    if account is None or asset is None:
        raise NotFoundError("Cuenta o activo no encontrado")
    operation = (OperacionService.comprar if side == "buy" else OperacionService.vender)(
        db, account.id, asset.id, qty)
    return {"ok": True, "id": str(operation.id)}


@router.get("/grupos")
def my_groups(db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    groups = db.query(GrupoDeInversion).join(GrupoInversor,
        GrupoInversor.grupo_id == GrupoDeInversion.id).filter(
        GrupoInversor.inversor_id == current.id).order_by(GrupoDeInversion.id).all()
    return [_group_payload(db, group) for group in groups]


@router.post("/grupos", status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCredentialsRequest, db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    name, password = payload.nombre.strip(), payload.password
    if not name:
        raise HTTPException(status_code=422, detail="El nombre no puede quedar vacío")
    if db.query(GrupoDeInversion).filter(GrupoDeInversion.nombre == name).first():
        raise HTTPException(status_code=409, detail="Ya existe un grupo con ese nombre")
    group = GrupoDeInversion(nombre=name, codigo_union=uuid4().hex[:10].upper(),
        password_hash=hash_password(password), creador_id=current.id, plata_disponible=0)
    db.add(group); db.flush()
    db.add(GrupoInversor(grupo_id=group.id, inversor_id=current.id)); db.commit(); db.refresh(group)
    return _group_payload(db, group)


@router.post("/grupos/unirse")
def join_group(payload: GroupCredentialsRequest, db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    name, password = payload.nombre.strip(), payload.password
    group = db.query(GrupoDeInversion).filter(GrupoDeInversion.nombre == name).first()
    if group is None or not group.password_hash or not verify_password(password, group.password_hash):
        raise HTTPException(status_code=401, detail="Nombre de grupo o contraseña incorrectos")
    membership = db.get(GrupoInversor, (group.id, current.id))
    if membership is None:
        db.add(GrupoInversor(grupo_id=group.id, inversor_id=current.id)); db.commit()
    return _group_payload(db, group)


@router.post("/grupos/{group_id}/aportes")
def contribute_group(group_id: int, payload: GroupContributionRequest, db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    amount = payload.monto
    group = db.get(GrupoDeInversion, group_id)
    membership = db.get(GrupoInversor, (group_id, current.id))
    account = db.query(Cuenta).filter(Cuenta.inversor_id == current.id).first()
    if group is None: raise NotFoundError("Grupo no encontrado")
    if membership is None: raise HTTPException(status_code=403, detail="No pertenecés al grupo")
    if amount <= 0: raise HTTPException(status_code=422, detail="El aporte debe ser mayor a cero")
    if account is None or Decimal(str(account.saldo_ars)) < amount:
        raise HTTPException(status_code=400, detail="Saldo ARS insuficiente para aportar")
    try:
        account.saldo_ars = Decimal(str(account.saldo_ars)) - amount
        group.plata_disponible = Decimal(str(group.plata_disponible)) + amount
        db.add(AporteGrupo(grupo_id=group_id, inversor_id=current.id, monto=amount)); db.commit()
    except Exception:
        db.rollback(); raise
    return _group_payload(db, group)


@router.post("/grupos/{group_id}/operaciones")
def group_operation(group_id: int, payload: GroupOperationRequest, db: Session = Depends(get_db), current: Inversor = Depends(get_current_inversor)):
    group = db.get(GrupoDeInversion, group_id)
    if group is None: raise NotFoundError("Grupo no encontrado")
    if db.get(GrupoInversor, (group_id, current.id)) is None:
        raise HTTPException(status_code=403, detail="No pertenecés al grupo")
    ticker = payload.ticker.upper()
    quantity = payload.cantidad
    asset = db.query(Activo).filter(Activo.ticker == ticker, Activo.activo.is_(True)).first()
    if asset is None: raise NotFoundError("Activo no encontrado")
    if quantity <= 0: raise HTTPException(status_code=422, detail="La cantidad debe ser mayor a cero")
    price = Decimal(str(asset.precio_actual)); gross = quantity * price
    total = (gross * Decimal("1.005")).quantize(Decimal("0.01"))
    if Decimal(str(group.plata_disponible)) < total:
        raise HTTPException(status_code=400, detail="El pozo del grupo no alcanza")
    holding = db.query(TenenciaGrupo).filter_by(grupo_id=group_id, activo_id=asset.id).first()
    if holding:
        old_qty = Decimal(str(holding.cantidad)); new_qty = old_qty + quantity
        holding.precio_promedio = (old_qty * Decimal(str(holding.precio_promedio)) + gross) / new_qty
        holding.cantidad = new_qty
    else:
        db.add(TenenciaGrupo(grupo_id=group_id, activo_id=asset.id, cantidad=quantity, precio_promedio=price))
    group.plata_disponible = Decimal(str(group.plata_disponible)) - total
    db.commit(); db.refresh(group)
    return _group_payload(db, group)
