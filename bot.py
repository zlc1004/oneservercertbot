import os
import json
import docker
import shutil

containers = docker.from_env().containers

def certbot(domains):
    containers.run(
        image="certbot/certbot",
        volumes={"./cert": {"bind": "/opt/certbot/config/archive", "mode": "rw"}},
        ports={"80": 80},
        command=[
            "certonly",
            "-n",
            "--agree-tos",
            "--preferred-challenges",
            "http",
            "--domain",
            ",".join(domains),
            "--config-dir",
            "./config",
            "--standalone",
        ],
    )

def chmod(domains):
    domain = domains[0]
    containers.run(
        image="alpine",
        volumes={"./cert": {"bind": "/opt/certbot/config/archive", "mode": "rw"}},
        command=["chmod", "777", f"/opt/certbot/config/archive/{domain}/*"]
    )

"""
[
    {
        "domain": "dynamic.server.kobosh.com",
        "forwarding": "host.docker.internal:59900",
        "type": "https",
        "ca-bundle": "dynamic.server.kobosh.com/fullchain.pem",
        "private-key": "dynamic.server.kobosh.com/privkey.pem",
        "websocket": true
    }
]
"""

containers.get("oneserver").stop()

with open("/oneserver/settings.json", 'r') as f:
    settings = json.load(f)

new_setting=[]

domains = []

for setting in settings:
    if setting["type"] == "http":
        new_setting.append(setting)
        continue
    setting["ca-bundle"] = f"fullchain.pem",
    setting["private-key"] = f"privkey.pem",
    domains.append(setting["domain"])

with open("/oneserver/settings.json", 'w') as f:
    json.dump(settings, f)

shutil.copy2(f"./cert/{domains[0]}/fullchain.pem", "/oneserver/cert/fullchain.pem")
shutil.copy2(f"./cert/{domains[0]}/privkey.pem", "/oneserver/cert/privkey.pem")

os.system("cd /oneserver && docker compose up -d --build")