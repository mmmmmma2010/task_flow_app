import os
import sys
import socket
import time
from urllib.parse import urlparse

def wait_for_service(service_name, url_env, default_host, default_port):
    url = os.environ.get(url_env)
    if url:
        if 'sqlite' in url:
            print(f"{service_name} uses SQLite, skipping wait.")
            return
        result = urlparse(url)
        host = result.hostname
        port = result.port
        if not host or not port:
             print(f"Could not parse host/port from {url_env}, skipping wait.")
             return
    else:
        host = os.environ.get(default_host, 'db' if service_name == 'PostgreSQL' else 'redis')
        port = int(os.environ.get(default_port, 5432 if service_name == 'PostgreSQL' else 6379))
    
    print(f"Waiting for {service_name} at {host}:{port}...")
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"{service_name} is ready!")
                return
        except (OSError, ValueError) as e:
            time.sleep(1)
            if time.time() - start_time > 60:
                 print(f"Timeout waiting for {service_name}: {e}")
                 # Don't exit, just continue and let the app fail if it must, 
                 # largely because sometimes these checks are flaky in some environments
                 return

if __name__ == "__main__":
    wait_for_service("PostgreSQL", "DATABASE_URL", "DB_HOST", "DB_PORT")
    wait_for_service("Redis", "REDIS_URL", "REDIS_HOST", "REDIS_PORT")
