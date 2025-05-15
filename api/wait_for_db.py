
import sys
import time
import subprocess
import os

def wait_for_db(host, port=5432):
    while True:
        try:
            # Use pg_isready to check the database status
            result = subprocess.run(
                ["pg_isready", "-h", host, "-p", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode == 0:
                print("Database is up - executing command", file=sys.stderr)
                break
            else:
                print("Database is unavailable - sleeping", file=sys.stderr)
        except Exception as e:
            print("Error checking database:", e, file=sys.stderr)
        time.sleep(2)

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} host command [args...]", file=sys.stderr)
        sys.exit(1)
    host = sys.argv[1]
    cmd = sys.argv[2:]
    wait_for_db(host)
    os.execvp(cmd[0], cmd)

if __name__ == "__main__":
    main()