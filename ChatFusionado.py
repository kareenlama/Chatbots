# ======================================================================
# CHAT FUSIONADO: Copia literal de Chat.py + ConsultaBase.py
# ======================================================================

import os
import json
import time
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import DeepLake

warnings.filterwarnings("ignore")


# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
def load_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
def chat_with_context(cfg: dict):
    # === Cargar .env para API Key (de ambos archivos) ===
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ No se encontró OPENAI_API_KEY en el archivo .env")

    # === Configuración del modelo (literal de Chat.py) ===
    llm = ChatOpenAI(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.environ["OPENAI_API_KEY"],
        model_name="mistralai/mistral-7b-instruct",
        temperature=0.7,
    )

    emb_cfg = cfg["embedding"]
    embeddings = HuggingFaceEmbeddings(
        model_name=emb_cfg["model_name"],
        model_kwargs={"device": emb_cfg.get("device", "cpu")},
        encode_kwargs={
            "normalize_embeddings": emb_cfg.get("normalize_embeddings", True)
        },
    )

    dl_cfg = cfg["deeplake"]
    dataset_path = os.path.expanduser(dl_cfg["dataset_path"])
    print(f"📂 Conectando a base Deep Lake: {dataset_path}")
    db = DeepLake(dataset_path=dataset_path, embedding=embeddings, read_only=True)

    k = int(cfg["retrieval"].get("k", 3))

    Meta_prompt = "Eres un experto literario y narrador mágico que conoce cada detalle de Cien años de soledad' de Gabriel García Márquez.Hablas con un tono poético y evocador, como si formaras parte del realismo mágico de Macondo. Tu tarea es responder preguntas, analizar personajes, símbolos, eventos y temas del libro con profundidad, belleza literaria y precisión textual. Responde mi pregunta con este rol. Pregunta:"

    Memo = ""

    print("💬 Chatbot Mistral vía OpenRouter (escribe 'salir' para terminar)\n")

    while True:
        user_input = input("👤 Tú: ")

        if user_input.lower() in ["salir", "exit", "quit"]:
            print("👋 Hasta luego.")
            break

        try:
            # --------------------------------------------------------------
            # AQUÍ SE FUSIONAN: Primero buscar en Deep Lake
            # --------------------------------------------------------------
            results = db.similarity_search(user_input, k=k)

            context_texts = []
            for i, doc in enumerate(results, start=1):
                meta = doc.metadata or {}
                page = meta.get("page", "")
                snippet = doc.page_content.strip().replace("\n", " ")
                context_texts.append(f"[{i}] (página {page}) {snippet[:500]}")

            contexto = "\n".join(context_texts)

            # --------------------------------------------------------------
            # Construir mensaje con memoria + contexto vectorial
            # --------------------------------------------------------------
            mensaje_completo = (
                f"Memoria del chat: {Memo}"
                f"Contexto del documento:\n{contexto}\n"
                f"Condiciones: {Meta_prompt}"
                f"Usuario: {user_input}"
            )

            response = llm.invoke([HumanMessage(content=mensaje_completo)])

            # === Manejo de respuesta (literal de Chat.py) ===
            try:
                # Si es un AIMessage (objeto de mensaje)
                print(f"🤖 Bot: {response.content.strip()}\n")
                print(f"mensaje completo:{mensaje_completo}")
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


# ----------------------------------------------------------------------
# BLOQUE PRINCIPAL
# ----------------------------------------------------------------------
if __name__ == "__main__":
    cfg = load_config("config.json")
    chat_with_context(cfg)