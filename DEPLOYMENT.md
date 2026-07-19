# Despliegue a Azure — TurfBook Login

Guía paso a paso para desplegar este proyecto a Azure. Es la primera vez que se
hace este despliegue, así que el documento está pensado como un runbook
detallado, no solo como referencia rápida.

**Alcance de esta ronda**: llegar hasta el ambiente **stage**. Producción
(`prod`) queda para una siguiente iteración — ver la sección
["Fuera de alcance por ahora"](#fuera-de-alcance-por-ahora) al final.

**Repos involucrados**:
- `app-login-Azure` — API FastAPI (login, logout, recuperación de contraseña).
- `fuction-sms-notifier` — Azure Function (trigger de cola) que envía el SMS
  con el código de verificación.

---

## 0. Estrategia de ramas (git flow)

Esto va primero porque los pipelines de CI/CD van a reaccionar a estas ramas
— hay que tenerlas creadas antes de armar los pipelines.

Mapeo de ramas a ambientes (patrón estándar de git flow / "Release Flow"):

| Rama          | Ambiente al que despliega | Cuándo se usa                                   |
|---------------|----------------------------|--------------------------------------------------|
| `develop`     | `dev`                       | Integración continua del día a día. Cada push dispara deploy automático a dev. |
| `release/*`   | `stage`                     | Se corta desde `develop` cuando una tanda de features está lista para validar. Deploy a stage para pruebas de aceptación. |
| `main`        | `prod` (fuera de alcance hoy) | Solo recibe merges desde `release/*` ya validado en stage. |
| `feature/*`   | ninguno (solo CI: tests/lint) | Rama de trabajo diario, sale de `develop` y vuelve a `develop` vía PR. |
| `hotfix/*`    | según urgencia               | Sale de `main`, se aplica a `main` y se remergea a `develop`. No aplica hoy. |

**Pasos concretos en cada repo** (`app-login-Azure` y `fuction-sms-notifier`):

1. Crear la rama `develop` desde `main`:
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```
2. En GitHub, configurar `develop` como rama por defecto para nuevos PRs
   (opcional pero recomendado), y agregar **branch protection** a `main` y
   `develop`: requerir PR + al menos 1 review + que pase el check de CI antes
   de mergear.
3. De ahora en adelante, el trabajo diario sale de `develop` en ramas
   `feature/<nombre>`, se mergea a `develop` vía PR.
4. Cuando decidamos llevar algo a stage: `git checkout -b release/x.y.z develop`
   y push — eso es lo que dispara el deploy a stage.

---

## 1. Convención de nombres y ambientes

Vamos a tener recursos de Azure **duplicados por ambiente** (dev y stage cada
uno con su propio Resource Group, su propia base de datos, etc.) — son
ambientes de verdad, aislados entre sí, no solo un slot compartido.

Convención de nombres sugerida (ajustar el prefijo si ya tenés uno definido):

| Recurso                          | Dev                                  | Stage                                   |
|-----------------------------------|---------------------------------------|-------------------------------------------|
| Resource Group                    | `rg-azure-app-login-dev`               | `rg-azure-app-login-stage`                  |
| App Service Plan                  | `plan-azure-app-login-dev`             | `plan-azure-app-login-stage`                |
| Web App (API)                     | `app-azure-app-login-dev`              | `app-azure-app-login-stage`                 |
| Function App                      | `func-azure-app-login-sms-dev`         | `func-azure-app-login-sms-stage`            |
| Storage Account (Functions/cola)  | `azureapploginsmsdev` *(sin guiones, ≤24 car)*| `azureapploginsmsstage`              |
| PostgreSQL Flexible Server        | `psql-azure-app-login-dev`             | `psql-azure-app-login-stage`                |
| Key Vault                         | `kv-azure-app-login-dev`               | `kv-azure-app-login-stage`                  |

**APIM es la excepción**: por costo, vamos a usar **una sola instancia de
APIM** compartida entre dev y stage (APIM es el recurso más caro del stack).
Dentro de esa única instancia, se crean **dos APIs separadas** (o dos
backends), una apuntando al Web App de dev y otra al de stage. Cuando
lleguemos a prod, ahí sí evaluamos si conviene una instancia de APIM
dedicada.

---

## 2. Recursos base (por ambiente: repetir para dev y luego para stage)

Orden de creación — cada uno puede depender del anterior:

1. **Resource Group**
2. **Azure Key Vault** — contenedor de secretos. Crear antes que el resto
   porque las identidades administradas se van a autorizar contra él.
3. **Storage Account** — para la Function App (`AzureWebJobsStorage`) y la
   cola real `sms-verification-codes` (reemplaza a Azurite local).
4. **Azure Database for PostgreSQL — Flexible Server**. Para dev/stage,
   acceso público + regla de firewall (más simple). Guardar usuario/password
   generados.
5. **App Service Plan (Linux) + Web App (Python)** — para `app-login-Azure`.
6. **Function App** (plan Consumption) — para `fuction-sms-notifier`, usando
   el Storage Account del paso 3 (no el mismo storage que usaría otra función,
   buena práctica de Azure Functions: un storage account por function app).

---

## 3. Identidad y secretos (por ambiente)

1. Activar **Managed Identity (system-assigned)** en el Web App y en la
   Function App.
2. En Key Vault, asignar el rol RBAC **"Key Vault Secrets User"** a cada una
   de esas identidades (mínimo privilegio — no "Administrator").
3. Cargar en Key Vault los secretos que hoy están en `.env`:
   - `DATABASE_URL` (con el usuario/password de PostgreSQL de ese ambiente)
   - `JWT_SECRET_KEY` (generar uno nuevo por ambiente, no reusar el de local)
   - `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `QUEUE_CONNECTION_STRING` (connection string real del Storage Account)
   - `SMS_QUEUE_NAME`
4. En el Web App y la Function App, configurar cada app setting como
   referencia a Key Vault:
   ```
   @Microsoft.KeyVault(SecretUri=https://kv-azure-app-login-dev.vault.azure.net/secrets/DATABASE-URL)
   ```
   El código no cambia — `pydantic-settings` sigue leyendo variables de
   entorno normalmente, Azure resuelve la referencia por detrás.

---

## 4. Deploy del código — `app-login-Azure`

1. **Startup command** del Web App (FastAPI no se auto-detecta salvo Python
   3.14+): en Configuración → Configuración general → Comando de inicio:
   ```
   gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
   ```
   (agregar `gunicorn` a `requirements/base.txt` si no está).
2. Deploy inicial manual (para validar que todo funciona antes de automatizar
   con el pipeline): vía `az webapp deploy` o Deployment Center apuntando al
   repo/rama `develop`.
3. **Migraciones de Alembic**: entrar por SSH al contenedor del Web App
   (Azure lo expone desde el portal, pestaña "SSH") y correr:
   ```bash
   alembic upgrade head
   ```
   contra la base de datos real de ese ambiente. A futuro esto se puede mover
   a un paso del pipeline.
4. Repetir 2-3 para stage una vez que dev esté validado.

---

## 5. Deploy del código — `fuction-sms-notifier`

1. Verificar que `host.json` mantiene `"messageEncoding": "none"` — es el fix
   que encontramos probando en local, y sigue siendo necesario contra Azure
   real (no es una particularidad de Azurite).
2. Deploy inicial manual: `func azure functionapp publish <nombre-function-app>`.
3. Configurar `AzureWebJobsStorage` y `SMS_QUEUE_NAME` como app settings del
   Function App (vía Key Vault references, igual que en el paso 3).
4. Probar el trigger end-to-end: pedir un código desde la API de login →
   confirmar en Application Insights / logs del Function App que se ejecutó
   `sms_verification_sender` y quedó en estado "Succeeded".

---

## 6. APIM (una sola instancia, compartida dev/stage)

1. Crear la instancia de APIM (tier Developer o Basic v2 para no vaciar el
   bolsillo — Premium es innecesario en esta etapa).
2. Importar el Web App de **dev** como API — FastAPI ya expone
   `/openapi.json`, así que APIM lo importa con alta fidelidad en vez de
   generar wildcards genéricos. Repetir para el Web App de **stage** como una
   API separada dentro de la misma instancia.
3. **Versionado**: por path (`/v1/login`, `/v1/logout`, etc.), aunque hoy
   solo exista v1 — así agregar v2 el día de mañana no rompe a nadie que ya
   esté integrado.
4. **Rate limiting**: política `rate-limit` (por subscription key) a nivel de
   producto. Al superarse, APIM devuelve 429 automáticamente — no hay que
   programar nada en la API.
5. Restringir el Web App para que solo acepte tráfico entrante desde APIM
   (IP restrictions), para que nadie lo llame salteándose el control.

---

## 7. CI/CD con GitHub Actions

Cambio de plan respecto a la primera versión de este documento: en vez de
Azure DevOps, usamos **GitHub Actions** — el código ya vive en GitHub, así
que no hace falta un portal/organización aparte. El archivo de workflow ya
está creado en cada repo: `.github/workflows/deploy.yml`.

**Autenticación a Azure sin secretos (OIDC)**: en vez de "Service
Connections" (eso es vocabulario de Azure DevOps), acá se usa una
**Federated credential** sobre una **Identidad administrada asignada por el
usuario** (User-Assigned Managed Identity) — mismo principio (workload
identity federation), pero es un recurso más de Azure (igual que el Web App
o la Function App), no algo de Entra ID separado — más simple de encontrar
en el Portal.

1. **Crear dos Identidades administradas** (una por ambiente, no por repo —
   ambos repos comparten el mismo resource group por ambiente): "Crear un
   recurso" → buscar **"User Assigned Managed Identity"** →
   `uami-gh-deploy-dev` en `rg-azure-app-login-dev`, y
   `uami-gh-deploy-stage` en `rg-azure-app-login-stage`.
2. En cada identidad → **Settings** → **Federated credentials** → **Add
   credential** → escenario **"GitHub Actions deploying Azure resources"**.
   Agregar **dos credenciales** (una por repo que va a usarla):
   - Organización/repo: `app-login-Azure`, Entity type: **Environment**,
     GitHub environment name: `dev` (o `stage` en la identidad de stage).
   - Repo: `fuction-sms-notifier`, mismo esquema.
3. En el **Resource Group** de cada ambiente (`rg-azure-app-login-dev` /
   `-stage`), asignar el rol **Contributor** a la identidad administrada
   correspondiente (Access control (IAM) → Add role assignment → Managed
   identity).
4. Anotar de cada identidad: **Client ID**, **Subscription ID**, y el
   **Directory (tenant) ID** (estos dos últimos son los mismos para dev y
   stage, es la misma suscripción/tenant).
5. En **cada repo de GitHub** → Settings → Environments → crear `dev` y
   `stage`:
   - `dev`: sin protection rules — deploy automático en push a `develop`.
   - `stage`: agregar **Required reviewers** (vos mismo) — es el equivalente
     a la aprobación manual antes de desplegar.
   - En cada Environment, cargar las **Environment variables** (no
     secrets — un client ID no es información sensible cuando se usa OIDC):
     `AZURE_CLIENT_ID` (el de la identidad administrada de ese ambiente),
     `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
6. Los workflows (`app-login-Azure/.github/workflows/deploy.yml` y
   `fuction-sms-notifier/.github/workflows/deploy.yml`) ya están armados con
   el mismo esquema que se pensó para Azure DevOps: build+test → deploy a
   `dev` (push a `develop`) → deploy a `stage` (push a `release/*`).

---

## 8. Checklist de validación en stage

Antes de dar por buena la ronda de hoy, confirmar en el ambiente stage:

- [ ] `POST /users` registra un usuario contra el PostgreSQL de stage.
- [ ] `POST /login` devuelve token.
- [ ] `POST /logout` invalida el token (204).
- [ ] `POST /password/reset-request` encola el mensaje y la Function App lo
      procesa (revisar logs de la function).
- [ ] `POST /password/reset` actualiza la contraseña con el código real.
- [ ] Las llamadas pasan por la URL de APIM, no directo al Web App.
- [ ] Los secretos se leen vía Key Vault reference (no hay ningún valor
      plano en los app settings del Web App / Function App).
- [ ] El pipeline de `develop` → dev corrió solo; el de `release/*` → stage
      pidió aprobación antes de ejecutar.

---

## Fuera de alcance por ahora

Explícitamente no lo hacemos en esta ronda (queda para cuando avancemos a
prod):

- Ambiente `prod` y la rama `main`.
- VNet integration + private endpoints para PostgreSQL (hoy: acceso público
  + firewall).
- Autenticación a PostgreSQL vía Managed Identity/Entra ID (hoy: connection
  string con password, guardado en Key Vault).
- Deployment slots del Web App para swap sin downtime (técnica específica
  para el corte a producción).
- Dominio custom + certificado SSL propio.
- Azure Front Door / WAF.
- Alta disponibilidad de PostgreSQL (zona redundante).
- Instancia de APIM dedicada para prod.
