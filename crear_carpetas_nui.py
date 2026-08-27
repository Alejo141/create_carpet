import streamlit as st
import pandas as pd
import os
import subprocess
from pathlib import Path

st.set_page_config(page_title="Creador de Carpetas", page_icon="📁", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.header-box {
    background: linear-gradient(135deg, #1B4F8A 0%, #2E7DD1 100%);
    border-radius: 12px; padding: 28px 32px 22px;
    margin-bottom: 28px; color: white;
}
.header-box h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.header-box p  { margin: 6px 0 0; opacity: 0.85; font-size: 0.95rem; }

.step-label {
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #2E7DD1; margin-bottom: 6px;
}
.tip-box {
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 8px; padding: 12px 16px;
    font-size: 0.85rem; color: #1E40AF; margin: 8px 0;
}
.ruta-box {
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-radius: 8px; padding: 12px 16px;
    font-size: 0.85rem; color: #166534;
    font-family: monospace; margin: 8px 0;
    word-break: break-all;
}
.stat-row { display: flex; gap: 16px; margin-top: 12px; }
.stat {
    flex: 1; text-align: center;
    background: #F0F7FF; border-radius: 8px; padding: 14px 8px;
}
.stat .num { font-size: 2rem; font-weight: 700; }
.stat .lbl { font-size: 0.8rem; color: #64748B; margin-top: 2px; }
.stat.ok   .num { color: #16A34A; }
.stat.skip .num { color: #D97706; }
.stat.err  .num { color: #DC2626; }
.log-area {
    background: #0F172A; color: #94A3B8;
    border-radius: 8px; padding: 14px 16px;
    font-family: monospace; font-size: 0.8rem;
    max-height: 260px; overflow-y: auto; margin-top: 16px;
}
.log-area .ok   { color: #4ADE80; }
.log-area .skip { color: #FCD34D; }
.log-area .err  { color: #F87171; }
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #1B4F8A, #2E7DD1);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; padding: 10px 0; width: 100%;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
    <h1>📁 Creador Masivo de Carpetas</h1>
    <p>Selecciona una carpeta, carga tu Excel y crea todas las subcarpetas en un clic.</p>
</div>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def abrir_selector_carpeta():
    """Abre selector nativo de carpetas (Mac/Windows/Linux)."""
    import platform
    sistema = platform.system()
    try:
        if sistema == "Darwin":  # Mac
            script = (
                'tell application "System Events" to set f to '
                'choose folder with prompt "Selecciona la carpeta destino"\n'
                'return POSIX path of f'
            )
            r = subprocess.run(["osascript", "-e", script],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return r.stdout.strip().rstrip("/")
        elif sistema == "Windows":
            script = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                '$f = New-Object System.Windows.Forms.FolderBrowserDialog;'
                '$f.Description = "Selecciona la carpeta destino";'
                'if ($f.ShowDialog() -eq "OK") { $f.SelectedPath }'
            )
            r = subprocess.run(["powershell", "-Command", script],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return r.stdout.strip()
        else:  # Linux
            r = subprocess.run(
                ["zenity", "--file-selection", "--directory",
                 "--title=Selecciona la carpeta destino"],
                capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return r.stdout.strip()
    except Exception:
        pass
    return None

# ── PASO 1: Seleccionar carpeta ───────────────────────────────────────────────
st.markdown('<div class="step-label">Paso 1 — Carpeta destino</div>', unsafe_allow_html=True)

# Inicializar estado
if "ruta_destino" not in st.session_state:
    st.session_state.ruta_destino = ""

col1, col2 = st.columns([2, 1])
with col1:
    ruta_texto = st.text_input(
        "Ruta de la carpeta",
        value=st.session_state.ruta_destino,
        placeholder="/Users/usuario/OneDrive/MiCarpeta",
        label_visibility="collapsed"
    )
    if ruta_texto != st.session_state.ruta_destino:
        st.session_state.ruta_destino = ruta_texto

with col2:
    if st.button("📂 Explorar..."):
        ruta = abrir_selector_carpeta()
        if ruta:
            st.session_state.ruta_destino = ruta
            st.rerun()
        else:
            st.warning("No se seleccionó ninguna carpeta.")

# Validar ruta
ruta_valida = False
ruta_final = None

if st.session_state.ruta_destino:
    ruta_str = st.session_state.ruta_destino.strip()
    try:
        existe = os.path.isdir(ruta_str)
    except Exception:
        existe = False

    if existe:
        try:
            n_items = len(os.listdir(ruta_str))
        except Exception:
            n_items = 0
        st.markdown(f'<div class="ruta-box">📍 {ruta_str}<br><small>{n_items} elemento(s) dentro</small></div>',
                    unsafe_allow_html=True)
        ruta_final = ruta_str
        ruta_valida = True
    else:
        st.error("❌ La ruta no existe o no es accesible.")
        st.markdown("""
        <div class="tip-box">
        💡 <b>En Mac:</b> Abre Finder → navega a la carpeta → clic derecho → 
        <b>Obtener información</b> → copia la ruta. O en Terminal: <code>echo $HOME</code>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── PASO 2: Cargar Excel ──────────────────────────────────────────────────────
st.markdown('<div class="step-label">Paso 2 — Excel con los nombres de carpetas</div>', unsafe_allow_html=True)

archivo = st.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx", "xls"])

nuis = None

if archivo:
    try:
        df_raw = pd.read_excel(archivo)
        if df_raw.empty:
            st.error("El archivo está vacío.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                columna = st.selectbox("Columna con los nombres", options=list(df_raw.columns))
            with col2:
                fila_inicio = st.number_input("Fila de inicio", min_value=1, value=1)

            valores_raw = df_raw[columna].dropna().iloc[fila_inicio - 1:]
            lista = []
            for v in valores_raw:
                try:
                    s = str(int(float(str(v)))).strip()
                except Exception:
                    s = str(v).strip()
                if s and s.lower() not in ("nan", "none", ""):
                    lista.append(s)

            unicos = list(dict.fromkeys(lista))
            duplicados = len(lista) - len(unicos)

            st.info(f"**{len(unicos)}** nombres únicos encontrados" +
                    (f" · {duplicados} duplicados omitidos" if duplicados else ""))

            preview = "  |  ".join(unicos[:8])
            if len(unicos) > 8:
                preview += f"  ...  +{len(unicos) - 8} más"
            st.code(preview, language=None)
            nuis = unicos

    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")

st.markdown("---")

# ── PASO 3: Formato del nombre ────────────────────────────────────────────────
st.markdown('<div class="step-label">Paso 3 — Formato del nombre (opcional)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    prefijo = st.text_input("Prefijo", placeholder="ej: NUI_", value="")
with col2:
    sufijo = st.text_input("Sufijo", placeholder="ej: _2024", value="")

if nuis and (prefijo or sufijo):
    st.info(f"Ejemplo: **{prefijo}{nuis[0]}{sufijo}**")

st.markdown("---")

# ── PASO 4: Crear carpetas ────────────────────────────────────────────────────
st.markdown('<div class="step-label">Paso 4 — Crear carpetas</div>', unsafe_allow_html=True)

modo = st.radio("Si la carpeta ya existe:",
                ["Omitir", "Reportar como error"], horizontal=True)

listo = ruta_valida and nuis is not None and len(nuis) > 0

if not listo:
    st.warning("Completa los pasos 1 y 2 para continuar.")

if listo:
    if st.button(f"🚀 Crear {len(nuis)} carpetas"):
        resultados = {"ok": 0, "omitidas": 0, "errores": 0}
        log_lines = []
        barra = st.progress(0)
        estado = st.empty()
        log_box = st.empty()
        total = len(nuis)

        for i, nombre_base in enumerate(nuis):
            nombre = f"{prefijo}{nombre_base}{sufijo}"
            ruta_carpeta = os.path.join(ruta_final, nombre)

            try:
                if os.path.isdir(ruta_carpeta):
                    if modo == "Reportar como error":
                        resultados["errores"] += 1
                        log_lines.append(f'<span class="err">✗ Ya existe: {nombre}</span>')
                    else:
                        resultados["omitidas"] += 1
                        log_lines.append(f'<span class="skip">⚠ Omitida:  {nombre}</span>')
                else:
                    os.makedirs(ruta_carpeta)
                    resultados["ok"] += 1
                    log_lines.append(f'<span class="ok">✔ Creada:   {nombre}</span>')
            except Exception as e:
                resultados["errores"] += 1
                log_lines.append(f'<span class="err">✗ Error en {nombre}: {e}</span>')

            barra.progress((i + 1) / total)
            estado.markdown(f"Procesando **{i + 1}** de **{total}**...")

            if (i + 1) % 5 == 0 or (i + 1) == total:
                log_box.markdown(
                    f'<div class="log-area">{"<br>".join(log_lines[-40:])}</div>',
                    unsafe_allow_html=True)

        estado.empty()
        barra.empty()

        st.markdown(f"""
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:20px 24px;margin-top:16px;">
            <b>✅ Proceso completado</b>
            <div class="stat-row">
                <div class="stat ok"><div class="num">{resultados['ok']}</div><div class="lbl">Creadas</div></div>
                <div class="stat skip"><div class="num">{resultados['omitidas']}</div><div class="lbl">Omitidas</div></div>
                <div class="stat err"><div class="num">{resultados['errores']}</div><div class="lbl">Errores</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if resultados["ok"] > 0:
            st.balloons()
