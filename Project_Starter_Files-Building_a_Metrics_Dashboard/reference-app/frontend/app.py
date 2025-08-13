from flask import Flask, render_template, request
from prometheus_flask_exporter import PrometheusMetrics
import logging

app = Flask(__name__)

# enable the collection and exposure of metrics for your Flask application, which can be scraped by Prometheus.
metrics = PrometheusMetrics(app) 
# static information as metric
metrics.info("app_info", "Application info", version="1.0.3")
# for usage of the Prometheus Flask exporter library see https://pypi.org/project/prometheus-flask-exporter/.
by_endpoint_counter = metrics.counter('by_endpoint_counter', 'Request count by endpoints', labels={'endpoint': lambda: request.endpoint})
by_path_counter = metrics.counter('by_path_counter', 'Request count by request paths', labels={'path': lambda: request.path})

logging.getLogger('').handlers = []
logging.basicConfig(format = '%(message)s', level = logging.INFO)

@app.route('/')
@by_endpoint_counter
@by_path_counter
def homepage():
    app.logger.info('Accessing the frontend homepage')
    try:
        return render_template("main.html")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    app.run(threaded=True)
