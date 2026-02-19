import os
import requests
import json
from flask import Flask, request
from dotenv import load_dotenv

# ==========================
# CONFIGURACIÓN
# ==========================
load_dotenv()
app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
VIEW_ID = os.getenv("VIEW_ID")
ORG_ID = os.getenv("ORG_ID")


# ==========================
# 1️⃣ Obtener Access Token
# ==========================
def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"

    data = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()["access_token"]


# ==========================
# 2️⃣ Obtener datos por ticket_id
# ==========================
def obtener_ticket(ticket_id):

    access_token = get_access_token()

    url = f"https://analyticsapi.zoho.com/restapi/v2/workspaces/{WORKSPACE_ID}/views/{VIEW_ID}/data"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "ZANALYTICS-ORGID": ORG_ID
    }

    criteria = f"\"tickets_consulta\".\"ticket_id\" = '{ticket_id}'"

    config = {
        "responseFormat": "json",
        "criteria": criteria
    }

    params = {
        "CONFIG": json.dumps(config)
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    result = response.json()

    if "data" not in result or len(result["data"]) == 0:
        return None

    return result["data"][0]


# ==========================
# 3️⃣ Endpoint consulta ticket
# ==========================
@app.route("/ticket", methods=["POST"])
def consultar_ticket():

    data = request.get_json(silent=True)

    if data:
        ticket_id = data.get("ticket_id")
    else:
        ticket_id = request.form.get("ticket_id")

    if not ticket_id:
        return {"success": False, "message": "Falta ticket_id"}, 400

    try:
        ticket = obtener_ticket(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket no encontrado"}

        estado = ticket.get("Estado_Final", "Sin estado")
        fecha_creacion = ticket.get("Fecha_creacion", "Sin fecha")
        fecha_cierre = ticket.get("Fecha_cierre") or "Sin cerrar"
        comment = ticket.get("Comment") or "Sin comentar"

        return {
            "success": True,
            "ticket_id": ticket_id,
            "Estado_Final": estado,
            "Fecha_creacion": fecha_creacion,
            "Fecha_cierre": fecha_cierre,
            "Comment": comment
        }

    except Exception as e:
        return {"success": False, "message": str(e)}, 500


# ==========================
# 4️⃣ Ping
# ==========================
@app.route("/ping", methods=["GET"])
def ping():
    return "OK", 200


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
