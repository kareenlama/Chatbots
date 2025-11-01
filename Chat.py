import os
import time
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

warnings.filterwarnings("ignore")

# 🔐 Cargar variables desde el archivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ No se encontró OPENAI_API_KEY en el archivo .env")

# 🤖 Configuración del modelo OpenRouter
llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.environ["OPENAI_API_KEY"],
    model_name="mistralai/mistral-7b-instruct",
    temperature=0.7,
)


def resumir_memoria(conversacion, max_palabras=100):
    """Genera un resumen extrayendo las últimas interacciones clave"""
    lineas = conversacion.strip().split("\n")

    # Mantener solo las últimas 6 líneas (3 turnos de conversación)
    ultimas_lineas = lineas[-6:] if len(lineas) > 6 else lineas

    # Extraer puntos clave (eliminar redundancias)
    puntos_clave = []
    for linea in ultimas_lineas:
        if "Usuario:" in linea or "Bot:" in linea:
            # Acortar respuestas largas
            contenido = linea.split(":", 1)[1].strip()
            palabras = contenido.split()
            if len(palabras) > 20:
                contenido = " ".join(palabras[:20]) + "..."
            puntos_clave.append(linea.split(":")[0] + ": " + contenido)

    return "\n".join(puntos_clave)


# 🗨️ Bucle de chat básico
print("💬 Chatbot Mistral vía OpenRouter (escribe 'salir' para terminar)\n")

Meta_prompt = "Eres un veterinario especializado en nutrición canina natural. Responde mi pregunta con este rol. Pregunta:"
Memo = ""

while True:
    user_input = input("👤 Tú: ")
    if user_input.lower() in ["salir", "exit", "quit"]:
        print("👋 Hasta luego.")
        break

    try:
        # Enviar mensaje con contexto
        mensaje_completo = (
            f"Memoria del chat: {Memo}Condiciones: {Meta_prompt}Usuario: {user_input}"
        )
        response = llm.invoke([HumanMessage(content=mensaje_completo)])

        # print('Memoria del chat:' + Memo + 'Condiciones:' + Meta_prompt + 'Usuario:' + user_input)
        try:
            # Si es un AIMessage (objeto de mensaje)
            print(f"🤖 Bot: {response.content.strip()}\n")
            bot_response = response.content.strip()
            Memo = Memo + "Usuario:" + user_input + "\n" + "Bot:" + bot_response + "\n"
            time.sleep(2)
            # Resumir memoria si es muy larga (1500 caracteres)
            if len(Memo) > 1500:
                print("🧠 Resumiendo memoria...\n")
                Memo = resumir_memoria(Memo)

        except AttributeError:
            # Si es un dict o lista de mensajes (caso nuevo en langchain_openai)
            if isinstance(response, dict) and "content" in response:
                print(f"🤖 Bot: {response['content'].strip()}\n")
                bot_response = response["content"].strip()
            elif isinstance(response, list) and len(response) > 0:
                print(f"🤖 Bot: {response[0].content.strip()}\n")
                bot_response = response[0].content.strip()
            else:
                print(f"🤖 Bot: {response}\n")
                bot_response = str(response)

            Memo = Memo + "Usuario:" + user_input + "\n" + "Bot:" + bot_response + "\n"

            # Resumir memoria si es muy larga
            if len(Memo) > 1500:
                print("🧠 Resumiendo memoria...\n")
                Memo = resumir_memoria(Memo)

    except Exception as e:
        print(f"❌ Error: {e}\n")
