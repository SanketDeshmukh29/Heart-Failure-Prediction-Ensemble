from flask import Flask, render_template
from api_routes import bp1
from chatbot import chatbot_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.register_blueprint(bp1)
app.register_blueprint(chatbot_bp)

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/predict')
def predict():
    return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    return render_template('ChatBot.html')

# Production deployment uses gunicorn, so this block is only for local development
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

