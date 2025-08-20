from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World! My application is running via Devtron CD!"

if __name__ == '__main__':
    # Listen on all network interfaces, so it's accessible within the cluster
    app.run(host='0.0.0.0', port=5000)
