# Despliegue automatico a Orange Pi

Este repositorio ya incluye un workflow que despliega automaticamente cuando haces push a `main`.

Archivo del workflow:
- `.github/workflows/deploy-orange-pi.yml`

## 1) Crea llave SSH (en tu PC)

```bash
ssh-keygen -t ed25519 -C "github-actions-orange-pi"
```

## 2) Autoriza la llave publica en Orange Pi

Copia tu llave publica al archivo `~/.ssh/authorized_keys` del usuario remoto.

## 3) Agrega secretos en GitHub

En tu repo: Settings > Secrets and variables > Actions > New repository secret

Crea estos secretos:
- `ORANGE_PI_HOST`: IP o dominio de la Orange Pi (ejemplo `192.168.100.61`)
- `ORANGE_PI_USER`: usuario SSH (ejemplo `orangepi`)
- `ORANGE_PI_PORT`: puerto SSH (normalmente `22`)
- `ORANGE_PI_SSH_KEY`: contenido completo de la llave privada (id_ed25519)
- `ORANGE_PI_APP_DIR`: ruta destino en Orange Pi (ejemplo `/var/www/GTR`)
- `ORANGE_PI_SERVICE_NAME` (opcional): servicio systemd a reiniciar (ejemplo `nginx` o `gtr.service`)

## 4) Primer despliegue

Haz push a `main`:

```bash
git add .
git commit -m "Agregar deploy automatico a Orange Pi"
git push origin main
```

## 5) Verifica ejecucion

En GitHub: Actions > workflow "Deploy to Orange Pi".

## Opcional: script de post-despliegue

Si agregas un archivo `deploy.sh` en la raiz del repo, el workflow lo ejecutara automaticamente en Orange Pi despues del `git reset --hard`.

Ejemplo:

```bash
#!/usr/bin/env bash
set -e

# Aqui pones pasos de build/restart
# npm ci
# npm run build
# sudo systemctl restart nginx
```
