from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "vaasiv"
socketio = SocketIO(app)

activeRooms = {}

def generateUniqueRoom(n):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(n))
        if code not in activeRooms:
            return code

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")  # Will be None if not checked
        create = request.form.get("create")  # Will be "on" if checked

        if not name:
            return render_template("home.html", error="Please Enter Your Name", code=code, name=name)

        if join and not code:  
            return render_template("home.html", error="Please enter the room code", code=code, name=name)

        room = code

        # ✅ Check if "Create Room" was clicked (fix)
        if create is not None:
            room = generateUniqueRoom(4)
            activeRooms[room] = {"members": 0, "messages": []}
        
        elif code not in activeRooms:
            return render_template("home.html", error="Entered room does not exist", code=code, name=name)

        # ✅ Save room and user in session
        session["room"] = room
        session["name"] = name

        return redirect(url_for("chat"))  # Correctly redirects

    return render_template("home.html")

@app.route("/chat")
def chat():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in activeRooms:
        return redirect(url_for("home"))
    
    return render_template("chat.html", room=room, name=session.get("name"))

#  Handle when a user connects
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    if room not in activeRooms:
        leave_room(room)  
        return
    
    join_room(room)
    
    # Notify others that a user has joined
    send({
        "name": name,
        "message": "has entered the room"
    }, room=room)

    print(f"{name} has entered room {room}")  # Debugging log

# Handle when a user disconnects
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    
    # Notify others that the user has left
    send({
        "name": name,
        "message": "has left the room"
    }, room=room)

    leave_room(room)
    
    # Remove user session info
    session.pop("room", None)
    session.pop("name", None)

    print(f"{name} has left room {room}")  # Debugging log

#  Handle messages between users
@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    
    # Send the message to everyone in the room
    send({"name": name, "message": data["message"]}, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
