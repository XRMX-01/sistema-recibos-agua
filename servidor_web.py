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
        SELECT nombre_completo, apellidos, dni, calle, mz, lote, 
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
            .logout { text-align: right; }
            table { width: 100%; border-collapse: collapse; background: white; margin-top: 20px; font-size: 14px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #0066cc; color: white; }
            .verde { background-color: #d4edda; }
            .amarillo { background-color: #fff3cd; }
            .rojo { background-color: #f8d7da; }
            .azul { background-color: #d1ecf1; }
        </style>
    </head>
    <body>
        <div class="logout"><a href="/logout">Cerrar sesión</a></div>
        <h1>Lista de Clientes</h1>
        <table>
            <tr>
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
            </tr>
    """

    for c in clientes:
        estado = c[10] if c[10] else "Puntual"
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
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
