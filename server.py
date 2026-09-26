from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import asyncio
import edge_tts
from playsound import playsound
import os
import uuid
from openai import OpenAI

from config import API_BASE_URL, API_KEY, MODEL_NAME
from tools import TOOL_DEFINITIONS, TOOL_MAP

app = FastAPI()

# React'in bu API'ye istek atabilmesi için CORS izni veriyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
messages = [{"role": "system", "content": "Sen otonom asistan Aria'sın. Kısa, net ve çözüm odaklı cevaplar ver."}]

class ChatRequest(BaseModel):
    message: str

def speak(text: str):
    """Sesi arka planda asenkron olarak çalar ki API yanıtı gecikmesin."""
    filename = f"temp_{uuid.uuid4().hex[:6]}.mp3"
    async def _generate():
        communicate = edge_tts.Communicate(text, "tr-TR-EmelNeural")
        await communicate.save(filename)
    try:
        asyncio.run(_generate())
        playsound(filename)
        os.remove(filename)
    except Exception as e:
        print(f"Ses hatası: {e}")

@app.post("/api/chat")
def chat_with_aria(req: ChatRequest):
    global messages
    messages.append({"role": "user", "content": req.message})
    
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=TOOL_DEFINITIONS, tool_choice="auto", temperature=0.2
        )
        msg = response.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tool in msg.tool_calls:
                fn_name = tool.function.name
                try: args = json.loads(tool.function.arguments)
                except: args = {}
                
                fn = TOOL_MAP.get(fn_name)
                output = fn(**args) if fn else f"Hata: {fn_name} yok."
                messages.append({"role": "tool", "tool_call_id": tool.id, "content": str(output)})
                
            messages.append({"role": "user", "content": "SİSTEM NOTU: İşlem başarılıysa başka araç çağırma, kullanıcıya yanıt ver."})
        else:
            messages.append({"role": "assistant", "content": msg.content})
            speak(msg.content) # Yanıtı hem sese çevirip hem React'e metin olarak dönüyoruz
            return {"response": msg.content, "status": "success"}
            
    return {"response": "Döngü sınırına ulaşıldı.", "status": "timeout"}

if __name__ == "__main__":
    print("Aria API Sunucusu 8000 portunda çalışıyor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)