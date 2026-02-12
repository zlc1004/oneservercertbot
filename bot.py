import os
import json
import docker
import shutil

containers = docker.from_env().containers


def certbot(domains):
    return containers.run(
        image="certbot/certbot",
        volumes={"/app/cert": {"bind": "/opt/certbot/config/archive", "mode": "rw"}},
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
        detach=True,
        remove=True,
    )


def chmod(domains):
    domain = domains[0]
    return containers.run(
        image="alpine",
        volumes={"/app/cert": {"bind": "/opt/certbot/config/archive", "mode": "rw"}},
        command=["chmod", "777", f"/opt/certbot/config/archive/{domain}/*"],
        detach=True,
        remove=True,
    )


def stream(container):
    try:
        if container.status != "running":return
        logs = container.logs(stdout=True, stderr=True, stream=True)
        for log in logs:
            print(log.decode())
    except Exception as e:
        print(e)


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

with open("/oneserver/settings.json", "r") as f:
    settings = json.load(f)

new_setting = []

domains = []

for setting in settings:
    setting = setting.copy()
    if setting["type"] == "http":
        new_setting.append(setting)
        continue
    setting["ca-bundle"] = ("fullchain.pem",)
    setting["private-key"] = ("privkey.pem",)
    domains.append(setting["domain"])
    new_setting.append(setting)

with open("/oneserver/settings.json", "w") as f:
    json.dump(new_setting, f)

stream(certbot(domains=domains))
stream(chmod(domains=domains))

shutil.copy2(f"/app/cert/{domains[0]}/fullchain1.pem", "/oneserver/cert/fullchain.pem")
shutil.copy2(f"/app/cert/{domains[0]}/privkey1.pem", "/oneserver/cert/privkey.pem")

os.system("cd /oneserver && docker compose up -d --build")
