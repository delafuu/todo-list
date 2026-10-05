from flask import Flask, render_template, jsonify, request
import uuid
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__, static_folder='comun', static_url_path='/comun')

# Render inyectará aquí la URL de la base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def init_db():
    if not DATABASE_URL:
        return
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    # Creamos la tabla si es la primera vez que arranca
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            orden INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

if DATABASE_URL:
    init_db()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if not DATABASE_URL: return jsonify([])
    conn = psycopg2.connect(DATABASE_URL)
    cur = get_db_cursor(conn)
    cur.execute('SELECT * FROM tareas ORDER BY orden')
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r["id"], "text": r["text"], "done": bool(r["done"])} for r in filas])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    texto = request.form.get('text')
    if not texto or texto.strip() == '':
        return jsonify({"error": "El texto es obligatorio"}), 400
        
    nuevo_id = uuid.uuid4().hex
    conn = psycopg2.connect(DATABASE_URL)
    cur = get_db_cursor(conn)
    cur.execute('SELECT MAX(orden) FROM tareas')
    max_orden = cur.fetchone()[0]
    max_orden = 0 if max_orden is None else max_orden + 1
    
    cur.execute('INSERT INTO tareas (id, text, done, orden) VALUES (%s, %s, 0, %s)', 
                 (nuevo_id, texto, max_orden))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': nuevo_id, 'text': texto, 'done': False}), 201

@app.route('/api/toggle_task', methods=['POST'])
def toggle_task():
    task_id = request.form.get('id')
    conn = psycopg2.connect(DATABASE_URL)
    cur = get_db_cursor(conn)
    cur.execute('SELECT * FROM tareas WHERE id = %s', (task_id,))
    tarea = cur.fetchone()
    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404
        
    nuevo_estado = 0 if tarea["done"] else 1
    cur.execute('UPDATE tareas SET done = %s WHERE id = %s', (nuevo_estado, task_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": task_id, "text": tarea["text"], "done": bool(nuevo_estado)}), 200

@app.route('/api/delete_task', methods=['POST'])
def delete_task():
    task_id = request.form.get('id')
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('DELETE FROM tareas WHERE id = %s', (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return '', 204

@app.route('/api/move_task', methods=['POST'])
def move_task():
    task_id = request.form.get('id')
    position = int(request.form.get('position', -1))
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = get_db_cursor(conn)
    cur.execute('SELECT * FROM tareas ORDER BY orden')
    filas = cur.fetchall()
    tareas = [{"id": r["id"], "text": r["text"], "done": bool(r["done"])} for r in filas]
    
    current_idx = next((i for i, t in enumerate(tareas) if t['id'] == task_id), -1)
    if current_idx != -1:
        tarea_a_mover = tareas.pop(current_idx)
        position = max(0, min(position, len(tareas)))
        tareas.insert(position, tarea_a_mover)
        for index, tarea in enumerate(tareas):
            cur.execute('UPDATE tareas SET orden = %s WHERE id = %s', (index, tarea["id"]))
        conn.commit()
        
    cur.close()
    conn.close()
    return jsonify(tareas), 200

@app.route('/api/edit_task', methods=['POST'])
def edit_task():
    task_id = request.form.get('id')
    new_text = request.form.get('text')
    
    if not new_text or new_text.strip() == '':
        return jsonify({"error": "El texto no puede estar vacío"}), 400
        
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('UPDATE tareas SET text = %s WHERE id = %s', (new_text, task_id))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"id": task_id, "text": new_text}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070)