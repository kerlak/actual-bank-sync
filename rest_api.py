"""REST API server for Actual Budget PWA."""

import os
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from actual import Actual
from actual.queries import get_accounts, get_budgets, get_categories, get_category_groups, get_transactions


app = FastAPI(title="Actual Budget Widget API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthConfig(BaseModel):
    server_url: str
    server_password: str
    file_name: str
    encryption_password: Optional[str] = None


@app.get("/")
async def root():
    return {"status": "ok", "service": "Actual Budget Widget API", "version": "2.0.0"}


@app.post("/api/validate")
async def validate_connection(config: AuthConfig):
    """Validate connection to Actual Budget server."""
    try:
        with Actual(
            base_url=config.server_url,
            password=config.server_password,
            cert=False  # Disable SSL verification
        ) as actual:
            files = actual.list_user_files()
            return {
                "success": True,
                "files": [{"name": f.name, "file_id": f.file_id} for f in files.data]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/accounts")
async def get_accounts_list(config: AuthConfig):
    """Get list of accounts with their balances."""
    try:
        with Actual(
            base_url=config.server_url,
            password=config.server_password,
            encryption_password=config.encryption_password,
            file=config.file_name,
            cert=False
        ) as actual:
            actual.download_budget()

            accounts = get_accounts(actual.session)

            result = []
            total_balance = 0.0

            # Debug: print first account info
            if accounts:
                sample = accounts[0]
                print(f"[DEBUG] Sample account attributes: {[a for a in dir(sample) if not a.startswith('_')]}")
                print(f"[DEBUG] Sample balance: {getattr(sample, 'balance', 'NO ATTR')}")
                print(f"[DEBUG] Sample balance type: {type(getattr(sample, 'balance', None))}")
                if hasattr(sample, 'balance'):
                    print(f"[DEBUG] Is it callable? {callable(sample.balance)}")

            for acc in accounts:
                if acc.tombstone or acc.closed:
                    continue

                # Get balance - already in correct format (not cents)
                balance = 0.0
                if hasattr(acc, 'balance'):
                    balance_val = acc.balance
                    # Check if it's a method or property
                    if callable(balance_val):
                        balance_val = balance_val()
                    # Convert to float (balance is already in correct format)
                    balance = float(balance_val) if balance_val else 0.0
                    print(f"[DEBUG] Account {acc.name}: balance={balance}")

                result.append({
                    "id": acc.id,
                    "name": acc.name,
                    "balance": balance,
                    "off_budget": bool(acc.offbudget) if hasattr(acc, 'offbudget') else False,
                    "closed": bool(acc.closed)
                })

                # Only count on-budget accounts in total
                if not (hasattr(acc, 'offbudget') and acc.offbudget):
                    total_balance += balance

            # Sort: on-budget first, then by name
            result.sort(key=lambda a: (a["off_budget"], a["name"]))

            return {
                "accounts": result,
                "total_balance": total_balance,
                "count": len(result)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/budget")
async def get_monthly_budget(config: AuthConfig, month: Optional[str] = Query(None)):
    """Get budget data for a specific month."""
    try:
        if month:
            target_date = datetime.strptime(month, "%Y-%m").date()
        else:
            target_date = date.today()

        with Actual(
            base_url=config.server_url,
            password=config.server_password,
            encryption_password=config.encryption_password,
            file=config.file_name,
            cert=False  # Disable SSL verification
        ) as actual:
            actual.download_budget()

            groups = get_category_groups(actual.session)
            categories = get_categories(actual.session)
            budgets = get_budgets(actual.session, month=target_date)

            budget_map = {b.category_id: b for b in budgets}

            result_groups = []

            for group in groups:
                if group.tombstone:
                    continue

                group_cats = []
                group_budgeted = 0.0
                group_spent = 0.0

                for cat in categories:
                    if cat.cat_group != group.id or cat.tombstone:
                        continue

                    budget = budget_map.get(cat.id)

                    if budget:
                        budgeted = float(budget.get_amount())
                        # balance: negativo = gasto, positivo = ingreso
                        # Mantenemos el signo: spent negativo = gasto, spent positivo = ingreso
                        spent = float(budget.balance)
                        carryover = float(budget.carryover or 0) / 100
                    else:
                        budgeted = 0.0
                        spent = 0.0
                        carryover = 0.0

                    # available = presupuesto + lo que queda (spent negativo resta, positivo suma)
                    available = budgeted + spent + carryover

                    # Progress solo para gastos (spent negativo) con presupuesto
                    if budgeted > 0 and spent < 0:
                        progress = (abs(spent) / budgeted * 100)
                    else:
                        progress = 0

                    group_cats.append({
                        "id": cat.id,
                        "name": cat.name,
                        "budgeted": budgeted,
                        "spent": spent,
                        "available": available,
                        "progress": min(progress, 100),
                        "overspent": spent < 0 and abs(spent) > budgeted and budgeted > 0
                    })

                    group_budgeted += budgeted
                    group_spent += spent

                if group_cats:
                    result_groups.append({
                        "id": group.id,
                        "name": group.name,
                        "is_income": bool(group.is_income),
                        "budgeted": group_budgeted,
                        "spent": group_spent,
                        "available": group_budgeted + group_spent,  # spent negativo resta
                        "categories": sorted(group_cats, key=lambda c: c["name"])
                    })

            result_groups.sort(key=lambda g: (not g["is_income"], g["name"]))

            expense_groups = [g for g in result_groups if not g["is_income"]]
            total_budgeted = sum(g["budgeted"] for g in expense_groups)
            total_spent = sum(g["spent"] for g in expense_groups)  # será negativo

            return {
                "month": target_date.strftime("%Y-%m"),
                "groups": result_groups,
                "total_budgeted": total_budgeted,
                "total_spent": total_spent,  # negativo = gastos
                "total_available": total_budgeted + total_spent  # spent negativo resta
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions")
async def get_category_transactions(
    config: AuthConfig,
    category_id: str = Query(...),
    month: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """Get transactions for a specific category in a month."""
    try:
        if month:
            target_date = datetime.strptime(month, "%Y-%m").date()
        else:
            target_date = date.today()

        # Calculate month start and end
        start_date = target_date.replace(day=1)
        if target_date.month == 12:
            end_date = target_date.replace(year=target_date.year + 1, month=1, day=1)
        else:
            end_date = target_date.replace(month=target_date.month + 1, day=1)

        print(f"[DEBUG] Date range: {start_date} to {end_date}")

        with Actual(
            base_url=config.server_url,
            password=config.server_password,
            encryption_password=config.encryption_password,
            file=config.file_name,
            cert=False
        ) as actual:
            actual.download_budget()

            # Get category info
            categories = get_categories(actual.session)
            print(f"[DEBUG] All category IDs: {[(c.name, c.id) for c in categories[:5]]}")
            print(f"[DEBUG] Searching for category_id: '{category_id}'")

            # Find the category object by ID
            category = next((c for c in categories if str(c.id) == str(category_id)), None)
            if not category:
                raise HTTPException(status_code=404, detail=f"Categoría no encontrada: {category_id}")

            print(f"[DEBUG] Found category: {category.name} (id={category.id})")

            # Use get_transactions with category filter (native filtering)
            filtered = get_transactions(
                actual.session,
                start_date=start_date,
                end_date=end_date,
                category=category  # Pass category object for native filtering
            )

            print(f"[DEBUG] Filtered transactions with native filter: {len(filtered)}")

            # If no transactions found, also try without category filter to debug
            if len(filtered) == 0:
                all_trans = get_transactions(
                    actual.session,
                    start_date=start_date,
                    end_date=end_date
                )
                print(f"[DEBUG] Total transactions in range (no filter): {len(all_trans)}")
                if all_trans:
                    # Show first 3 transactions with their categories
                    for i, t in enumerate(all_trans[:3]):
                        t_cat_id = getattr(t, 'category_id', None)
                        t_cat_name = getattr(t.category, 'name', None) if hasattr(t, 'category') and t.category else None
                        print(f"[DEBUG] Transaction {i}: cat_id={t_cat_id}, cat_name={t_cat_name}")

            # Format transactions
            result = []
            for t in filtered[:limit]:
                try:
                    # Get amount safely using get_amount() method
                    if hasattr(t, 'get_amount'):
                        amount = float(t.get_amount())
                    elif hasattr(t, 'amount') and t.amount is not None:
                        amount = float(t.amount) / 100
                    else:
                        amount = 0.0

                    # Get date safely using get_date() method
                    trans_date = None
                    if hasattr(t, 'get_date'):
                        d = t.get_date()
                        trans_date = d.isoformat() if d else None
                    elif hasattr(t, 'date') and t.date:
                        # Fallback: if date is already a date object
                        if hasattr(t.date, 'isoformat'):
                            trans_date = t.date.isoformat()
                        else:
                            trans_date = str(t.date)

                    result.append({
                        "id": t.id,
                        "date": trans_date,
                        "payee": t.payee.name if t.payee else None,
                        "notes": t.notes or "",
                        "amount": amount,
                        "account": t.account.name if t.account else None,
                    })
                except Exception as ex:
                    print(f"[DEBUG] Error formatting transaction: {ex}")
                    # Skip problematic transactions
                    continue

            return {
                "category_id": category_id,
                "category_name": category.name,
                "month": target_date.strftime("%Y-%m"),
                "transactions": result,
                "count": len(result)
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Serve PWA static files
PWA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pwa")

@app.get("/app")
async def serve_app():
    return FileResponse(os.path.join(PWA_DIR, "index.html"), media_type="text/html")

@app.get("/app/{filename:path}")
async def serve_static(filename: str):
    filepath = os.path.join(PWA_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    print(f"PWA directory: {PWA_DIR}")
    print(f"Files in PWA: {os.listdir(PWA_DIR) if os.path.exists(PWA_DIR) else 'NOT FOUND'}")
    uvicorn.run(app, host="0.0.0.0", port=8080)
