import os
import time
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

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
        response = llm.invoke([HumanMessage(content='Memoria del chat:' + Memo + 'Condiciones:' + Meta_prompt + 'Usuario:' + user_input)])
        # print('Memoria del chat:' + Memo + 'Condiciones' + Meta_prompt + 'Usuario' + user_input)
        try:
            # Si es un AIMessage (objeto de mensaje)
            print(f"🤖 Bot: {response.content.strip()}\n")
            Memo = Memo + 'Usuario:' + user_input + '\n' + 'Bot:' + response.content.strip()
            time.sleep(2)
            if len(Memo) > 1500:
                resumen_prompt = f"Resume esta conversación de forma breve, conserva los puntos importantes:\n{Memo}"
                resumen = llm.invoke([HumanMessage(content=resumen_prompt)])
                Memo = resumen.content.strip()  # Guarda solo el resumen
                print("🧠 (Resumen actualizado)\n")
                print(resumen_prompt)
        except AttributeError:
            # Si es un dict o lista de mensajes (caso nuevo en langchain_openai)
            if isinstance(response, dict) and "content" in response:
                print(f"🤖 Bot: {response['content'].strip()}\n")
            elif isinstance(response, list) and len(response) > 0:
                print(f"🤖 Bot: {response[0].content.strip()}\n")
            else:
                print(f"🤖 Bot: {response}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
