from app.__init__ import create_app
from flask import Flask, jsonify
app = create_app()

@app.route('/', methods=['GET'])
def check_status():
    return jsonify({"status": "ok", "message": "API is running"}), 200
if __name__ == '__main__':
    app.run(debug=True) 