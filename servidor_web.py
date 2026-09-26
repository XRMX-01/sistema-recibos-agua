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
            body {{ font-family: Arial; background-color: #0066cc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-box {{ background: white; padding: 30px; border-radius: 10px; width: 300px; text-align: center; }}
            h1 {{ color: #0066cc; font-size: 24px; }}
            input {{ width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
            button {{ background-color: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }}
            .error {{ color: red; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>Sistema de Recibos</h1>
            <form method="POST">
                <input type="text" name="usuario" placeholder="Usuario" required>
                <input type="password" name="contrasena" id="contrasena" placeholder="Contraseña" required>
                <label style="font-size: 12px; text-align: left; display: block; margin-bottom: 10px;">
                    <input type="checkbox" onclick="mostrarContrasena()"> Mostrar contraseña
                </label>
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
            body { font-family: Arial; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #0066cc; text-align: center; }
            .logout { text-align: right; margin-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; background: white; margin-top: 20px; font-size: 13px; }
            th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
            th { background-color: #0066cc; color: white; }
            .verde { background-color: #d4edda; }
            .amarillo { background-color: #fff3cd; }
            .rojo { background-color: #f8d7da; }
            .azul { background-color: #d1ecf1; }
            .btn-agregar { background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-size: 14px; display: inline-block; }
            .btn-editar { background-color: #007bff; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; display: inline-block; margin: 2px; }
            .btn-eliminar { background-color: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; display: inline-block; margin: 2px; }
        </style>
    </head>
    <body>
        <div class="logout"><a href="/logout">Cerrar sesión</a></div>
        <h1>Lista de Clientes</h1>
        <a href="/agregar" class="btn-agregar">+ Agregar Cliente</a>
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
                <td>{c[1]}</td>
                <td>{c[2]}</td>
                <td>{c[3]}</td>
                <td>{c[4]}</td>
                <td>{c[5]}</td>
                <td>{c[6]}</td>
                <td>{c[7]}</td>
                <td>{c[8]}</td>
                <td>{c[9]}</td>
                <td>{c[10]}</td>
                <td>{c[11]}</td>
                <td>
                    <a href="/editar/{c[0]}" class="btn-editar">Editar</a>
                    <a href="/eliminar/{c[0]}" class="btn-eliminar" onclick="return confirm('¿Eliminar a {c[1]}?')">Eliminar</a>
                </td>
            </tr>
        """

    html += """
        </table>
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
            body { font-family: Arial; padding: 20px; background-color: #f4f4f4; }
            h1 { color: #0066cc; }
            input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            button { background-color: #28a745; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
            .volver { display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; }
        </style>
    </head>
    <body>
        <a href="/" class="volver">← Volver a la lista</a>
        <h1>Agregar Cliente</h1>
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
            <button type="submit">Guardar Cliente</button>
        </form>
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
    
    fecha_pago = c[7].strftime('%Y-%m-%d') if c[7] else ''
    fecha_corte = c[8].strftime('%Y-%m-%d') if c[8] else ''
    
    return f"""
    <html>
    <head>
        <title>Editar Cliente</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial; padding: 20px; background-color: #f4f4f4; }}
            h1 {{ color: #0066cc; }}
            input, select {{ width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }}
            button {{ background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }}
            .volver {{ display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; }}
        </style>
    </head>
    <body>
        <a href="/" class="volver">← Volver a la lista</a>
        <h1>Editar Cliente</h1>
        <form method="POST">
            <label>Nombres:</label>
            <input type="text" name="nombre_completo" value="{c[1] or ''}" required>
            <label>Apellidos:</label>
            <input type="text" name="apellidos" value="{c[2] or ''}">
            <label>DNI:</label>
            <input type="text" name="dni" value="{c[3] or ''}" maxlength="8">
            <label>Calle:</label>
            <input type="text" name="calle" value="{c[4] or ''}">
            <label>Mz:</label>
            <input type="text" name="mz" value="{c[5] or ''}">
            <label>Lote:</label>
            <input type="text" name="lote" value="{c[6] or ''}">
            <label>Fecha de Pago:</label>
            <input type="date" name="fecha_pago" value="{fecha_pago}">
            <label>Fecha de Corte:</label>
            <input type="date" name="fecha_corte" value="{fecha_corte}">
            <label>Monto a Pagar:</label>
            <input type="number" step="0.01" name="monto_pagar" value="{c[9] or ''}">
            <label>Mes:</label>
            <input type="text" name="mes" value="{c[10] or ''}">
            <label>Estado:</label>
            <select name="estado">
                <option value="Puntual" {'selected' if c[11] == 'Puntual' else ''}>Puntual</option>
                <option value="Pendiente" {'selected' if c[11] == 'Pendiente' else ''}>Pendiente</option>
                <option value="Deudor" {'selected' if c[11] == 'Deudor' else ''}>Deudor</option>
                <option value="Justificado" {'selected' if c[11] == 'Justificado' else ''}>Justificado</option>
            </select>
            <button type="submit">Guardar Cambios</button>
        </form>
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
