from io import BytesIO

from flask import Flask, request, jsonify, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'do1olfi1bk2hs3scras4dkdaey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
database = SQLAlchemy(app)


class Users(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(50))
    password = database.Column(database.String(50))


class Tasks(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    task = database.Column(database.String(100), nullable=False)
    user = database.Column(database.String(50), nullable=False)


class Files(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    file_name = database.Column(database.String(100), nullable=False)
    file_size = database.Column(database.String(50), nullable=False)
    file = database.Column(database.BLOB)
    user = database.Column(database.String(50), nullable=False)


def token_required(f):
    @wraps(f)
    def decorator(secret_key=app.config['SECRET_KEY'], *args, **kwargs):
        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            current_user = Users.query.filter_by(name=data['name']).first()
        except:
            return jsonify({'message': 'token is invalid'})

        return f(current_user, *args, **kwargs)

    return decorator


@app.route('/')
def index():
    return 'TodoList'


@app.route('/user', methods=['POST'])
def signup_user():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password, method='sha256')

    new_user = Users(name=username, password=hashed_password)
    database.session.add(new_user)
    database.session.commit()

    return jsonify({'message': 'registered successfully'})


@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']

    user = Users.query.filter_by(name=username).first()
    if not user:
        return make_response('user not found', 401)
    if check_password_hash(user.password, password):
        token = jwt.encode(
            {'name': user.name}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})

    return make_response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})


@app.route('/todo', methods=['GET'])
@token_required
def task_view(current_user):
    tasks = Tasks.query.filter(Tasks.user == current_user.name)
    result = []
    for task in tasks:
        task_data = {'id': task.id, 'task': task.task}
        result.append(task_data)
    return jsonify({'tasks': result})


@app.route('/todo', methods=['POST'])
@token_required
def create_task(current_user):
    task = request.form['task']
    new_task = Tasks(task=task, user=current_user.name)
    database.session.add(new_task)
    database.session.commit()
    return jsonify({'message': 'new task created'})


@app.route('/todo/<int:id>', methods=['PUT'])
@token_required
def update_task(current_user, id):
    element = Tasks.query.filter(Tasks.id == id, Tasks.user == current_user.name).first()
    new_task = request.form['task']
    if not element:
        return make_response('Task not found', 401)
    element.task = new_task
    database.session.commit()
    return jsonify({'message': 'Task updated'})


@app.route('/todo/<int:id>', methods=['DELETE'])
@token_required
def deleting_task(current_user, id):
    element = Tasks.query.filter(Tasks.id == id, Tasks.user == current_user.name).first()
    if not element:
        return make_response('Task not found', 401)
    database.session.delete(element)
    database.session.commit()
    return jsonify({'message': 'Task deleted'})


@app.route('/files', methods=['GET'])
@token_required
def file_browsing(current_user):
    files = Files.query.filter(Files.user == current_user.name)
    result = []
    for file in files:
        file_data = {'id': file.id,
                     'file_name': file.file_name,
                     'file_size': file.file_size}
        result.append(file_data)
    return jsonify({'files': result})


@app.route('/files', methods=['POST'])
@token_required
def fileupload(current_user):
    new_file = request.files['file']
    data = new_file.read()
    file_size = str(len(data))
    file = Files(file_name=new_file.filename,
                 file_size=file_size,
                 file=data,
                 user=current_user.name)
    database.session.add(file)
    database.session.commit()
    return jsonify({'message': 'file uploaded successfully'})


@app.route('/files/<string:file_name>', methods=['GET'])
@token_required
def download_file(current_user, file_name):
    file = Files.query.filter(Files.file_name == file_name,
                              Files.user == current_user.name).first()
    if not file:
        return make_response('File not found', 401)
    return send_file(BytesIO(file.file), attachment_filename=f"{file_name}", as_attachment=True)


@app.route('/files/<string:file_name>', methods=['DELETE'])
@token_required
def delete_file(current_user, file_name):
    file = Files.query.filter(Files.file_name == file_name,
                              Files.user == current_user.name).first()
    if not file:
        return make_response('File not found', 401)
    database.session.delete(file)
    database.session.commit()
    return jsonify({'message': 'file deleted successfully'})


if __name__ == '__main__':
    app.run()
