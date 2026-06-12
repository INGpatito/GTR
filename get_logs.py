import paramiko

def get_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("192.168.100.61", username="orangepi", password="orangepi", timeout=10)
        stdin, stdout, stderr = ssh.exec_command("pm2 logs --lines 50 --nostream")
        print(stdout.read().decode())
    except Exception as e:
        print("Error:", e)
    finally:
        ssh.close()

if __name__ == "__main__":
    get_logs()
