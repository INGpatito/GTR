import paramiko
import time

def deploy():
    print("🚀 Conectando a Orange Pi (192.168.100.61)...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect("192.168.100.61", username="orangepi", password="orangepi", timeout=10)
        print("✅ Conexión exitosa. Ejecutando comandos...")
        
        commands = [
            "echo orangepi | sudo -S timedatectl set-timezone America/Mexico_City",
            "echo orangepi | sudo -S apt-get install -y chrony",
            "echo orangepi | sudo -S systemctl enable --now chronyd",
            "echo orangepi | sudo -S chronyc makestep",
            "cd ~/GTR && git fetch origin && git reset --hard origin/main",
            "cd ~/GTR/backend && npm install && pm2 restart all"
        ]
        
        for cmd in commands:
            print(f"➜ Ejecutando: {cmd.replace('echo orangepi | sudo -S ', 'sudo ')}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # Imprimir salida
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print(f"  [OUT] {out}")
            if err: print(f"  [ERR] {err}")
            time.sleep(1)
            
        print("🎉 ¡Despliegue y configuración de reloj completados con éxito!")
        
    except Exception as e:
        print(f"❌ Error conectando a SSH: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
