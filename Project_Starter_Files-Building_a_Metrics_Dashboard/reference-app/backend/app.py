from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from jaeger_client import Config
from prometheus_flask_exporter import PrometheusMetrics
import logging
import pymongo

app = Flask(__name__)

# enable the collection and exposure of metrics for your Flask application, which can be scraped by Prometheus.
metrics = PrometheusMetrics(app) 
# static information as metric
metrics.info("app_info", "Application info", version="1.0.3")
# for usage of Prometheus Flask exporter library see https://pypi.org/project/prometheus-flask-exporter/.
by_endpoint_counter = metrics.counter('by_endpoint_counter', 'Request count by endpoints', labels={'endpoint': lambda: request.endpoint})
by_path_counter = metrics.counter('by_path_counter', 'Request count by request paths', labels={'path': lambda: request.path})


app.config["MONGO_DBNAME"] = "example-mongodb"
app.config["MONGO_URI"] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"
mongo = PyMongo(app)


# initialize tracing 
def init_jaeger_tracer(service_name = 'backend-service'):

    # Logging: %(message)s is a placeholder that will be replaced by the actual log message when it is emitted.
    logging.getLogger('').handlers = []
    logging.basicConfig(format = '%(message)s', level = logging.DEBUG)
    
    config = Config(config = {'logging':True}, service_name = service_name, validate = True)
    return config.initialize_tracer()

tracer = init_jaeger_tracer('backend-service')

@app.route('/')
@by_endpoint_counter
@by_path_counter
def homepage():
    app.logger.info('Accessing the backend homepage')
    with tracer.start_span('homepage-span') as span:
        span.set_tag('http.method', request.method)
        return "Hello World"

@app.route('/api')
@by_endpoint_counter
@by_path_counter
def my_api():
    app.logger.info('Accessing backend endpoint /api')
    with tracer.start_span('my_api_span') as span:
        span.set_tag('http.method', request.method)
        answer = "something"
        return jsonify(reponse=answer)

@app.route('/star', methods=['POST'])
@by_endpoint_counter
@by_path_counter
def add_star():
    app.logger.info('Accessing backend endpoint /star')
    with tracer.start_span('star_span') as span:
        span.set_tag('http.method', request.method)    
        try:
            star = mongo.db.stars
            name = request.json['name']
            distance = request.json['distance']
            star_id = star.insert({'name': name, 'distance': distance})
            new_star = star.find_one({'_id': star_id })
            output = {'name' : new_star['name'], 'distance' : new_star['distance']}
            return jsonify({'result' : output})
        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    app.run(threaded=True)
