from flask import Flask, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from bson import json_util
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/mydatabase'  # Reemplaza con la URL de tu base de datos MongoDB
app.secret_key = 'mysecretkey'  # Clave secreta para la sesión
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


CORS(app)  # Opcional: permite solicitudes CORS


# Middleware para verificar la autenticación
@app.before_request
def require_login():
    if not session.get('user_id') and request.endpoint != 'login' and request.endpoint != 'register':
        return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = {
        'username': data['username'],
        'password': hashed_password
    }
    result = mongo.db.users.insert_one(user)
    # return jsonify({'message': 'User registered successfully!', 'user_id': str(result.inserted_id)})
    return redirect(url_for('home', user=user))


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = mongo.db.users.find_one({'username': data['username']})
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        session['user_id'] = str(user['_id'])
        # return jsonify({'message': 'Login successful!', 'user_id': session['user_id']})
        return redirect(url_for('home', user=user))
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully!'})

@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users.find()
    return json_util.dumps(users)

@app.route('/')
def home():

    return jsonify({'message': 'Welcome to the Home page!'})

#  create notes collection for a user
@app.route('/users/<user_id>/create_notes', methods=['POST'])
def createNotes(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'})
    else:
        notes_collection = mongo.db.notes

        # Insert the note document into the collection, associating it with the user ID
        inserted_id = notes_collection.insert_one({
            'user_id': user_id,
            # '_id': _id,
            'title': request.json['title'],
            'description': request.json['description'],
            'created_at': datetime.now(),
            'updated_at': None,
            'finished_at': None
        }).inserted_id

    # return (console.log({'msg': 'Note created succesfully','_id': str(inserted_id)}))
    return jsonify({'msg': 'Note created succesfully','_id': str(inserted_id)})



# get all notes for a user
@app.route('/users/<user_id>/notes', methods=['GET'])
def getNotes(user_id):
    notes_collection = mongo.db.notes

    # Find all notes associated with the user ID
    notes = notes_collection.find({'user_id': user_id})

    # Convert the MongoDB Cursor to a list of dictionaries
    notes_list = []
    for note in notes:
        note['_id'] = str(note['_id'])
        notes_list.append(note)

    return jsonify({'notes': notes_list})


# DELETE AN SINGLE NOTE BASED ON THE NOTE'S ID
@app.route('/users/<user_id>/delete_notes/<_id>', methods=['DELETE'])
def deleteSingleNote(user_id, _id):
    notes_collection = mongo.db.notes

    # Find the note associated with the user ID and note ID
    noteToDelete = notes_collection.find_one({'user_id': user_id, '_id': ObjectId(_id)})
    if noteToDelete:
        # delete it
        notes_collection.delete_one(noteToDelete)

        return jsonify({'msg': 'Note have been deleted successfully'})
    else:
        return jsonify({'msg': 'No note was found!'})

# UPDATE SINGLE NOTE BASED ON THE NOTE'S ID
@app.route('/users/<user_id>/notes/<_id>', methods=['PUT'])
def updateNote(user_id, _id):
    notes_collection = mongo.db.notes

    # Verificar si la nota existe
    existing_note = notes_collection.find_one({'user_id': user_id, '_id': ObjectId(_id)})
    if not existing_note:
        return jsonify({'msg': 'La nota no existe'})

    # Obtener los nuevos datos de la nota desde la solicitud
    updated_data = request.json

    # Actualizar los campos de la nota existente
    notes_collection.update_one(
        {'_id': ObjectId(_id)},
        {'$set': updated_data}
    )

    return jsonify({'msg': 'Nota actualizada exitosamente'})


if __name__ == '__main__':
    app.run(debug=True)





