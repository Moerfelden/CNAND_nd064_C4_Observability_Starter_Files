from flask import Flask, render_template, request
from flask_opentracing import FlaskTracing
from jaeger_client import Config
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

# initialize tracing 
def init_jaeger_tracer(service_name = 'frontend-service'):

    # Logging: %(message)s is a placeholder that will be replaced by the actual log message when it is emitted.
    logging.getLogger('').handlers = []
    logging.basicConfig(format = '%(message)s', level = logging.DEBUG)
    
    config = Config(
        config={
            'sampler': {'type': 'const', 'param': 1},
            'logging': True,
            'reporter_batch_size': 1}, 
        service_name=service_name,
        validate = True)
    return config.initialize_tracer()

tracer = init_jaeger_tracer('frontend-service')
tracing = FlaskTracing(tracer, True, app)

@app.route('/')
@by_endpoint_counter
@by_path_counter
def homepage():
    app.logger.info('Accessing the frontend homepage')
    with tracer.start_span('frontend_homepage_span') as span:
        span.set_tag('tag', 'frontend homepage')
        try:
            result = Flask.ensure_sync(render_template("main.html"))()  # Wrap the async function
            return result
        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    app.run(threaded=True)
