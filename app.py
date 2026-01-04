from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Función para conectarme a la base de datos


def get_db():
    conn = sqlite3.connect("tienda.db")
    conn.row_factory = sqlite3.Row
    return conn

# Inicio las tablas


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        saldo_total REAL DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        fecha TEXT,
        concepto TEXT,
        monto REAL,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def lista_clientes():
    conn = get_db()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    conn.close()
    return render_template("clientes.html", clientes=clientes)


@app.route("/cliente/<int:cliente_id>")
def historial(cliente_id):
    conn = get_db()
    cliente = conn.execute(
        "SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
    movimientos = conn.execute(
        "SELECT * FROM movimientos WHERE cliente_id=? ORDER BY fecha DESC", (cliente_id,)).fetchall()
    conn.close()
    return render_template("historial.html", cliente=cliente, movimientos=movimientos)


@app.route("/nuevo/<int:cliente_id>", methods=["GET", "POST"])
def nuevo_movimiento(cliente_id):
    if request.method == "POST":
        fecha = request.form["fecha"]
        concepto = request.form["concepto"]
        monto = float(request.form["monto"])
        conn = get_db()
        conn.execute("INSERT INTO movimientos (cliente_id, fecha, concepto, monto) VALUES (?, ?, ?, ?)",
                     (cliente_id, fecha, concepto, monto))
        conn.execute(
            "UPDATE clientes SET saldo_total = saldo_total + ? WHERE id=?", (monto, cliente_id))
        conn.commit()
        conn.close()
        return redirect(url_for("historial", cliente_id=cliente_id))
    return render_template("nuevo.html", cliente_id=cliente_id)


@app.route("/agregar_cliente", methods=["POST"])
def agregar_cliente():
    nombre = request.form["nombre"]
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO clientes (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()
    return redirect(url_for("lista_clientes"))


@app.route("/eliminar/<int:cliente_id>", methods=["POST"])
def eliminar_cliente(cliente_id):
    conn = get_db()
    conn.execute("DELETE FROM movimientos WHERE cliente_id=?", (cliente_id,))
    conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("lista_clientes"))


@app.route("/buscar", methods=["POST"])
def buscar_cliente():
    nombre = request.form["nombre"]
    conn = get_db()
    clientes = conn.execute(
        "SELECT id, nombre, (SELECT SUM(monto) FROM movimientos WHERE cliente_id=c.id) AS saldo_total FROM clientes c WHERE nombre LIKE ?",
        ('%' + nombre + '%',)
    ).fetchall()
    conn.close()
    return render_template("clientes.html", clientes=clientes)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
