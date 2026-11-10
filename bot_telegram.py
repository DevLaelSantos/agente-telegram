import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from agentmold import Agent, tool
import datetime
from zoneinfo import ZoneInfo

# --- 1. CARREGAR AS VARIÁVEIS DO .ENV ---
load_dotenv()
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

# --- 2. FERRAMENTAS (O que o seu agente sabe fazer) ---
@tool
def get_current_time(city: str = "São Paulo") -> str:
    """Get the current time for a given city."""
    try:
        tz_map = {"são paulo": "America/Sao_Paulo", "londres": "Europe/London", "tóquio": "Asia/Tokyo"}
        tz_name = tz_map.get(city.lower(), "America/Sao_Paulo")
        now = datetime.datetime.now(ZoneInfo(tz_name))
        return f"A hora em {city} é {now.strftime('%H:%M:%S')}."
    except Exception as e: return f"Erro: {e}"

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    try: return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e: return f"Erro: {e}"

# --- 3. CRIAR O AGENTE (Supervisor e Especialista) ---
llm_config = {"provider": "openai", "model": "openai/gpt-oss-20b"}
agente_financeiro = Agent(name="Financeiro", instructions="Faça cálculos e horas.", tools=[calculate, get_current_time], llm=llm_config)

@tool
def chamar_financeiro(pergunta: str) -> str:
    """Chame para cálculos e horas."""
    return agente_financeiro.run(pergunta)

# --- 3. CRIAR O AGENTE (Simplificado) ---
llm_config = {"provider": "openai", "model": "openai/gpt-oss-120b"}

# Em vez de criar um especialista e um supervisor, damos as ferramentas direto para o agente principal.
supervisor = Agent(
    name="Assistente",
    instructions=(
        "Você é um assistente útil. "
        "SEMPRE que o usuário perguntar sobre horas ou fusos horários, "
        "você DEVE usar a ferramenta 'get_current_time'. "
        "SEMPRE que o usuário pedir um cálculo, use a ferramenta 'calculate'. "
        "NUNCA tente adivinhar a hora. Não use markdown (**)."
    ),
    tools=[calculate], # Ferramentas diretas
    llm=llm_config,
)

# --- 4. CÓDIGO DO TELEGRAM ---
# Pega o Token do .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Token do Telegram não encontrado no arquivo .env!")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🤖 Olá! Eu sou o seu assistente de IA. Como posso ajudar?")

@dp.message()
async def handle_message(message: types.Message):
    # Mostra "digitando..." no chat
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Chama o Supervisor
        resposta = supervisor.run(message.text)
        # Limpa os asteriscos e envia
        await message.answer(resposta.replace("**", ""))
    except Exception as e:
        await message.answer(f"❌ Ocorreu um erro: {e}")

async def main():
    print("🤖 Bot do Telegram rodando... (Aperte Ctrl+C para parar)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())