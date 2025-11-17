import requests
import json

# === CONFIG ===
base_url = "http://localhost:3000"
auth = "Basic YWRtaW46YWRtaW4="  # admin:admin (Base64)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": auth
}

# === 1️⃣ Create Service Account ===
service_account_data = {
    "name": "init",
    "role": "Admin",
    "isDisabled": False
}

create_sa = requests.post(
    f"{base_url}/api/serviceaccounts",
    headers=headers,
    json=service_account_data
)

print("Create service account:", create_sa.status_code, create_sa.text)

# Parse service account ID
if create_sa.ok:
    sa_id = create_sa.json().get("id")
else:
    raise SystemExit("Failed to create service account")

# === 2️⃣ Create Token for Service Account ===
token_data = {
    "name": "grafana",
    "secondsToLive": 604800  # 7 days
}

create_token = requests.post(
    f"{base_url}/api/serviceaccounts/{sa_id}/tokens",
    headers=headers,
    json=token_data
)

print("Create token:", create_token.status_code, create_token.text)

if create_token.ok:
    token_info = create_token.json()

    token = token_info.get("key")
else:
    print('Grafana token not created')



# === CONFIG ===
url = f"{base_url}/api/datasources"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# === DATASOURCE CONFIG ===
payload = {
    "name": "clickhouse_local",
    "type": "grafana-clickhouse-datasource",  # plugin type
    "url": "http://localhost:8123",          # or localhost if running locally
    "access": "proxy",
    "basicAuth": False,
    "database": "default",
    "jsonData": {
        "username": "dwuser",       
        "server": "host.docker.internal",
        "port": 8123,
        "protocol": "http",
    },
    "secureJsonData": {
        "password": "dwpass"   # send password here
    }
}

# === SEND POST REQUEST ===
response = requests.post(
    url, 
    headers=headers, 
    json=payload)



# === CONFIG ===
url = f"{base_url}/apis/dashboard.grafana.app/v1beta1/namespaces/default/dashboards" 

# === LOAD DASHBOARD JSON ===
with open("dashboard.json", "r", encoding="utf-8") as f:
    dashboard_spec = json.load(f)

# === BUILD REQUEST BODY ===
payload = {
    "metadata": {"name": "my-dashboard"},
    "spec": dashboard_spec
}

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# === SEND POST REQUEST ===
response = requests.post(
    url, 
    headers=headers, 
    json=payload)

# print("Status:", response.status_code)
# print("Response:", response.text)
