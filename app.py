import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    config_val = os.environ.get('APP_CONFIG_VAL', 'No Config')
    secret_val = os.environ.get('APP_SECRET_VAL', 'No Secret')
    return f"Hello, World!\nConfig: {config_val}\nSecret: {secret_val}\n"

@app.route('/about')
def about():
    return "This is the secure about page! Welcome to the Python GKE App.\n"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
