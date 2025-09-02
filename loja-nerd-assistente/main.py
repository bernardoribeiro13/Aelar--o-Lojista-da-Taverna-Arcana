import json
import os
from typing import List, Dict

from dotenv import load_dotenv
import google.generativeai as genai

from persona import PERSONA

def carregar_chave_api():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não encontrada. Defina no arquivo .env")
    genai.configure(api_key=api_key)

def carregar_catalogo(caminho: str = "catalogo_loja.json") -> List[Dict]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_completo = os.path.join(base_dir, caminho)
    with open(caminho_completo, "r", encoding="utf-8") as f:
        return json.load(f)

def formatar_catalogo_para_contexto(catalogo: List[Dict]) -> str:
    linhas = []
    for item in catalogo:
        linhas.append(
            f"- {item['nome']} (SKU: {item['sku']}) | R$ {item['preco']:.2f}\n"
            f"  Categoria: {item.get('categoria','N/A')}\n"
            f"  Tags: {', '.join(item.get('tags', []))}\n"
            f"  Desc: {item.get('descricao','')}\n"
        )
    return "\n".join(linhas)

def criar_modelo(model_name: str = "gemini-1.5-flash"):
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=PERSONA,
    )

def gerar_resposta(chat, mensagem_usuario: str, contexto_catalogo: str) -> str:
    """Envia a mensagem ao chat, incluindo o catálogo como contexto."""
    prompt = f"""
Você é Aelar, o lojista da Taverna Arcana.

Catálogo atual (use para as recomendações e preços, quando fizer sentido):

{contexto_catalogo}

Pergunta do cliente:
{mensagem_usuario}

📜 FORMATAÇÃO OBRIGATÓRIA DA RESPOSTA:
1. Uma breve saudação no início (em tom medieval/RPG).
2. Listar recomendações usando este formato:
   ---
   🪄 **Nome do Item**  
   [descrição do item]  
   💰 Preço: R$ XX,XX  
   ---
3. Se listar vários itens, separar cada um com uma linha `---`.
4. No fim, trazer uma sugestão clara de próximo passo (ex: “quer que prepare um kit para iniciantes?”).

Não invente preços: use apenas os do catálogo.
"""
    resp = chat.send_message(prompt)
    return resp.text.strip() if hasattr(resp, "text") and resp.text else "(sem resposta)"


def loop_chat():
    carregar_chave_api()
    catalogo = carregar_catalogo()
    contexto = formatar_catalogo_para_contexto(catalogo)

    modelo = criar_modelo()
    chat = modelo.start_chat(history=[])

    print("🧙 Aelar (Taverna Arcana): Saudações, aventureiro! Em que posso auxiliar?")
    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            user = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté a próxima jornada!")
            break

        if not user:
            continue
        if user.lower() in {"sair", "exit", "quit"}:
            print("🧙 Aelar: Que os dados rolem a seu favor. Até breve!")
            break

        try:
            resposta = gerar_resposta(chat, user, contexto)
            print(f"\n🧙 Aelar: {resposta}\n")
        except Exception as e:
            print(f"\n[Erro do oráculo] {e}\n")

if __name__ == "__main__":
    loop_chat()
