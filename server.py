from flask import Flask , render_template , request , session , redirect , url_for
from flask_socketio import join_room , leave_room , send , SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "vaasiv"
socketio = SocketIO(app)

activeRooms = {}

def generateUniqueRoom(n):
    while True:
        code = ""
        for _ in range(n):
            code+= random.choice(ascii_uppercase)

        if code not in activeRooms:
            return code
        
@app.route("/",methods = ["POST" , "GET"])
def home():


    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")
# When a form is submitted, the browser sends the input data as key-value pairs:
# Here, name acts as the identifier (key) for the value entered in that input. 


        if not name:
            return render_template("home.html",error = "Please Enter Your Name",code = code , name = name)
        
        if join and not code: #If join is not pressed join is assigned to none 
            return render_template("home.html",error = "Please enter the room code",code = code , name = name)
        
        room = code
        if create is not None:
            room = generateUniqueRoom(4)
            activeRooms[room] = {"members" : 0 , "messages" : []}

        elif code not in activeRooms:
            return render_template("home.html",error = "Entered room does not exists",code = code , name = name)
        
        #{{}} --> Jinja2 syntax for rendering
        session["room"] = room
        session["name"] = name

        return redirect(url_for("chat"))#Only the name for the route
    
    return render_template("home.html")


@app.route("/chat")
def chat():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in activeRooms:
        return redirect(url_for("home"))
    
    return render_template("chat.html")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    if room not in activeRooms:
        leave_room(room) #Default function form socketio
        return
    
    join_room(room)
    #send({"name" : name , "message": "has entered the room"})
    send(f"{name} has entered the room",room = room)
    #send is an default function which has two parameters send(message,room) room is optional
    #message can be of two types ---> string or dict

    activeRooms[room]["members"] += 1
    print(f"{name} has entered the {room}")

@socketio.on("diconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in activeRooms:
        activeRooms[room]["members"] -= 1
        if activeRooms[room]["members"] <= 0:
            del activeRooms[room]

    send(f"{name} has left the room",room = room)

if __name__ == "__main__":
    socketio.run(app , debug = True)