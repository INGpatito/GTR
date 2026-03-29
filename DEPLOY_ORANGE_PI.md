# Despliegue automatico a Orange Pi (self-hosted runner)

Este repositorio usa GitHub Actions con un runner instalado dentro de tu Orange Pi. Asi, cada push a `main` despliega sin depender de exponer tu red local.

Archivo del workflow:
- `.github/workflows/deploy-orange-pi.yml`

## 1) Instala el runner en Orange Pi

En GitHub: Settings > Actions > Runners > New self-hosted runner > Linux > ARM64.

Copia y ejecuta en la Orange Pi los comandos que te da GitHub (descarga, config y run).

Recomendacion: instalar como servicio para que inicie solo.

```bash
cd actions-runner
sudo ./svc.sh install orangepi
sudo ./svc.sh start
```

## 2) Secretos/variables que necesitas

En tu repo: Settings > Secrets and variables > Actions.

Obligatorio:
- `ORANGE_PI_APP_DIR`: ruta destino local en la Orange Pi (ejemplo `/home/orangepi/GTR`)

Opcional:
- `ORANGE_PI_SERVICE_NAME`: servicio systemd a reiniciar al final (ejemplo `nginx` o `gtr.service`)

## 3) Primer despliegue

Haz push a `main`:

```bash
git add .
git commit -m "Configurar deploy con self-hosted runner"
git push origin main
```

## 4) Verifica ejecucion

En GitHub: Actions > workflow "Deploy to Orange Pi".

En la Orange Pi:

```bash
cd /home/orangepi/GTR
ls -la
```

## Opcional: script de post-despliegue

Si agregas un archivo `deploy.sh` en la raiz del repo, el workflow lo ejecuta automaticamente dentro de `ORANGE_PI_APP_DIR`.

Ejemplo:

```bash
#!/usr/bin/env bash
set -e

# Aqui pones pasos de build/restart
# npm ci
# npm run build
```
