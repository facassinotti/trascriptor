import streamlit as st
import requests
import time
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Transcriptor Pro", page_icon="🎙️", layout="wide")

st.title("🎙️ Transcriptor Inteligente con Historial")

# 🔑 TU CLAVE API (Reemplázala por la tuya de AssemblyAI)
API_KEY = "TU_API_KEY_AQUI"

headers = {
    "authorization": API_KEY,
    "content-type": "application/json"
}

# --- MEMORIA DE LA APP (HISTORIAL) ---
if "historial" not in st.session_state:
    st.session_state.historial = []

# --- FUNCIÓN DE TRANSCRIPCIÓN ---
def transcribir_audio(audio_bytes):
    upload_url = "https://api.assemblyai.com/v2/upload"
    upload_response = requests.post(upload_url, headers=headers, data=audio_bytes)
    
    if upload_response.status_code != 200:
        st.error("Error al subir el audio. Verifica tu API Key.")
        return None
        
    audio_url = upload_response.json()["upload_url"]

    transcript_url = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "language_code": "es"
    }
    
    transcript_response = requests.post(transcript_url, json=json_data, headers=headers)
    transcript_id = transcript_response.json()["id"]
    
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    
    # Marcador de tiempo de procesamiento
    inicio_procesamiento = time.time()
    placeholder_tiempo = st.empty()
    
    with st.spinner("Analizando voces y transcribiendo..."):
        while True:
            # Calcular tiempo transcurrido procesando
            tiempo_actual = time.time() - inicio_procesamiento
            placeholder_tiempo.info(f"⏳ Tiempo de procesamiento: {int(tiempo_actual)} segundos")
            
            polling_response = requests.get(polling_url, headers=headers)
            status = polling_response.json()["status"]
            
            if status == "completed":
                placeholder_tiempo.empty()
                return polling_response.json()
            elif status == "failed":
                placeholder_tiempo.empty()
                st.error("La transcripción falló.")
                return None
            time.sleep(2)

# --- INTERFAZ GRÁFICA (Diseño en columnas) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🎛️ Panel de Grabación / Subida")
    
    archivo_subido = st.file_uploader("Subir un archivo de audio (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])
    
    st.write("---")
    st.write("**Grabar directamente:**")
    audio_grabado = st.audio_input("Presiona el micrófono para hablar")

    # Determinar qué audio usar
    audio_final = None
    nombre_audio = ""
    
    if archivo_subido is not None:
        audio_final = archivo_subido.read()
        nombre_audio = archivo_subido.name
    elif audio_grabado is not None:
        audio_final = audio_grabado.read()
        nombre_audio = f"Grabación_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    if audio_final is not None:
        st.audio(audio_final, format="audio/wav")
        
        if st.button("🚀 Iniciar Transcripción"):
            if API_KEY == "TU_API_KEY_AQUI":
                st.warning("Introduce tu API Key en el código para continuar.")
            else:
                resultado = transcribir_audio(audio_final)
                
                if resultado:
                    # Formatear el texto con los interlocutores
                    texto_formateado = ""
                    for utterance in resultado["utterances"]:
                        texto_formateado += f"Persona {utterance['speaker']}: {utterance['text']}\n\n"
                    
                    # GUARDAR EN EL HISTORIAL (Audio y Texto)
                    guardar_registro = {
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "nombre": nombre_audio,
                        "audio": audio_final,
                        "texto": texto_formateado
                    }
                    # Insertar al principio para ver lo más reciente primero
                    st.session_state.historial.insert(0, guardar_registro)
                    st.success("¡Transcripción completada y guardada en el historial!")

with col2:
    st.header("🗂️ Historial de Guardados")
    
    if not st.session_state.historial:
        st.info("Aún no tienes transcripciones guardadas en esta sesión.")
    else:
        for i, item in enumerate(st.session_state.historial):
            # Tarjeta visual para cada grabación guardada
            with st.expander(f"📁 {item['fecha']} - {item['nombre']}", expanded=(i == 0)):
                st.write("**Audio guardado:**")
                st.audio(item['audio'], format="audio/wav")
                
                st.write("**Transcripción:**")
                st.write(item['texto'])
                
                # Botón de descarga para el texto específico
                st.download_button(
                    label="📥 Descargar Texto (.txt)",
                    data=item['texto'],
                    file_name=f"transcripcion_{i}.txt",
                    mime="text/plain",
                    key=f"btn_{i}"
                )