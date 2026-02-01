#!/usr/bin/env python3
"""
Script de prueba para la REST API del widget de Actual Budget.

Uso:
    python test_rest_api.py [server_url] [password] [file_name] [encryption_password]

Ejemplo:
    python test_rest_api.py https://actual.local mypassword "My Budget" myencryptionkey
"""

import sys
import requests
from typing import Optional


class Colors:
    """Colores ANSI para terminal."""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_header(text: str):
    """Imprime un header colorido."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text:^60}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_success(text: str):
    """Imprime un mensaje de éxito."""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_error(text: str):
    """Imprime un mensaje de error."""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")


def print_info(text: str):
    """Imprime un mensaje de información."""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.NC}")


def test_health_check(api_url: str) -> bool:
    """Prueba el endpoint de health check."""
    print_header("Test 1: Health Check")

    try:
        response = requests.get(f"{api_url}/")
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ok":
            print_success("Health check passed")
            print_info(f"Service: {data.get('service')}")
            return True
        else:
            print_error("Health check failed: invalid response")
            return False

    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False


def test_validate_connection(
    api_url: str,
    server_url: str,
    password: str,
    file_name: str,
    encryption_password: Optional[str]
) -> bool:
    """Prueba el endpoint de validación de conexión."""
    print_header("Test 2: Validate Connection")

    try:
        payload = {
            "server_url": server_url,
            "server_password": password,
            "file_name": file_name,
        }

        if encryption_password:
            payload["encryption_password"] = encryption_password

        response = requests.post(f"{api_url}/api/validate-connection", json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            print_success("Connection validated successfully")
            files = data.get("files", [])
            print_info(f"Found {len(files)} budget file(s):")
            for file in files:
                print(f"  - {file.get('name')} (ID: {file.get('file_id')})")
            return True
        else:
            print_error("Connection validation failed")
            return False

    except requests.exceptions.HTTPError as e:
        print_error(f"Connection validation failed: {e.response.text}")
        return False
    except Exception as e:
        print_error(f"Connection validation failed: {str(e)}")
        return False


def test_monthly_balance(
    api_url: str,
    server_url: str,
    password: str,
    file_name: str,
    encryption_password: Optional[str]
) -> bool:
    """Prueba el endpoint de balance mensual."""
    print_header("Test 3: Monthly Balance")

    try:
        payload = {
            "server_url": server_url,
            "server_password": password,
            "file_name": file_name,
        }

        if encryption_password:
            payload["encryption_password"] = encryption_password

        response = requests.post(f"{api_url}/api/monthly-balance", json=payload)
        response.raise_for_status()
        data = response.json()

        print_success("Monthly balance retrieved successfully")
        print_info(f"Month: {data.get('month')}")
        print_info(f"Total spent: €{data.get('total_spent', 0):.2f}")
        print_info(f"Total budgeted: €{data.get('total_budgeted', 0):.2f}")
        print_info(f"Total balance: €{data.get('total_balance', 0):.2f}")

        categories = data.get('categories', [])
        print_info(f"Categories: {len(categories)}")

        if categories:
            print("\n  Top 5 spending categories:")
            sorted_categories = sorted(
                categories,
                key=lambda x: abs(x.get('spent', 0)),
                reverse=True
            )
            for i, cat in enumerate(sorted_categories[:5], 1):
                spent = cat.get('spent', 0)
                budgeted = cat.get('budgeted', 0)
                print(f"    {i}. {cat.get('category_name')} ({cat.get('group_name')})")
                print(f"       Spent: €{abs(spent):.2f} / Budgeted: €{budgeted:.2f}")

        return True

    except requests.exceptions.HTTPError as e:
        print_error(f"Monthly balance failed: {e.response.text}")
        return False
    except Exception as e:
        print_error(f"Monthly balance failed: {str(e)}")
        return False


def test_list_accounts(
    api_url: str,
    server_url: str,
    password: str,
    file_name: str,
    encryption_password: Optional[str]
) -> bool:
    """Prueba el endpoint de listar cuentas."""
    print_header("Test 4: List Accounts")

    try:
        payload = {
            "server_url": server_url,
            "server_password": password,
            "file_name": file_name,
        }

        if encryption_password:
            payload["encryption_password"] = encryption_password

        response = requests.post(f"{api_url}/api/accounts", json=payload)
        response.raise_for_status()
        data = response.json()

        accounts = data.get('accounts', [])
        print_success(f"Found {len(accounts)} account(s)")

        for acc in accounts:
            status = "closed" if acc.get('closed') else "open"
            offbudget = " (off-budget)" if acc.get('offbudget') else ""
            print(f"  - {acc.get('name')} [{status}]{offbudget}")

        return True

    except requests.exceptions.HTTPError as e:
        print_error(f"List accounts failed: {e.response.text}")
        return False
    except Exception as e:
        print_error(f"List accounts failed: {str(e)}")
        return False


def main():
    """Función principal."""
    print_header("Actual Budget REST API - Test Suite")

    # Parse arguments
    api_url = "http://localhost:8080"

    if len(sys.argv) < 4:
        print_error("Missing required arguments")
        print("\nUsage:")
        print(f"  {sys.argv[0]} <server_url> <password> <file_name> [encryption_password]")
        print("\nExample:")
        print(f'  {sys.argv[0]} https://actual.local mypassword "My Budget" myencryptionkey')
        print("\nOr run with environment variables:")
        print("  export ACTUAL_SERVER_URL=https://actual.local")
        print("  export ACTUAL_PASSWORD=mypassword")
        print("  export ACTUAL_FILE_NAME='My Budget'")
        print("  export ACTUAL_ENCRYPTION_PASSWORD=myencryptionkey  # optional")
        sys.exit(1)

    server_url = sys.argv[1]
    password = sys.argv[2]
    file_name = sys.argv[3]
    encryption_password = sys.argv[4] if len(sys.argv) > 4 else None

    print_info(f"API URL: {api_url}")
    print_info(f"Actual Budget Server: {server_url}")
    print_info(f"File Name: {file_name}")
    print_info(f"Encryption: {'Yes' if encryption_password else 'No'}")

    # Run tests
    tests = [
        ("Health Check", lambda: test_health_check(api_url)),
        ("Validate Connection", lambda: test_validate_connection(
            api_url, server_url, password, file_name, encryption_password
        )),
        ("Monthly Balance", lambda: test_monthly_balance(
            api_url, server_url, password, file_name, encryption_password
        )),
        ("List Accounts", lambda: test_list_accounts(
            api_url, server_url, password, file_name, encryption_password
        )),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.NC}")

    if passed == total:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
