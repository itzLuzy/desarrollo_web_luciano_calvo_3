from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db
from sqlalchemy.sql import text
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Portada
@app.route('/')
def index():
    por_pagina = 5
    actividades = db.get_activities(por_pagina)
    data = []
    for act in actividades:
        tema = db.get_theme_by_activity(act.id)
        if tema:
            if tema.glosa_otro:
                tema = tema.glosa_otro
            else:
                tema = tema.tema
        else:
            tema = "no especificado"
        comuna = db.get_comuna_by_id(act.comuna_id)
        foto = None
        if len(db.get_activity_photos(act.id)) > 0:
            foto = db.get_activity_photos(act.id)[0]
        foto = foto.ruta_archivo if foto else "default.jpg"
        data.append({
            "id": act.id,
            "inicio": act.dia_hora_inicio,
            "termino": act.dia_hora_termino,
            "comuna": comuna.nombre,
            "sector": act.sector,
            "tema": tema,
            "foto": url_for('static', filename=foto)
        })
    return render_template('index.html', data=data)

# Formulario
@app.route('/formulario')
def formulario():
    regiones = db.get_regions()
    temas = db.temas
    contact_methods = db.contactos
    return render_template('formulario.html', regiones=regiones, temas=temas, contact_methods=contact_methods)

@app.route('/agregar', methods=['POST'])
def agregar():
    # Actividad
    nombre = request.form['nombre']
    email = request.form['email']
    celular = request.form.get('telefono')
    descripcion = request.form.get('descripcion', '')
    sector = request.form.get('sector', '')
    comuna_id = int(request.form['comuna'])
    inicio = datetime.strptime(request.form['inicio'], '%Y-%m-%dT%H:%M')
    termino_raw = request.form.get('termino')
    termino = datetime.strptime(termino_raw, '%Y-%m-%dT%H:%M') if termino_raw else None

    db.create_activity(
        name=nombre,
        email=email,
        celular=celular,
        description=descripcion,
        comuna_id=comuna_id,
        init_date=inicio,
        end_date=termino,
        sector=sector
    )

    actividad = db.get_last_activity()

    # Tema
    tema = request.form.get('tema')
    otro_tema = request.form.get('otro_tema')
    db.create_activity_theme(
        activity_id=actividad.id,
        tema=tema,
        glosa_otro=otro_tema if tema == 'otro' else None
    )

    # Contactos
    contactos = request.form.getlist('contactos')
    print(contactos)
    identificadores = request.form.getlist('identificadores[]')
    for nombre, identificador in zip(contactos, identificadores):
        if nombre and identificador:
            db.create_contact_method(
                activity_id=actividad.id,
                name=nombre,
                identifier=identificador
            )


    # Fotos
    files = request.files.getlist('fotos[]')
    for archivo in files:
        if archivo and archivo.filename:
            nombre_archivo = archivo.filename
            ruta = app.config['UPLOAD_FOLDER'] + '/' + nombre_archivo
            archivo.save('static/' + ruta)
            db.create_photo(
                activity_id=actividad.id,
                name=nombre_archivo,
                path=ruta
            )
    return redirect(url_for('index'))

# Listado
@app.route('/listado')
def listado():
    por_pagina = 5
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * por_pagina
    actividades = db.get_activities(por_pagina, offset)
    data = []
    for act in actividades:
        tema = db.get_theme_by_activity(act.id)
        if tema:
            if tema.glosa_otro:
                tema = tema.glosa_otro
            else:
                tema = tema.tema
        else:
            tema = "no especificado"
        comuna = db.get_comuna_by_id(act.comuna_id)
        n_fotos = db.count_photos_by_activity(act.id)
        data.append({
            "id": act.id,
            "inicio": act.dia_hora_inicio,
            "termino": act.dia_hora_termino,
            "comuna": comuna.nombre,
            "sector": act.sector,
            "tema": tema,
            "nombre": act.nombre,
            "n_fotos": n_fotos
        })
    total = db.count_activities()
    return render_template('listado.html', data=data, pagina=page, total=total, por_pagina=por_pagina)

# Detalle de actividad
@app.route('/actividad/<int:actividad_id>')
def detalle(actividad_id):
    act= db.get_activity_by_id(actividad_id)
    tema = db.get_theme_by_activity(act.id)
    if tema:
        if tema.glosa_otro:
            tema = tema.glosa_otro
        else:
            tema = tema.tema
    else:
        tema = "no especificado"
    comuna = db.get_comuna_by_id(act.comuna_id)
    region = db.get_region_by_id(comuna.region_id)
    fotos = db.get_activity_photos(actividad_id)
    contactos = db.get_activity_contact_methods(actividad_id)
    data = {
        "id": act.id,
        "inicio": act.dia_hora_inicio,
        "termino": act.dia_hora_termino,
        "comuna": comuna.nombre,
        "region": region.nombre,
        "sector": act.sector,
        "tema": tema,
        "nombre": act.nombre,
        "email" : act.email,
        "celular" : act.celular,
        "descripcion" : act.descripcion,
        "contactos" : contactos,
        "fotos" : fotos
    }

    return render_template('detalle.html', data=data)


# Obtener comunas de la bd según región
@app.route('/get_comunas/<int:region_id>')
def get_comunas(region_id):
    comunas = db.get_comunas_by_region(region_id)
    comunas_dict = [{"id": c.id, "nombre": c.nombre} for c in comunas]
    return jsonify(comunas_dict)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

@app.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/api/estadisticas/actividades_por_dia')
def actividades_por_dia():
    session = db.SessionLocal()
    result = session.execute(text("""
        SELECT DATE(dia_hora_inicio) as fecha, COUNT(*) as cantidad
        FROM actividad
        GROUP BY DATE(dia_hora_inicio)
        ORDER BY fecha
    """))
    data = [{'fecha': str(r[0]), 'cantidad': r[1]} for r in result.fetchall()]
    session.close()
    return jsonify(data)

@app.route('/api/estadisticas/actividades_por_tema')
def actividades_por_tema():
    session = db.SessionLocal()
    result = session.execute(text("""
        SELECT tema, COUNT(*) FROM actividad_tema GROUP BY tema
    """))
    data = [{'tema': r[0], 'cantidad': r[1]} for r in result.fetchall()]
    session.close()
    return jsonify(data)

@app.route('/api/estadisticas/actividades_por_horario')
def actividades_por_horario():
    session = db.SessionLocal()
    result = session.execute(text("""
        SELECT MONTH(dia_hora_inicio) as mes,
            SUM(CASE WHEN HOUR(dia_hora_inicio) < 12 THEN 1 ELSE 0 END) as manana,
            SUM(CASE WHEN HOUR(dia_hora_inicio) BETWEEN 12 AND 17 THEN 1 ELSE 0 END) as tarde,
            SUM(CASE WHEN HOUR(dia_hora_inicio) >= 18 THEN 1 ELSE 0 END) as noche
        FROM actividad
        GROUP BY mes
        ORDER BY mes
    """))
    data = [{'mes': r[0], 'manana': int(r[1]), 'tarde': int(r[2]), 'noche': int(r[3])} for r in result.fetchall()]
    session.close()
    return jsonify(data)


@app.route('/api/comentarios/agregar', methods=['POST'])
def agregar_comentario():
    data = request.get_json()
    errores = []
    if not data.get('nombre') or len(data['nombre']) < 3 or len(data['nombre']) > 80:
        errores.append("Nombre inválido")
    if not data.get('texto') or len(data['texto']) < 5:
        errores.append("Comentario muy corto")
    if errores:
        return jsonify({'ok': False, 'errores': errores}), 400

    session = db.SessionLocal()
    comentario = db.Comentario(
        actividad_id=data['actividad_id'],
        nombre=data['nombre'],
        texto=data['texto'],
        fecha=datetime.now()
    )
    session.add(comentario)
    session.commit()
    session.close()
    return jsonify({'ok': True})

@app.route('/api/comentarios/<int:actividad_id>')
def obtener_comentarios(actividad_id):
    session = db.SessionLocal()
    result = session.query(db.Comentario).filter_by(actividad_id=actividad_id).order_by(db.Comentario.fecha.desc()).all()
    comentarios = []
    for c in result:
        comentarios.append({
                "fecha": c.fecha.strftime("%Y-%m-%d %H:%M"),
                "nombre": c.nombre,
                "texto": c.texto
        })
    session.close()
    return jsonify(comentarios)

