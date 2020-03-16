from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanjayjameskundanbryan'
socketio = SocketIO(app)

# For the home page (denoted by the '/'):
@app.route('/')
def sessions():
    return render_template('session.html')

def messageReceived(methods=['GET', 'POST']):
    print('Transaction received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('Event received --- ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

if __name__ == '__main__':
    socketio.run(app, host = '0.0.0.0', debug = True) #running at http://127.0.0.1:5000
    # socketio.run(app, host = '0.0.0.0', port = 8080)
