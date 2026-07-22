# Guía de Consumo de API para Frontend Next.js

## Configuración Base

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TokenData {
  access_token: string
  token_type: string
}

interface Usuario {
  id: number
  username: string
  email: string
  telefono: string | null
  rol: string
  unidad_administrativa_id: number | null
  activo: boolean
}
```

---

## Autenticación

### 1. Login (Obtener Token)

```typescript
async function login(username: string, password: string): Promise<TokenData> {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await fetch(`${API_BASE}/usuarios/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Login failed')
  }

  return response.json()
}
```

**Uso:**
```typescript
const { access_token } = await login('adminGPP', 'admingpp325948')
localStorage.setItem('token', access_token)
```

---

### 2. Logout

```typescript
async function logout(): Promise<void> {
  const token = localStorage.getItem('token')

  if (token) {
    try {
      await fetch(`${API_BASE}/usuarios/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  localStorage.removeItem('token')
  window.location.href = '/login'
}
```

---

### 3. Obtener Usuario Actual (Me)

```typescript
async function getCurrentUser(token: string): Promise<Usuario> {
  const response = await fetch(`${API_BASE}/usuarios/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('Token expired')
  }

  if (!response.ok) {
    throw new Error('Failed to fetch user')
  }

  return response.json()
}
```

**Retorna:**
```json
{
  "id": 1,
  "username": "adminGPP",
  "email": "admin@gpp.com",
  "telefono": null,
  "rol": "administrador",
  "unidad_administrativa_id": null,
  "activo": true
}
```

---

## Endpoints de Usuarios (Requiere Auth)

### Listar Usuarios

```typescript
async function getUsuarios(token: string): Promise<Usuario[]> {
  const response = await fetch(`${API_BASE}/usuarios/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) throw new Error('Failed to fetch usuarios')
  return response.json()
}
```

**Nota:** Ejecutores solo ven usuarios de su unidad administrativa.

---

### Obtener Usuario por ID

```typescript
async function getUsuarioById(token: string, id: number): Promise<Usuario> {
  const response = await fetch(`${API_BASE}/usuarios/${id}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) throw new Error('Failed to fetch usuario')
  return response.json()
}
```

---

### Actualizar Usuario

```typescript
async function updateUsuario(
  token: string,
  id: number,
  data: Partial<Usuario>
): Promise<Usuario> {
  const response = await fetch(`${API_BASE}/usuarios/${id}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) throw new Error('Failed to update usuario')
  return response.json()
}
```

---

## Endpoints de Programas (Requiere Auth)

### Listar Programas

```typescript
interface Programa {
  id: number
  clave: string
  descripcion: string
  ejecutorClave: string
  ejecutorNombre: string
  ejercicio: number
  fechaCreacion: string
  ultimaActualizacion: string | null
}

async function getProgramas(token: string): Promise<Programa[]> {
  const response = await fetch(`${API_BASE}/api/programas`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) throw new Error('Failed to fetch programas')
  return response.json()
}
```

**Comportamiento por Rol:**
- `administrador` / `planeacion` / `programacion-presupuestal` → ve todos los programas
- `ejecutores` → ve solo programas de su unidad administrativa

---

### Obtener Programa por Clave

```typescript
async function getProgramaByClave(token: string, clave: string): Promise<Programa> {
  const response = await fetch(`${API_BASE}/api/programas/${clave}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (response.status === 403) throw new Error('Access denied')
  if (response.status === 404) throw new Error('Programa no encontrado')
  if (!response.ok) throw new Error('Failed to fetch programa')
  return response.json()
}
```

---

### Listar Componentes de un Programa

```typescript
interface Componente {
  id: number
  programaClave: string
  clave: string
  descripcion: string
}

async function getComponentes(token: string, clave: string): Promise<Componente[]> {
  const response = await fetch(`${API_BASE}/api/programas/${clave}/componentes`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (response.status === 403) throw new Error('Access denied')
  if (response.status === 404) throw new Error('Programa no encontrado')
  if (!response.ok) throw new Error('Failed to fetch componentes')
  return response.json()
}
```

---

### Listar Actividades de un Programa

```typescript
interface Actividad {
  id: number
  programaClave: string
  componenteClave: string
  clave: string
  descripcion: string
  metaAnual: number
  costoEstimado: number
  unidadAdministrativaClave: string
}

async function getActividades(token: string, clave: string): Promise<Actividad[]> {
  const response = await fetch(`${API_BASE}/api/programas/${clave}/actividades`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (response.status === 403) throw new Error('Access denied')
  if (response.status === 404) throw new Error('Programa no encontrado')
  if (!response.ok) throw new Error('Failed to fetch actividades')
  return response.json()
}
```

---

## Manejo de Errores

```typescript
interface ApiError {
  detail: string
}

async function fetchWithAuth(url: string, token: string, options: RequestInit = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  })

  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('Session expired')
  }

  if (response.status === 403) {
    throw new Error('Access denied')
  }

  if (response.status === 404) {
    throw new Error('Resource not found')
  }

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}
```

---

## Utilidad: Obtener Token

```typescript
function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token')
}

function setToken(token: string): void {
  localStorage.setItem('token', token)
}

function removeToken(): void {
  localStorage.removeItem('token')
}
```

---

## Ejemplo: Hook de Autenticación para Next.js

```typescript
import { useState, useEffect } from 'react'

export function useAuth() {
  const [user, setUser] = useState<Usuario | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }

    getCurrentUser(token)
      .then(setUser)
      .catch(() => {
        removeToken()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  return { user, loading, isAuthenticated: !!user }
}
```

---

## Roles Disponibles

| Rol | Descripción |
|-----|-------------|
| `administrador` | Acceso total al sistema |
| `programacion-presupuestal` | Revisión de programas, fechas y fondeos |
| `planeacion` | Modifica reglas/actividades globales, ve todos los programas |
| `ejecutores` | Solo ve programas de su unidad, sube evidencias |

---

## Notas Importantes

1. **El token debe incluirse en el header `Authorization: Bearer <token>`** en todas las requests autenticadas.
2. **El token expira** según `ACCESS_TOKEN_EXPIRE_MINUTES` (configurado en backend, default 120 minutos).
3. **Ejecutores** no pueden ver/modificar programas fuera de su unidad administrativa.
4. **Solo administradores** pueden crear nuevos usuarios vía API.
5. **La creación de usuarios administradores** solo se hace manualmente en la base de datos (por seguridad).