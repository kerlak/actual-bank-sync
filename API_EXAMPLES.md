# Ejemplos de Uso de la REST API

Ejemplos de cómo usar la REST API del widget de Actual Budget.

## Requisitos

- Servidor REST API ejecutándose en `http://localhost:8080`
- Servidor Actual Budget configurado y funcionando
- Herramientas: `curl`, `httpie`, o cualquier cliente HTTP

## Endpoints Disponibles

### 1. Health Check

Verifica que el servidor está funcionando.

```bash
curl http://localhost:8080/
```

**Respuesta:**
```json
{
    "status": "ok",
    "service": "Actual Budget Widget API"
}
```

### 2. Validar Conexión

Valida la conexión al servidor de Actual Budget y lista los archivos disponibles.

**cURL:**
```bash
curl -X POST http://localhost:8080/api/validate-connection \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://actual.midominio.com",
    "server_password": "mi_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": "mi_clave_cifrado"
  }'
```

**HTTPie:**
```bash
http POST http://localhost:8080/api/validate-connection \
  server_url="https://actual.midominio.com" \
  server_password="mi_contraseña" \
  file_name="Mi Presupuesto" \
  encryption_password="mi_clave_cifrado"
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8080/api/validate-connection",
    json={
        "server_url": "https://actual.midominio.com",
        "server_password": "mi_contraseña",
        "file_name": "Mi Presupuesto",
        "encryption_password": "mi_clave_cifrado"
    }
)

print(response.json())
```

**Respuesta exitosa:**
```json
{
    "success": true,
    "files": [
        {
            "name": "Mi Presupuesto",
            "file_id": "abc123"
        },
        {
            "name": "Presupuesto 2025",
            "file_id": "def456"
        }
    ]
}
```

**Respuesta con error:**
```json
{
    "detail": "Failed to connect: Incorrect password"
}
```

### 3. Balance Mensual

Obtiene el balance del mes actual por categorías.

**cURL (mes actual):**
```bash
curl -X POST http://localhost:8080/api/monthly-balance \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://actual.midominio.com",
    "server_password": "mi_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": "mi_clave_cifrado"
  }'
```

**cURL (mes específico):**
```bash
curl -X POST "http://localhost:8080/api/monthly-balance?month=2025-12" \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://actual.midominio.com",
    "server_password": "mi_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": "mi_clave_cifrado"
  }'
```

**HTTPie:**
```bash
http POST http://localhost:8080/api/monthly-balance \
  month==2026-01 \
  server_url="https://actual.midominio.com" \
  server_password="mi_contraseña" \
  file_name="Mi Presupuesto" \
  encryption_password="mi_clave_cifrado"
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://localhost:8080/api/monthly-balance', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        server_url: 'https://actual.midominio.com',
        server_password: 'mi_contraseña',
        file_name: 'Mi Presupuesto',
        encryption_password: 'mi_clave_cifrado'
    })
});

const data = await response.json();
console.log(data);
```

**Respuesta:**
```json
{
    "month": "2026-01",
    "categories": [
        {
            "category_id": "cat_001",
            "category_name": "Alimentación",
            "group_name": "Necesidades",
            "spent": 450.50,
            "budgeted": 500.00,
            "balance": 49.50
        },
        {
            "category_id": "cat_002",
            "category_name": "Transporte",
            "group_name": "Necesidades",
            "spent": 120.00,
            "budgeted": 150.00,
            "balance": 30.00
        },
        {
            "category_id": "cat_003",
            "category_name": "Entretenimiento",
            "group_name": "Ocio",
            "spent": 180.75,
            "budgeted": 150.00,
            "balance": -30.75
        }
    ],
    "total_spent": 751.25,
    "total_budgeted": 800.00,
    "total_balance": 48.75
}
```

### 4. Listar Cuentas

Lista todas las cuentas disponibles en el archivo de presupuesto.

**cURL:**
```bash
curl -X POST http://localhost:8080/api/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://actual.midominio.com",
    "server_password": "mi_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": "mi_clave_cifrado"
  }'
```

**Respuesta:**
```json
{
    "accounts": [
        {
            "id": "acc_001",
            "name": "Ibercaja común",
            "closed": false,
            "offbudget": false
        },
        {
            "id": "acc_002",
            "name": "ING Nómina",
            "closed": false,
            "offbudget": false
        },
        {
            "id": "acc_003",
            "name": "Ahorros",
            "closed": false,
            "offbudget": true
        }
    ]
}
```

## Ejemplos con Archivo NO Cifrado

Si tu archivo de presupuesto NO está cifrado, omite el campo `encryption_password`:

```bash
curl -X POST http://localhost:8080/api/monthly-balance \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://actual.midominio.com",
    "server_password": "mi_contraseña",
    "file_name": "Mi Presupuesto"
  }'
```

## Pruebas con Postman

### Colección de Postman

Importa esta colección JSON en Postman:

```json
{
    "info": {
        "name": "Actual Budget Widget API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "url": "http://localhost:8080/"
            }
        },
        {
            "name": "Validate Connection",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"server_url\": \"https://actual.midominio.com\",\n    \"server_password\": \"mi_contraseña\",\n    \"file_name\": \"Mi Presupuesto\",\n    \"encryption_password\": \"mi_clave_cifrado\"\n}"
                },
                "url": "http://localhost:8080/api/validate-connection"
            }
        },
        {
            "name": "Monthly Balance",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"server_url\": \"https://actual.midominio.com\",\n    \"server_password\": \"mi_contraseña\",\n    \"file_name\": \"Mi Presupuesto\",\n    \"encryption_password\": \"mi_clave_cifrado\"\n}"
                },
                "url": "http://localhost:8080/api/monthly-balance"
            }
        },
        {
            "name": "List Accounts",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"server_url\": \"https://actual.midominio.com\",\n    \"server_password\": \"mi_contraseña\",\n    \"file_name\": \"Mi Presupuesto\",\n    \"encryption_password\": \"mi_clave_cifrado\"\n}"
                },
                "url": "http://localhost:8080/api/accounts"
            }
        }
    ]
}
```

## Variables de Entorno

Para facilitar las pruebas, puedes usar variables de entorno:

**Bash:**
```bash
export ACTUAL_SERVER_URL="https://actual.midominio.com"
export ACTUAL_PASSWORD="mi_contraseña"
export ACTUAL_FILE_NAME="Mi Presupuesto"
export ACTUAL_ENCRYPTION_PASSWORD="mi_clave_cifrado"

curl -X POST http://localhost:8080/api/monthly-balance \
  -H "Content-Type: application/json" \
  -d "{
    \"server_url\": \"$ACTUAL_SERVER_URL\",
    \"server_password\": \"$ACTUAL_PASSWORD\",
    \"file_name\": \"$ACTUAL_FILE_NAME\",
    \"encryption_password\": \"$ACTUAL_ENCRYPTION_PASSWORD\"
  }"
```

## Manejo de Errores

### Error 400: Bad Request

**Causa:** Parámetros incorrectos o faltantes

**Ejemplo:**
```json
{
    "detail": "Failed to connect: Unable to decrypt file with the provided password"
}
```

### Error 500: Internal Server Error

**Causa:** Error en el servidor o en Actual Budget

**Ejemplo:**
```json
{
    "detail": "Failed to get monthly balance: Connection refused"
}
```

### Error 401: Unauthorized

**Causa:** Contraseña del servidor incorrecta

**Ejemplo:**
```json
{
    "detail": "Incorrect password"
}
```

## Integración en Otras Apps

### React Native

```javascript
import axios from 'axios';

const getMonthlyBalance = async () => {
    try {
        const response = await axios.post('http://192.168.1.100:8080/api/monthly-balance', {
            server_url: 'https://actual.midominio.com',
            server_password: 'mi_contraseña',
            file_name: 'Mi Presupuesto',
            encryption_password: 'mi_clave_cifrado'
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};
```

### Android (Kotlin)

```kotlin
import okhttp3.*
import com.google.gson.Gson

data class AuthConfig(
    val server_url: String,
    val server_password: String,
    val file_name: String,
    val encryption_password: String?
)

fun getMonthlyBalance() {
    val client = OkHttpClient()
    val gson = Gson()

    val config = AuthConfig(
        server_url = "https://actual.midominio.com",
        server_password = "mi_contraseña",
        file_name = "Mi Presupuesto",
        encryption_password = "mi_clave_cifrado"
    )

    val json = gson.toJson(config)
    val body = RequestBody.create(
        MediaType.parse("application/json"),
        json
    )

    val request = Request.Builder()
        .url("http://192.168.1.100:8080/api/monthly-balance")
        .post(body)
        .build()

    client.newCall(request).enqueue(object : Callback {
        override fun onResponse(call: Call, response: Response) {
            val responseData = response.body()?.string()
            println(responseData)
        }

        override fun onFailure(call: Call, e: IOException) {
            e.printStackTrace()
        }
    })
}
```

## Documentación Interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

Puedes probar todos los endpoints directamente desde el navegador.

## Notas de Seguridad

1. **NO** expongas la API a Internet sin autenticación adicional
2. **NO** hardcodees credenciales en el código
3. **USA** HTTPS en producción
4. **LIMITA** CORS a orígenes específicos en producción
5. **CONSIDERA** añadir rate limiting

## Soporte

Para más ejemplos o ayuda:
- Consulta la documentación de FastAPI: https://fastapi.tiangolo.com
- Consulta la documentación de actualpy: https://github.com/bvanelli/actualpy
- Abre un issue en el repositorio

---

Última actualización: 2026-01-30
