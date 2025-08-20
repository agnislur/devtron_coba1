from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "<strong>Hello World! Versi 3.0 - Diperbarui secara otomatis oleh Devtron!</strong>" 

if __name__ == '__main__':
    # Listen on all network interfaces, so it's accessible within the cluster
    app.run(host='0.0.0.0', port=5000)
