from flask import Flask, request, session, redirect, url_for, send_from_directory, make_response
import psycopg2
import os
import bcrypt
from datetime import date
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_123"

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def conectar():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        sslmode="require"
    )

def calcular_edad(fecha_nac):
    if not fecha_nac:
        return ""
    hoy = date.today()
    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    return edad

def limpiar_texto(texto):
    if not texto:
        return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js')

@app.route('/icono.png')
def icono():
    return send_from_directory('.', 'icono.png')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT contrasena_hash, rol FROM usuarios WHERE nombre_usuario = %s", (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if resultado:
            hash_guardado = resultado[0].encode('utf-8')
            if bcrypt.checkpw(contrasena.encode('utf-8'), hash_guardado):
                session['usuario'] = usuario
                session['rol'] = resultado[1] if resultado[1] else 'cliente'
                return redirect(url_for('inicio'))
        
        error = "Usuario o contraseña incorrectos"
    
    return f"""
    <html>
    <head>
        <title>Login - Sistema de Recibos</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #0066cc 0%, #003d7a 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-box {{ background: white; padding: 40px 30px; border-radius: 15px; width: 340px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); text-align: center; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
            h1 {{ color: #0066cc; font-size: 22px; margin-bottom: 25px; }}
            input {{ width: 100%; padding: 12px 15px; margin: 8px 0; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }}
            input:focus {{ border-color: #0066cc; outline: none; }}
            button {{ background: linear-gradient(135deg, #0066cc, #004a99); color: white; padding: 12px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; margin-top: 10px; }}
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
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/service-worker.js');
            }}
        </script>
    </body>
    </html>
    """

@app.route('/')
def inicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if session.get('rol') == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('cliente'))

@app.route('/admin')
def admin():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    buscar = request.args.get('buscar', '')
    mensaje = request.args.get('mensaje', '')
    
    conexion = conectar()
    cursor = conexion.cursor()
    
    if buscar:
        cursor.execute("""
            SELECT id_cliente, nombre_completo, apellidos, dni, direccion, correo, celular, calle, mz, lote, 
                   fecha_pago, fecha_corte, monto_pagar, mes, estado, fecha_nacimiento 
            FROM clientes 
            WHERE nombre_completo ILIKE %s 
               OR apellidos ILIKE %s 
               OR dni ILIKE %s 
               OR calle ILIKE %s 
               OR mz ILIKE %s 
               OR lote ILIKE %s 
               OR estado ILIKE %s
            ORDER BY id_cliente
        """, (f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%'))
    else:
        cursor.execute("""
            SELECT id_cliente, nombre_completo, apellidos, dni, direccion, correo, celular, calle, mz, lote, 
                   fecha_pago, fecha_corte, monto_pagar, mes, estado, fecha_nacimiento 
            FROM clientes ORDER BY id_cliente
        """)
    
    clientes = cursor.fetchall()
    cursor.close()
    conexion.close()

    html = f"""
    <html>
    <head>
        <title>Sistema de Recibos de Agua</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .header h1 {{ color: #0066cc; margin: 0; font-size: 22px; }}
            .header a {{ color: #dc3545; text-decoration: none; font-weight: bold; }}
            .btn-agregar {{ background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 14px; display: inline-block; font-weight: bold; }}
            .btn-mes {{ background: linear-gradient(135deg, #ffc107, #d39e00); color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 14px; display: inline-block; font-weight: bold; margin-left: 10px; }}
            .btn-borrar {{ background: linear-gradient(135deg, #dc3545, #a71d2a); color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 14px; display: inline-block; font-weight: bold; margin-left: 10px; }}
            .btn-pdf {{ background: linear-gradient(135deg, #6f42c1, #4b2a89); color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 14px; display: inline-block; font-weight: bold; margin-left: 10px; }}
            .mensaje {{ background-color: #d4edda; color: #155724; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-weight: bold; }}
            .buscador {{ display: flex; gap: 10px; margin-bottom: 20px; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .buscador input {{ flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }}
            .buscador button {{ background: linear-gradient(135deg, #0066cc, #004a99); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }}
            .buscador a {{ background: #6c757d; color: white; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; }}
            .tabla-container {{ overflow-x: auto; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); padding: 10px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background-color: #0066cc; color: white; font-weight: bold; }}
            .verde {{ background-color: #d4edda; color: #155724; font-weight: bold; text-align: center; }}
            .amarillo {{ background-color: #fff3cd; color: #856404; font-weight: bold; text-align: center; }}
            .rojo {{ background-color: #f8d7da; color: #721c24; font-weight: bold; text-align: center; }}
            .azul {{ background-color: #d1ecf1; color: #0c5460; font-weight: bold; text-align: center; }}
            .btn-editar {{ background-color: #007bff; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; display: inline-block; margin: 2px; }}
            .btn-eliminar {{ background-color: #dc3545; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; display: inline-block; margin: 2px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💧 Lista de Clientes (Admin)</h1>
            <a href="/logout">Cerrar sesión</a>
        </div>
        <a href="/agregar" class="btn-agregar">+ Agregar Cliente</a>
        <a href="/generar_mes" class="btn-mes">📅 Generar Mes Nuevo</a>
        <a href="/borrar_mes" class="btn-borrar">🗑️ Borrar Mes</a>
        <a href="/pdf_admin?buscar={buscar}" class="btn-pdf" target="_blank">📄 Imprimir PDF</a>
        <br><br>
        {f'<div class="mensaje">{mensaje}</div>' if mensaje else ''}
        <form class="buscador" method="GET">
            <input type="text" name="buscar" placeholder="Buscar por nombre, DNI, calle, Mz, lote o estado..." value="{buscar}">
            <button type="submit">🔍 Buscar</button>
            <a href="/admin">Mostrar todos</a>
        </form>
        <div class="tabla-container">
        <table>
            <tr>
                <th>ID</th>
                <th>Nombres</th>
                <th>Apellidos</th>
                <th>DNI</th>
                <th>Edad</th>
                <th>Calle</th>
                <th>Mz</th>
                <th>Lote</th>
                <th>Estado</th>
                <th>Acciones</th>
            </tr>
    """

    for c in clientes:
        estado = c[14] if c[14] else "Puntual"
        color = ""
        if estado == "Puntual":
            color = "verde"
        elif estado == "Pendiente":
            color = "amarillo"
        elif estado == "Deudor" or estado == "Corte":
            color = "rojo"
        elif estado == "Justificado":
            color = "azul"
        
        edad = calcular_edad(c[15])
        
        html += f"""
            <tr>
                <td>{c[0]}</td>
                <td>{c[1] or ''}</td>
                <td>{c[2] or ''}</td>
                <td>{c[3] or ''}</td>
                <td>{edad}</td>
                <td>{c[7] or ''}</td>
                <td>{c[8] or ''}</td>
                <td>{c[9] or ''}</td>
                <td class="{color}">{c[14] or ''}</td>
                <td>
                    <a href="/editar/{c[0]}" class="btn-editar">✏️ Editar</a>
                    <a href="/eliminar/{c[0]}" class="btn-eliminar" onclick="return confirm('¿Eliminar a {c[1]}?')">🗑️ Eliminar</a>
                </td>
            </tr>
        """

    html += """
        </table>
        </div>
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js');
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/pdf_admin')
def pdf_admin():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    buscar = request.args.get('buscar', '')
    
    conexion = conectar()
    cursor = conexion.cursor()
    
    if buscar:
        cursor.execute("""
            SELECT id_cliente, nombre_completo, apellidos, dni, calle, mz, lote, monto_pagar, mes, estado
            FROM clientes 
            WHERE nombre_completo ILIKE %s 
               OR apellidos ILIKE %s 
               OR dni ILIKE %s 
               OR calle ILIKE %s 
               OR mz ILIKE %s 
               OR lote ILIKE %s 
               OR estado ILIKE %s
            ORDER BY id_cliente
        """, (f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%', f'%{buscar}%'))
    else:
        cursor.execute("""
            SELECT id_cliente, nombre_completo, apellidos, dni, calle, mz, lote, monto_pagar, mes, estado
            FROM clientes ORDER BY id_cliente
        """)
    
    clientes = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, limpiar_texto("LISTA DE CLIENTES"), ln=True, align="C")
    
    if buscar:
        pdf.set_font("helvetica", "I", 11)
        pdf.cell(0, 8, limpiar_texto(f"Filtro: {buscar}"), ln=True, align="C")
    
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 8, limpiar_texto(f"Fecha: {date.today().strftime('%d/%m/%Y')}"), ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(10, 8, "ID", 1)
    pdf.cell(30, 8, "Nombres", 1)
    pdf.cell(25, 8, "Apellidos", 1)
    pdf.cell(18, 8, "DNI", 1)
    pdf.cell(25, 8, "Calle", 1)
    pdf.cell(10, 8, "Mz", 1)
    pdf.cell(10, 8, "Lote", 1)
    pdf.cell(15, 8, "Monto", 1)
    pdf.cell(18, 8, "Mes", 1)
    pdf.cell(18, 8, "Estado", 1)
    pdf.ln()
    
    pdf.set_font("helvetica", size=7)
    for c in clientes:
        pdf.cell(10, 7, str(c[0]), 1)
        pdf.cell(30, 7, limpiar_texto(c[1] or '')[:16], 1)
        pdf.cell(25, 7, limpiar_texto(c[2] or '')[:14], 1)
        pdf.cell(18, 7, limpiar_texto(c[3] or ''), 1)
        pdf.cell(25, 7, limpiar_texto(c[4] or '')[:12], 1)
        pdf.cell(10, 7, limpiar_texto(c[5] or ''), 1)
        pdf.cell(10, 7, limpiar_texto(c[6] or ''), 1)
        pdf.cell(15, 7, str(c[7] or ''), 1)
        pdf.cell(18, 7, limpiar_texto(c[8] or '')[:10], 1)
        pdf.cell(18, 7, limpiar_texto(c[9] or '')[:10], 1)
        pdf.ln()
    
    response = make_response(bytes(pdf.output(dest='S')))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=lista_clientes.pdf'
    return response

@app.route('/pdf_cliente')
def pdf_cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT c.id_cliente, c.nombre_completo, c.apellidos, c.dni, c.direccion, c.calle, c.mz, c.lote, c.celular,
               c.reposicion, c.inscripcion, c.multa
        FROM clientes c
        INNER JOIN usuarios u ON c.id_cliente = u.id_cliente
        WHERE u.nombre_usuario = %s
    """, (session['usuario'],))
    c = cursor.fetchone()
    
    if not c:
        cursor.close()
        conexion.close()
        return "No se encontraron datos."
    
    cursor.execute("""
        SELECT mes, anio, monto, fecha_pago, fecha_corte, estado 
        FROM facturas WHERE id_cliente = %s ORDER BY anio, id_factura
    """, (c[0],))
    facturas = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 10, 15)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, limpiar_texto("JUNTA ADMINISTRADORA DE SERVICIOS Y SANEAMIENTO"), ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 8, limpiar_texto("JASS - CHANQUIN - STA. MARIA"), ln=True, align="C")
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, limpiar_texto("Santa Maria Mza. 4 Lote 09 (frente Loza Deportiva) - Puente Viru - Viru"), ln=True, align="C")
    pdf.ln(3)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(60, 8, limpiar_texto("Mes:"), 1)
    if facturas:
        ultimo_mes = facturas[-1][0]
        anio = facturas[-1][1]
        pdf.cell(60, 8, limpiar_texto(f"{ultimo_mes} {anio}"), 1)
    else:
        pdf.cell(60, 8, limpiar_texto("Sin facturas"), 1)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(60, 8, limpiar_texto("N° 000001"), 1)
    pdf.ln()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(60, 8, limpiar_texto("Fecha de Vencimiento:"), 1)
    if facturas:
        fecha_corte = facturas[-1][4]
        pdf.cell(60, 8, limpiar_texto(str(fecha_corte)[:10] if fecha_corte else ''), 1)
    else:
        pdf.cell(60, 8, limpiar_texto(""), 1)
    pdf.cell(60, 8, limpiar_texto(""), 1)
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(30, 8, limpiar_texto("Usuario(a):"), 1)
    pdf.set_font("helvetica", size=10)
    pdf.cell(150, 8, limpiar_texto(f"{c[1]} {c[2] or ''}"), 1)
    pdf.ln()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(30, 8, limpiar_texto("Sector:"), 1)
    pdf.set_font("helvetica", size=10)
    pdf.cell(150, 8, limpiar_texto(f"{c[5] or ''} Mz {c[6] or ''} Lote {c[7] or ''}"), 1)
    pdf.ln(10)
    
    # Tabla CONCEPTO
    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(0, 102, 204)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(150, 8, limpiar_texto("CONCEPTO"), 1, 0, "C", True)
    pdf.cell(30, 8, limpiar_texto("IMPORTE S/"), 1, 0, "C", True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=10)
    
    total = 0
    if facturas:
        for f in facturas:
            pdf.cell(150, 8, limpiar_texto(f"Cuota de Agua - {f[0]} {f[1]}"), 1)
            pdf.cell(30, 8, f"{f[2]:.2f}" if f[2] else "0.00", 1, 0, "R")
            pdf.ln()
            if f[5] in ['Pendiente', 'Deudor', 'Corte']:
                total += f[2] if f[2] else 0
    
    # Cuadro Reposición / Inscripción / Multa
    marcado_repo = "X" if c[9] else ""
    marcado_insc = "X" if c[10] else ""
    marcado_multa = "X" if c[11] else ""
    
    pdf.cell(50, 8, limpiar_texto(f"Reposición [{marcado_repo}]"), 1)
    pdf.cell(50, 8, limpiar_texto(f"Inscripción [{marcado_insc}]"), 1)
    pdf.cell(50, 8, limpiar_texto(f"Multa [{marcado_multa}]"), 1)
    pdf.cell(30, 8, "", 1)
    pdf.ln()
    
    pdf.cell(150, 8, limpiar_texto("Deuda atrasada"), 1)
    pdf.cell(30, 8, "", 1)
    pdf.ln()
    
    pdf.cell(150, 8, limpiar_texto("Por concepto de:"), 1)
    pdf.cell(30, 8, "", 1)
    pdf.ln()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(150, 10, limpiar_texto("TOTAL S/"), 1, 0, "R")
    pdf.cell(30, 10, f"{total:.2f}", 1, 0, "R")
    pdf.ln(15)
    
    pdf.set_font("helvetica", "I", 7)
    pdf.cell(0, 5, limpiar_texto("Vecino(a): pague a tiempo su recibo y evite el corte y el pago de reposicion de servicio."), ln=True)
    pdf.cell(0, 5, limpiar_texto("A LOS CLANDESTINOS: El Hurto del agua es un delito contra el patrimonio, penado por Ley."), ln=True)
    pdf.cell(0, 5, limpiar_texto("El Agua es Vida ¡Cuidala! ... ¡Todos lo necesitamos!"), ln=True, align="C")
    
    response = make_response(bytes(pdf.output(dest='S')))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=recibo.pdf'
    return response

@app.route('/generar_mes', methods=['GET', 'POST'])
def generar_mes():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        mes = request.form['mes']
        anio = request.form['anio']
        monto = request.form['monto']
        fecha_corte = request.form['fecha_corte']
        
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_cliente FROM clientes")
        clientes = cursor.fetchall()
        
        for c in clientes:
            cursor.execute("""
                INSERT INTO facturas (id_cliente, mes, anio, monto, fecha_corte, estado)
                VALUES (%s, %s, %s, %s, %s, 'Pendiente')
            """, (c[0], mes, anio, monto, fecha_corte))
        
        conexion.commit()
        cursor.close()
        conexion.close()
        
        return redirect(url_for('admin', mensaje=f'✅ Se generó el mes de {mes} {anio} para {len(clientes)} clientes.'))
    
    return """
    <html>
    <head>
        <title>Generar Mes Nuevo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }
            .contenedor { max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0066cc; margin-top: 0; }
            label { font-size: 13px; color: #555; font-weight: bold; }
            input, select { width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
            input:focus, select:focus { border-color: #0066cc; outline: none; }
            button { background: linear-gradient(135deg, #ffc107, #d39e00); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
            .volver { display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }
            .info { background-color: #d1ecf1; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 15px; color: #0c5460; }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/admin" class="volver">← Volver a la lista</a>
            <h1>📅 Generar Mes Nuevo</h1>
            <div class="info">Este botón crea una factura nueva (pendiente) para TODOS los clientes.</div>
            <form method="POST">
                <label>Mes:</label>
                <select name="mes">
                    <option value="Enero">Enero</option>
                    <option value="Febrero">Febrero</option>
                    <option value="Marzo">Marzo</option>
                    <option value="Abril">Abril</option>
                    <option value="Mayo">Mayo</option>
                    <option value="Junio">Junio</option>
                    <option value="Julio">Julio</option>
                    <option value="Agosto">Agosto</option>
                    <option value="Septiembre">Septiembre</option>
                    <option value="Octubre">Octubre</option>
                    <option value="Noviembre">Noviembre</option>
                    <option value="Diciembre">Diciembre</option>
                </select>
                <label>Año:</label>
                <input type="number" name="anio" value="2026" required>
                <label>Monto a Cobrar (S/):</label>
                <input type="number" step="0.01" name="monto" value="10.00" required>
                <label>Fecha de Corte:</label>
                <input type="date" name="fecha_corte" required>
                <button type="submit">✅ Generar Mes para Todos</button>
            </form>
        </div>
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js');
            }
        </script>
    </body>
    </html>
    """

@app.route('/borrar_mes', methods=['GET', 'POST'])
def borrar_mes():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        mes = request.form['mes']
        anio = request.form['anio']
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM facturas WHERE mes = %s AND anio = %s", (mes, anio))
        eliminados = cursor.rowcount
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('admin', mensaje=f'🗑️ Se eliminaron {eliminados} facturas del mes de {mes} {anio}.'))
    
    return """
    <html>
    <head>
        <title>Borrar Mes</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }
            .contenedor { max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #dc3545; margin-top: 0; }
            label { font-size: 13px; color: #555; font-weight: bold; }
            input, select { width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
            button { background: linear-gradient(135deg, #dc3545, #a71d2a); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
            .volver { display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }
            .alerta { background-color: #f8d7da; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 15px; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/admin" class="volver">← Volver a la lista</a>
            <h1>🗑️ Borrar Mes</h1>
            <div class="alerta">⚠️ Esta acción elimina TODAS las facturas de un mes específico. No se puede deshacer.</div>
            <form method="POST" onsubmit="return confirm('¿Estás seguro?')">
                <label>Mes:</label>
                <select name="mes">
                    <option value="Enero">Enero</option>
                    <option value="Febrero">Febrero</option>
                    <option value="Marzo">Marzo</option>
                    <option value="Abril">Abril</option>
                    <option value="Mayo">Mayo</option>
                    <option value="Junio">Junio</option>
                    <option value="Julio">Julio</option>
                    <option value="Agosto">Agosto</option>
                    <option value="Septiembre">Septiembre</option>
                    <option value="Octubre">Octubre</option>
                    <option value="Noviembre">Noviembre</option>
                    <option value="Diciembre">Diciembre</option>
                </select>
                <label>Año:</label>
                <input type="number" name="anio" value="2026" required>
                <button type="submit">🗑️ Borrar Mes para Todos</button>
            </form>
        </div>
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js');
            }
        </script>
    </body>
    </html>
    """

@app.route('/cliente')
def cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT c.id_cliente, c.nombre_completo, c.apellidos, c.dni, c.direccion, c.correo, c.celular, c.calle, c.mz, c.lote, 
               c.fecha_pago, c.fecha_corte, c.monto_pagar, c.mes, c.estado, c.fecha_nacimiento 
        FROM clientes c
        INNER JOIN usuarios u ON c.id_cliente = u.id_cliente
        WHERE u.nombre_usuario = %s
    """, (session['usuario'],))
    c = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if not c:
        return "No se encontraron datos."
    
    estado = c[14] if c[14] else "Puntual"
    color = ""
    if estado == "Puntual":
        color = "#d4edda"
    elif estado == "Pendiente":
        color = "#fff3cd"
    elif estado == "Deudor" or estado == "Corte":
        color = "#f8d7da"
    elif estado == "Justificado":
        color = "#d1ecf1"
    
    edad = calcular_edad(c[15])
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT mes, anio, monto, fecha_pago, fecha_corte, estado 
        FROM facturas WHERE id_cliente = %s ORDER BY anio, id_factura
    """, (c[0],))
    facturas = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    historial = ""
    total_deuda = 0
    for f in facturas:
        if f[5] == "Puntual":
            color_f = "verde"
        elif f[5] == "Pendiente":
            color_f = "amarillo"
            total_deuda += f[2] if f[2] else 0
        elif f[5] == "Deudor" or f[5] == "Corte":
            color_f = "rojo"
            total_deuda += f[2] if f[2] else 0
        elif f[5] == "Justificado":
            color_f = "azul"
        else:
            color_f = ""
        
        historial += f"""
            <tr>
                <td>{f[0]} {f[1]}</td>
                <td>S/ {f[2] or ''}</td>
                <td>{str(f[3])[:10] if f[3] else 'Sin pagar'}</td>
                <td>{str(f[4])[:10] if f[4] else ''}</td>
                <td class="{color_f}">{f[5] or ''}</td>
            </tr>
        """
    
    return f"""
    <html>
    <head>
        <title>Mi Recibo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 15px; background-color: #f0f2f5; margin: 0; }}
            .contenedor {{ max-width: 100%; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #0066cc; text-align: center; font-size: 22px; }}
            h2 {{ color: #0066cc; font-size: 18px; margin-top: 25px; }}
            .estado {{ padding: 15px; border-radius: 10px; text-align: center; font-size: 16px; font-weight: bold; margin: 20px 0; background-color: {color}; }}
            .dato {{ margin: 8px 0; font-size: 14px; }}
            .dato strong {{ color: #0066cc; }}
            .logout {{ text-align: right; margin-bottom: 15px; }}
            .logout a {{ color: #dc3545; text-decoration: none; font-weight: bold; }}
            .btn-pdf {{ display: block; background: linear-gradient(135deg, #6f42c1, #4b2a89); color: white; padding: 15px; text-align: center; text-decoration: none; border-radius: 8px; font-size: 15px; font-weight: bold; margin: 20px 0; box-shadow: 0 4px 10px rgba(111,66,193,0.3); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; table-layout: fixed; }}
            th, td {{ padding: 6px; text-align: center; border-bottom: 1px solid #eee; word-wrap: break-word; }}
            th {{ background-color: #0066cc; color: white; font-size: 11px; }}
            .verde {{ background-color: #d4edda; color: #155724; font-weight: bold; }}
            .amarillo {{ background-color: #fff3cd; color: #856404; font-weight: bold; }}
            .rojo {{ background-color: #f8d7da; color: #721c24; font-weight: bold; }}
            .azul {{ background-color: #d1ecf1; color: #0c5460; font-weight: bold; }}
            .total {{ background-color: #f8d7da; padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; font-size: 16px; font-weight: bold; color: #721c24; }}
            
            @media (max-width: 600px) {{
                table, thead, tbody, th, td, tr {{ display: block; }}
                thead tr {{ position: absolute; top: -9999px; left: -9999px; }}
                tr {{ border: 1px solid #ccc; margin-bottom: 10px; border-radius: 8px; padding: 5px; }}
                td {{ border: none; position: relative; padding-left: 50%; text-align: right; font-size: 13px; }}
                td:before {{ position: absolute; left: 6px; width: 45%; padding-right: 10px; white-space: nowrap; text-align: left; font-weight: bold; color: #0066cc; }}
                td:nth-of-type(1):before {{ content: "Mes:"; }}
                td:nth-of-type(2):before {{ content: "Monto:"; }}
                td:nth-of-type(3):before {{ content: "Fecha Pago:"; }}
                td:nth-of-type(4):before {{ content: "Fecha Corte:"; }}
                td:nth-of-type(5):before {{ content: "Estado:"; }}
            }}
        </style>
    </head>
    <body>
        <div class="contenedor">
            <div class="logout"><a href="/logout">Cerrar sesión</a></div>
            <h1>💧 Mi Recibo</h1>
            <div class="estado">Estado actual: {estado}</div>
            <div class="dato"><strong>Nombre:</strong> {c[1]} {c[2] or ''}</div>
            <div class="dato"><strong>DNI:</strong> {c[3] or ''}</div>
            <div class="dato"><strong>Edad:</strong> {edad}</div>
            <div class="dato"><strong>Dirección:</strong> {c[4] or ''}</div>
            <div class="dato"><strong>Calle:</strong> {c[7] or ''}</div>
            <div class="dato"><strong>Mz:</strong> {c[8] or ''}</div>
            <div class="dato"><strong>Lote:</strong> {c[9] or ''}</div>
            <div class="dato"><strong>Celular:</strong> {c[6] or ''}</div>
            
            <a href="/pdf_cliente" class="btn-pdf">📄 Descargar mi Recibo en PDF</a>
            
            <h2>📋 Historial de Meses</h2>
            <table>
                <tr>
                    <th>Mes</th>
                    <th>Monto</th>
                    <th>Fecha Pago</th>
                    <th>Fecha Corte</th>
                    <th>Estado</th>
                </tr>
                {historial}
            </table>
            
            <div class="total">Deuda Total: S/ {total_deuda:.2f}</div>
        </div>
        <script>
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/service-worker.js');
            }}
        </script>
    </body>
    </html>
    """

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre_completo, apellidos, dni, direccion, correo, celular, calle, mz, lote, fecha_pago, fecha_corte, monto_pagar, mes, estado, fecha_nacimiento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['nombre_completo'],
            request.form['apellidos'],
            request.form['dni'],
            request.form['direccion'],
            request.form['correo'],
            request.form['celular'],
            request.form['calle'],
            request.form['mz'],
            request.form['lote'],
            request.form['fecha_pago'] or None,
            request.form['fecha_corte'] or None,
            request.form['monto_pagar'] or None,
            request.form['mes'],
            request.form['estado'],
            request.form['fecha_nacimiento'] or None
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('admin'))
    
    return """
    <html>
    <head>
        <title>Agregar Cliente</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }
            .contenedor { max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #0066cc; margin-top: 0; }
            label { font-size: 13px; color: #555; font-weight: bold; }
            input, select { width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
            button { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }
            .volver { display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/admin" class="volver">← Volver a la lista</a>
            <h1>➕ Agregar Cliente</h1>
            <form method="POST">
                <label>Nombres:</label>
                <input type="text" name="nombre_completo" required>
                <label>Apellidos:</label>
                <input type="text" name="apellidos">
                <label>DNI:</label>
                <input type="text" name="dni" maxlength="8">
                <label>Fecha de Nacimiento:</label>
                <input type="date" name="fecha_nacimiento">
                <label>Dirección:</label>
                <input type="text" name="direccion">
                <label>Correo:</label>
                <input type="email" name="correo">
                <label>Celular:</label>
                <input type="text" name="celular">
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
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js');
            }
        </script>
    </body>
    </html>
    """

@app.route('/editar/<int:id_cliente>', methods=['GET', 'POST'])
def editar(id_cliente):
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE clientes SET nombre_completo=%s, apellidos=%s, dni=%s, direccion=%s, correo=%s, celular=%s, 
            calle=%s, mz=%s, lote=%s, fecha_pago=%s, fecha_corte=%s, monto_pagar=%s, mes=%s, estado=%s, fecha_nacimiento=%s,
            reposicion=%s, inscripcion=%s, multa=%s
            WHERE id_cliente=%s
        """, (
            request.form['nombre_completo'],
            request.form['apellidos'],
            request.form['dni'],
            request.form['direccion'],
            request.form['correo'],
            request.form['celular'],
            request.form['calle'],
            request.form['mz'],
            request.form['lote'],
            request.form['fecha_pago'] or None,
            request.form['fecha_corte'] or None,
            request.form['monto_pagar'] or None,
            request.form['mes'],
            request.form['estado'],
            request.form['fecha_nacimiento'] or None,
            request.form.get('reposicion', ''),
            request.form.get('inscripcion', ''),
            request.form.get('multa', ''),
            id_cliente
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('admin'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_cliente, nombre_completo, apellidos, dni, direccion, correo, celular, calle, mz, lote, fecha_pago, fecha_corte, monto_pagar, mes, estado, fecha_nacimiento, reposicion, inscripcion, multa FROM clientes WHERE id_cliente = %s", (id_cliente,))
    c = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    fecha_pago = str(c[10])[:10] if c[10] else ''
    fecha_corte = str(c[11])[:10] if c[11] else ''
    fecha_nac = str(c[15])[:10] if c[15] else ''
    
    repo_check = 'checked' if c[16] else ''
    insc_check = 'checked' if c[17] else ''
    multa_check = 'checked' if c[18] else ''
    
    return f"""
    <html>
    <head>
        <title>Editar Cliente</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#0066cc">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f0f2f5; margin: 0; }}
            .contenedor {{ max-width: 500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #0066cc; margin-top: 0; }}
            label {{ font-size: 13px; color: #555; font-weight: bold; }}
            input, select {{ width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; }}
            button {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; }}
            .volver {{ display: inline-block; margin-bottom: 15px; color: #0066cc; text-decoration: none; font-weight: bold; }}
            .check-group {{ display: flex; gap: 15px; margin-bottom: 12px; }}
            .check-group label {{ font-size: 14px; display: flex; align-items: center; gap: 5px; }}
        </style>
    </head>
    <body>
        <div class="contenedor">
            <a href="/admin" class="volver">← Volver a la lista</a>
            <h1>✏️ Editar Cliente</h1>
            <form method="POST">
                <label>Nombres:</label>
                <input type="text" name="nombre_completo" value="{c[1] or ''}" required>
                <label>Apellidos:</label>
                <input type="text" name="apellidos" value="{c[2] or ''}">
                <label>DNI:</label>
                <input type="text" name="dni" value="{c[3] or ''}" maxlength="8">
                <label>Fecha de Nacimiento:</label>
                <input type="date" name="fecha_nacimiento" value="{fecha_nac}">
                <label>Dirección:</label>
                <input type="text" name="direccion" value="{c[4] or ''}">
                <label>Correo:</label>
                <input type="email" name="correo" value="{c[5] or ''}">
                <label>Celular:</label>
                <input type="text" name="celular" value="{c[6] or ''}">
                <label>Calle:</label>
                <input type="text" name="calle" value="{c[7] or ''}">
                <label>Mz:</label>
                <input type="text" name="mz" value="{c[8] or ''}">
                <label>Lote:</label>
                <input type="text" name="lote" value="{c[9] or ''}">
                <label>Fecha de Pago:</label>
                <input type="date" name="fecha_pago" value="{fecha_pago}">
                <label>Fecha de Corte:</label>
                <input type="date" name="fecha_corte" value="{fecha_corte}">
                <label>Monto a Pagar:</label>
                <input type="number" step="0.01" name="monto_pagar" value="{c[12] or ''}">
                <label>Mes:</label>
                <input type="text" name="mes" value="{c[13] or ''}">
                <label>Estado:</label>
                <select name="estado">
                    <option value="Puntual" {'selected' if c[14] == 'Puntual' else ''}>Puntual</option>
                    <option value="Pendiente" {'selected' if c[14] == 'Pendiente' else ''}>Pendiente</option>
                    <option value="Deudor" {'selected' if c[14] == 'Deudor' else ''}>Deudor</option>
                    <option value="Justificado" {'selected' if c[14] == 'Justificado' else ''}>Justificado</option>
                </select>
                
                <label>Conceptos adicionales:</label>
                <div class="check-group">
                    <label><input type="checkbox" name="reposicion" value="X" {repo_check}> Reposición</label>
                    <label><input type="checkbox" name="inscripcion" value="X" {insc_check}> Inscripción</label>
                    <label><input type="checkbox" name="multa" value="X" {multa_check}> Multa</label>
                </div>
                
                <button type="submit">💾 Guardar Cambios</button>
            </form>
        </div>
        <script>
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/service-worker.js');
            }}
        </script>
    </body>
    </html>
    """

@app.route('/eliminar/<int:id_cliente>')
def eliminar(id_cliente):
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
