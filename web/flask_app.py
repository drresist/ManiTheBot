import threading

from flask import Flask, jsonify


def start_flask_app():
    app = Flask(__name__)

    health_status = True

    @app.route('/toggle')
    def toggle():
        global health_status
        health_status = not health_status
        return jsonify(health_value=health_status)

    @app.route('/health')
    def health():
        if health_status:
            resp = jsonify(health="healthy")
            resp.status_code = 200
        else:
            resp = jsonify(health="unhealthy")
            resp.status_code = 500
        return resp

    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 4000}).start()