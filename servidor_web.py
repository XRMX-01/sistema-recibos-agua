from flask import Flask, request, session, redirect, url_for
import psycopg2
import os
import bcrypt

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_123"

def conectar():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        sslmode="require"
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT contrasena_hash FROM usuarios WHERE nombre_usuario = %s", (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if resultado:
            hash_guardado = resultado[0].encode('utf-8')
            if bcrypt.checkpw(contrasena.encode('utf-8'), hash_guardado):
                session['usuario'] = usuario
                return redirect(url_for('inicio'))
        
        error = "Usuario o contraseña incorrectos"
    
    return f"""
    <html>
    <head>
        <title>Login - Sistema de Recibos</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #0066cc 0%, #003d7a 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-box {{ background: white; padding: 40px 30px; border-radius: 15px; width: 340px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); text-align: center; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
            h1 {{ color: #0066cc; font-size: 22px; margin-bottom: 25px; }}
            input {{ width: 100%; padding: 12px 15px; margin: 8px 0; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border 0.3s; }}
            input:focus {{ border-color: #0066cc; outline: none; }}
            button {{ background: linear-gradient(135deg, #0066cc, #004a99); color: white; padding: 12px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; margin-top: 10px; transition: transform 0.2s; }}
            button:hover {{ transform: scale(1.02); }}
            .error {{ color: #dc3545; font-size: 13px; margin-top: 10px; }}
            label {{ font-size: 12px; color: #555; display: flex; align-items: center; gap: 5px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="logo">💧</div>
            <h1>Sistema de Recibos</h1>
            <form method="POST">
                <input type="text" name="usuario" placeholder="Usuario" required>
                <input type="password" name="contrasena" id="contrasena" placeholder="Contraseña" required>
                <label><input type="checkbox" onclick="mostrarContrasena()"> Mostrar contraseña</label>
                <button type="submit">Ingresar</button>
            </form>
            <p class="error">{error if error else ''}</p>
        </div>
        <script>
            function mostrarContrasena() {{
                var campo = document.getElementById("contrasena");
                if (campo.type === "password") {{
                    campo.type = "text";
                }} else {{
                    campo.type = "password";
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.route('/')
def inicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id_cliente, nombre_completo, apellidos, dni, calle, mz, lote, 
               fecha_pago, fecha_corte, monto_pagar, mes, estado 
        FROM clientes ORDER BY id_cliente
    """)
    clientes = cursor.fetchall()
    cursor.close()
    conexion.close()

    html = """
    <html>
    <head>
        <title>Sistema de Recibos de Agua</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }
            .header { display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .header h1 { color: #0066cc; margin: 0; font-size: 22px; }
            .header a { color: #dc3545; text-decoration: none; font-weight: bold; }
            .btn-agregar { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 14px; display: inline-block; font-weight: bold; box-shadow: 0 2px 5px rgba(40,167,69,0.3); }
            .tabla-container { overflow-x: auto; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 10px; }
            table { width: 100%; border-collapse: collapse; font-size: 13px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
            th { background-color: #0066cc; color: white; font-weight: bold; }
            tr:hover { background-color: #f8f9fa; }
            .verde { background-color: #d4edda !important; }
            .amarillo { background-color: #fff3cd !important; }
            .rojo { background-color: #f8d7da !important; }
            .azul { background-color: #d1ecf1 !important; }
            .btn-editar { background-color: #007bff; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; display: inline-block; margin: 2px; }
            .btn-eliminar { background-color: #dc3545; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; display: inline-block; margin: 2px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💧 Lista de Clientes</h1>
            <a href="/logout">Cerrar sesión</a>
        </div>
        <a href="/agregar" class="btn-agregar">+ Agregar Cliente</a>
        <br><br>
        <div class="tabla-container">
        <table>
            <tr>
                <th>ID</th>
                <th>Nombres</th>
                <th>Apellidos</th>
                <th>DNI</th>
                <th>Calle</th>
                <th>Mz</th>
                <th>Lote</th>
                <th>Fecha Pago</th>
                <th>Fecha Corte</th>
                <th>Monto</th>
                <th>Mes</th>
                <th>Estado</th>
                <th>Acciones</th>
            </tr>
    """

    for c in clientes:
        estado = c[11] if c[11] else "Puntual"
        color = ""
        if estado == "Puntual":
            color = "verde"
        elif estado == "Pendiente":
            color = "amarillo"
        elif estado == "Deudor" or estado == "Corte":
            color = "rojo"
        elif estado == "Justificado":
            color = "azul"
        
        html += f"""
            <tr class="{color}">
                <td>{c[0]}</td>
                <td>{c[1] or ''}</td>
                <td>{c[2] or ''}</td>
                <td>{c[3] or ''}</td>
                <td>{c[4] or ''}</td>
                <td>{c[5] or ''}</td>
                <td>{c[6] or ''}</td>
                <td>{str(c[7])[:10] if c[7] else ''}</td>
                <td>{str(c[8])[:10] if c[8] else ''}</td>
                <td>{c[9] or ''}</td>
                <td>{c[10] or ''}</td>
                <td>{c[11] or ''}</td>
                <td>
                    <a href="/editar/{c[0]}" class="btn-editar">✏️ Editar</a>
                    <a href="/eliminar/{c[0]}" class="btn-eliminar" onclick="return confirm('¿Eliminar a {c[1]}?')">🗑️ Eliminar</a>
                </td>
            </tr>
        """

    html += """
        </table>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre_completo, apellidos, dni, calle, mz, lote, fecha_pago, fecha_corte, monto_pagar, mes, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['nombre_completo'],
            request.form['apellidos'],
            request.form['dni'],
            request.form['calle'],
            request.form['mz'],
            request.form['lote'],
            request.form['fecha_pago'] or None,
            request.form['fecha_corte'] or None,
            request.form['monto_pagar'] or None,
            request.form['mes'],
            request.form['estado']
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('inicio'))
    
    return """
    <html>
    <head>
        <title>Agregar Cliente</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }
            .contenedor { max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0066cc; margin-top: 0; }
            label { font-size: 13px; color: #555; font-weight: bold; }
            input, select { width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
            input:focus, select:focus { border-color: #0066cc; outline: none; }
            button { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
            .volver { display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/" class="volver">← Volver a la lista</a>
            <h1>➕ Agregar Cliente</h1>
            <form method="POST">
                <label>Nombres:</label>
                <input type="text" name="nombre_completo" required>
                <label>Apellidos:</label>
                <input type="text" name="apellidos">
                <label>DNI:</label>
                <input type="text" name="dni" maxlength="8">
                <label>Calle:</label>
                <input type="text" name="calle">
                <label>Mz:</label>
                <input type="text" name="mz">
                <label>Lote:</label>
                <input type="text" name="lote">
                <label>Fecha de Pago:</label>
                <input type="date" name="fecha_pago">
                <label>Fecha de Corte:</label>
                <input type="date" name="fecha_corte">
                <label>Monto a Pagar:</label>
                <input type="number" step="0.01" name="monto_pagar">
                <label>Mes:</label>
                <input type="text" name="mes">
                <label>Estado:</label>
                <select name="estado">
                    <option value="Puntual">Puntual</option>
                    <option value="Pendiente">Pendiente</option>
                    <option value="Deudor">Deudor</option>
                    <option value="Justificado">Justificado</option>
                </select>
                <button type="submit">💾 Guardar Cliente</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/editar/<int:id_cliente>', methods=['GET', 'POST'])
def editar(id_cliente):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE clientes SET nombre_completo=%s, apellidos=%s, dni=%s, calle=%s, mz=%s, lote=%s, 
            fecha_pago=%s, fecha_corte=%s, monto_pagar=%s, mes=%s, estado=%s
            WHERE id_cliente=%s
        """, (
            request.form['nombre_completo'],
            request.form['apellidos'],
            request.form['dni'],
            request.form['calle'],
            request.form['mz'],
            request.form['lote'],
            request.form['fecha_pago'] or None,
            request.form['fecha_corte'] or None,
            request.form['monto_pagar'] or None,
            request.form['mes'],
            request.form['estado'],
            id_cliente
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('inicio'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id_cliente,))
    c = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    fecha_pago = str(c[7])[:10] if c[7] else ''
    fecha_corte = str(c[8])[:10] if c[8] else ''
    
    nombre = c[1] if c[1] else ''
    apellidos = c[2] if c[2] else ''
    dni = c[3] if c[3] else ''
    calle = c[4] if c[4] else ''
    mz = c[5] if c[5] else ''
    lote = c[6] if c[6] else ''
    monto = c[9] if c[9] else ''
    mes = c[10] if c[10] else ''
    
    return f"""
    <html>
    <head>
        <title>Editar Cliente</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }}
            .contenedor {{ max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #0066cc; margin-top: 0; }}
            label {{ font-size: 13px; color: #555; font-weight: bold; }}
            input, select {{ width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }}
            input:focus, select:focus {{ border-color: #0066cc; outline: none; }}
            button {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }}
            .volver {{ display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/" class="volver">← Volver a la lista</a>
            <h1>✏️ Editar Cliente</h1>
            <form method="POST">
                <label>Nombres:</label>
                <input type="text" name="nombre_completo" value="{nombre}" required>
                <label>Apellidos:</label>
                <input type="text" name="apellidos" value="{apellidos}">
                <label>DNI:</label>
                <input type="text" name="dni" value="{dni}" maxlength="8">
                <label>Calle:</label>
                <input type="text" name="calle" value="{calle}">
                <label>Mz:</label>
                <input type="text" name="mz" value="{mz}">
                <label>Lote:</label>
                <input type="text" name="lote" value="{lote}">
                <label>Fecha de Pago:</label>
                <input type="date" name="fecha_pago" value="{fecha_pago}">
                <label>Fecha de Corte:</label>
                <input type="date" name="fecha_corte" value="{fecha_corte}">
                <label>Monto a Pagar:</label>
                <input type="number" step="0.01" name="monto_pagar" value="{monto}">
                <label>Mes:</label>
                <input type="text" name="mes" value="{mes}">
                <label>Estado:</label>
                <select name="estado">
                    <option value="Puntual" {'selected' if c[11] == 'Puntual' else ''}>Puntual</option>
                    <option value="Pendiente" {'selected' if c[11] == 'Pendiente' else ''}>Pendiente</option>
                    <option value="Deudor" {'selected' if c[11] == 'Deudor' else ''}>Deudor</option>
                    <option value="Justificado" {'selected' if c[11] == 'Justificado' else ''}>Justificado</option>
                </select>
                <button type="submit">💾 Guardar Cambios</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/eliminar/<int:id_cliente>')
def eliminar(id_cliente):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inicio'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
