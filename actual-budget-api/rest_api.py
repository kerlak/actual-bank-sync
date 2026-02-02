"""REST API server for Actual Budget with caching."""

import os
import hashlib
import time
from datetime import datetime, date
from typing import Optional
from threading import Lock

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from actual import Actual
from actual.queries import get_accounts, get_budgets, get_categories, get_category_groups, get_transactions


app = FastAPI(title="Actual Budget Widget API", version="3.0.0")

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


# =============================================================================
# CACHE SYSTEM
# =============================================================================

class BudgetCache:
    """Cache for Actual Budget session to avoid repeated downloads."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.ttl = ttl_seconds
        self._actual: Optional[Actual] = None
        self._config_hash: Optional[str] = None
        self._last_refresh: float = 0
        self._lock = Lock()

    def _get_config_hash(self, config: AuthConfig) -> str:
        """Generate hash from config to detect changes."""
        data = f"{config.server_url}|{config.file_name}|{config.encryption_password or ''}"
        return hashlib.md5(data.encode()).hexdigest()

    def _is_valid(self, config: AuthConfig) -> bool:
        """Check if cache is still valid."""
        if self._actual is None:
            return False
        if self._config_hash != self._get_config_hash(config):
            return False
        if time.time() - self._last_refresh > self.ttl:
            return False
        return True

    def get_session(self, config: AuthConfig) -> Actual:
        """Get cached session or create new one."""
        with self._lock:
            if not self._is_valid(config):
                self._refresh(config)
            return self._actual

    def _refresh(self, config: AuthConfig):
        """Download budget and cache the session."""
        # Close old session if exists
        if self._actual is not None:
            try:
                self._actual.__exit__(None, None, None)
            except:
                pass

        print(f"[CACHE] Downloading budget from {config.server_url}...")
        start = time.time()

        self._actual = Actual(
            base_url=config.server_url,
            password=config.server_password,
            encryption_password=config.encryption_password,
            file=config.file_name,
            cert=False
        )
        self._actual.__enter__()
        self._actual.download_budget()

        self._config_hash = self._get_config_hash(config)
        self._last_refresh = time.time()

        elapsed = time.time() - start
        print(f"[CACHE] Budget downloaded in {elapsed:.2f}s")

    def refresh(self, config: AuthConfig):
        """Force refresh the cache."""
        with self._lock:
            self._refresh(config)

    def invalidate(self):
        """Invalidate the cache."""
        with self._lock:
            if self._actual is not None:
                try:
                    self._actual.__exit__(None, None, None)
                except:
                    pass
            self._actual = None
            self._config_hash = None
            self._last_refresh = 0
            print("[CACHE] Cache invalidated")

    def get_status(self) -> dict:
        """Get cache status."""
        with self._lock:
            if self._actual is None:
                return {
                    "cached": False,
                    "age_seconds": None,
                    "ttl_seconds": self.ttl,
                    "expires_in": None
                }

            age = time.time() - self._last_refresh
            expires_in = max(0, self.ttl - age)

            return {
                "cached": True,
                "age_seconds": round(age, 1),
                "ttl_seconds": self.ttl,
                "expires_in": round(expires_in, 1),
                "last_refresh": datetime.fromtimestamp(self._last_refresh).isoformat()
            }


# Global cache instance
cache = BudgetCache(ttl_seconds=300)  # 5 minutes


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    status = cache.get_status()
    return {
        "status": "ok",
        "service": "Actual Budget Widget API",
        "version": "3.0.0",
        "cache": status
    }


@app.post("/api/cache/refresh")
async def refresh_cache(config: AuthConfig):
    """Force refresh the budget cache."""
    try:
        start = time.time()
        cache.refresh(config)
        elapsed = time.time() - start
        return {
            "success": True,
            "message": "Cache refreshed",
            "elapsed_seconds": round(elapsed, 2),
            "cache": cache.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/status")
async def cache_status():
    """Get current cache status."""
    return cache.get_status()


@app.post("/api/cache/invalidate")
async def invalidate_cache():
    """Invalidate the cache (next request will re-download)."""
    cache.invalidate()
    return {"success": True, "message": "Cache invalidated"}


@app.post("/api/validate")
async def validate_connection(config: AuthConfig):
    """Validate connection to Actual Budget server (does not use cache)."""
    try:
        with Actual(
            base_url=config.server_url,
            password=config.server_password,
            cert=False
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
        actual = cache.get_session(config)
        accounts = get_accounts(actual.session)

        result = []
        total_balance = 0.0

        for acc in accounts:
            if acc.tombstone or acc.closed:
                continue

            balance = 0.0
            if hasattr(acc, 'balance'):
                balance_val = acc.balance
                if callable(balance_val):
                    balance_val = balance_val()
                balance = float(balance_val) if balance_val else 0.0

            result.append({
                "id": acc.id,
                "name": acc.name,
                "balance": balance,
                "off_budget": bool(acc.offbudget) if hasattr(acc, 'offbudget') else False,
                "closed": bool(acc.closed)
            })

            if not (hasattr(acc, 'offbudget') and acc.offbudget):
                total_balance += balance

        result.sort(key=lambda a: (a["off_budget"], a["name"]))

        return {
            "accounts": result,
            "total_balance": total_balance,
            "count": len(result),
            "cached": cache.get_status()["cached"]
        }

    except Exception as e:
        cache.invalidate()  # Invalidate on error
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/budget")
async def get_monthly_budget(config: AuthConfig, month: Optional[str] = Query(None)):
    """Get budget data for a specific month."""
    try:
        if month:
            target_date = datetime.strptime(month, "%Y-%m").date()
        else:
            target_date = date.today()

        actual = cache.get_session(config)

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
                    spent = float(budget.balance)
                    carryover = float(budget.carryover or 0) / 100
                else:
                    budgeted = 0.0
                    spent = 0.0
                    carryover = 0.0

                available = budgeted + spent + carryover

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
                    "available": group_budgeted + group_spent,
                    "categories": sorted(group_cats, key=lambda c: c["name"])
                })

        result_groups.sort(key=lambda g: (not g["is_income"], g["name"]))

        expense_groups = [g for g in result_groups if not g["is_income"]]
        total_budgeted = sum(g["budgeted"] for g in expense_groups)
        total_spent = sum(g["spent"] for g in expense_groups)

        return {
            "month": target_date.strftime("%Y-%m"),
            "groups": result_groups,
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "total_available": total_budgeted + total_spent,
            "cached": cache.get_status()["cached"]
        }

    except Exception as e:
        cache.invalidate()
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

        start_date = target_date.replace(day=1)
        if target_date.month == 12:
            end_date = target_date.replace(year=target_date.year + 1, month=1, day=1)
        else:
            end_date = target_date.replace(month=target_date.month + 1, day=1)

        actual = cache.get_session(config)

        categories = get_categories(actual.session)
        category = next((c for c in categories if str(c.id) == str(category_id)), None)
        if not category:
            raise HTTPException(status_code=404, detail=f"Categoría no encontrada: {category_id}")

        filtered = get_transactions(
            actual.session,
            start_date=start_date,
            end_date=end_date,
            category=category
        )

        result = []
        for t in filtered[:limit]:
            try:
                if hasattr(t, 'get_amount'):
                    amount = float(t.get_amount())
                elif hasattr(t, 'amount') and t.amount is not None:
                    amount = float(t.amount) / 100
                else:
                    amount = 0.0

                trans_date = None
                if hasattr(t, 'get_date'):
                    d = t.get_date()
                    trans_date = d.isoformat() if d else None
                elif hasattr(t, 'date') and t.date:
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
            except:
                continue

        return {
            "category_id": category_id,
            "category_name": category.name,
            "month": target_date.strftime("%Y-%m"),
            "transactions": result,
            "count": len(result),
            "cached": cache.get_status()["cached"]
        }

    except HTTPException:
        raise
    except Exception as e:
        cache.invalidate()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions/by-note")
async def get_transactions_by_note(
    config: AuthConfig,
    note: str = Query(...),
    limit: int = Query(100)
):
    """Get all transactions with a specific note, grouped by month."""
    try:
        actual = cache.get_session(config)

        # Get all transactions (no date filter)
        all_transactions = get_transactions(actual.session)

        # Filter by note (case-insensitive partial match)
        note_lower = note.lower().strip()
        filtered = [
            t for t in all_transactions
            if t.notes and note_lower in t.notes.lower()
        ]

        # Sort by date descending (most recent first)
        def get_sort_date(t):
            if hasattr(t, 'get_date'):
                d = t.get_date()
                return d if d else date.min
            return date.min

        filtered.sort(key=get_sort_date, reverse=True)

        # Format transactions with category info
        result = []
        for t in filtered[:limit]:
            try:
                if hasattr(t, 'get_amount'):
                    amount = float(t.get_amount())
                elif hasattr(t, 'amount') and t.amount is not None:
                    amount = float(t.amount) / 100
                else:
                    amount = 0.0

                trans_date = None
                if hasattr(t, 'get_date'):
                    d = t.get_date()
                    trans_date = d.isoformat() if d else None
                elif hasattr(t, 'date') and t.date:
                    if hasattr(t.date, 'isoformat'):
                        trans_date = t.date.isoformat()
                    else:
                        trans_date = str(t.date)

                # Get category name
                category_name = None
                if hasattr(t, 'category') and t.category:
                    category_name = t.category.name

                result.append({
                    "id": t.id,
                    "date": trans_date,
                    "payee": t.payee.name if t.payee else None,
                    "notes": t.notes or "",
                    "amount": amount,
                    "account": t.account.name if t.account else None,
                    "category": category_name,
                })
            except:
                continue

        return {
            "note": note,
            "transactions": result,
            "count": len(result),
            "cached": cache.get_status()["cached"]
        }

    except Exception as e:
        cache.invalidate()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PWA STATIC FILES
# =============================================================================

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
    uvicorn.run(app, host="0.0.0.0", port=8080)
