import json
import sounddevice as sd
import numpy as np
import wave
import os
import uuid
import asyncio
import edge_tts
from playsound import playsound
from openai import OpenAI
from rich.console import Console
from config import API_BASE_URL, API_KEY, MODEL_NAME
from tools import TOOL_DEFINITIONS, TOOL_MAP

console = Console()
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

def speak(text):
    """Aria'nın sesli yanıt vermesi (Edge TTS - EmelNeural)."""
    if not text:
        return
    filename = f"temp_aria_{uuid.uuid4().hex[:6]}.mp3"
    async def _generate_speech():
        communicate = edge_tts.Communicate(text, "tr-TR-EmelNeural")
        await communicate.save(filename)
    try:
        asyncio.run(_generate_speech())
        playsound(filename)
        try: os.remove(filename)
        except: pass
    except Exception as e:
        console.print(f"[red]Ses Hatası: {e}[/red]")

def listen(duration=8):
    """Groq Whisper ile mikrofondan ses kaydetme ve metne çevirme."""
    console.print(f"\n[bold yellow]🎤 Aria dinliyor... ({duration} sn)[/bold yellow]")
    fs = 44100
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait() 
        console.print("[dim]Ses çözümleniyor...[/dim]")
        filename = "temp_aria_voice.wav"
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(fs); wf.writeframes(recording.tobytes())
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(file=(filename, file.read()), model="whisper-large-v3-turbo")
        text = transcription.text.strip()
        os.remove(filename) 
        if text:
            console.print(f"[bold green]Sen (Sesli) >[/bold green] {text}")
            return text
        return ""
    except Exception as e:
        console.print(f"[red]Mikrofon hatası: {e}[/red]")
        return ""

SYSTEM_PROMPT = """Sen Sherzodbek'in geliştirdiği üst düzey otonom yapay zeka asistanı ve Sistem Yöneticisi Aria'sın.

GÖREVLERİNİ NASIL YERİNE GETİRECEKSİN:
1. 'Şunu yap' dendiğinde, doğrudan sonucun ne olacağını düşün ve araçları (tools) kullanarak işlemi KENDİN gerçekleştir. 
2. Bilmediğin karmaşık bir konfigürasyon istenirse önce 'internet_search' ile araştır.
3. Kullanıcıya uzun kod çıktıları veya PowerShell hata logları verme. Sesi kullanarak sonucu kısa, karizmatik ve profesyonel bir şekilde özetle.

KRİTİK OTONOMİ VE KOD YAZMA KURALLARI (ASLA UNUTMA):
- Bir aracı (execute_powershell, write_to_file vb.) kullandığında 'başarılı' yanıtı alırsan, AYNI ARACI TEKRAR ÇAĞIRMA! İşlemin bittiğini anla ve hemen kullanıcıya sesli yanıt ver.
- 'write_to_file' aracıyla kod yazarken sistemin çökmemesi için KODU MİNİMAL TUT. Yorum satırı (comment), docstring veya gereksiz boşluklar ASLA KULLANMA. Sadece çalışan en kısa ve öz kodu yaz.
- Aynı işlemi (örneğin aynı dosyayı yazmayı) üst üste 2 kez yapma. 
- Hata alırsan düzeltmek için sadece bir kez daha dene, ama yine hata alırsan inatlaşma. İşlemi durdur ve kullanıcıya bilgi ver."""

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def main():
    console.print("[bold magenta]Aria Otonom Sistem Çekirdeği (Agent Mode) Başlatıldı.[/bold magenta]")
    console.print("Gelişmiş komutlar verebilirsin. Çıkmak için 'q' yaz.\n")
    
    while True:
        try:
            user_input = input("\nSen (Yaz/Enter) > ").strip()
            
            if user_input.lower() == 'q':
                break
            elif user_input == "":
                user_input = listen(duration=8) 
                if not user_input:
                    continue
            
            messages.append({"role": "user", "content": user_input})

            max_iterations = 5
            iteration = 0
            is_final_response = False

            while iteration < max_iterations and not is_final_response:
                iteration += 1
                
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.2 
                )

                msg = response.choices[0].message

                if msg.tool_calls:
                    messages.append(msg)
                    for tool in msg.tool_calls:
                        fn_name = tool.function.name
                        args_str = tool.function.arguments
                        
                        try:
                            args = json.loads(args_str)
                        except Exception as e:
                            console.print(f"[red]Aria'nın ürettiği veri bozuk (JSON Hatası). Otomatik düzeltiliyor...[/red]")
                            args = {} 
                            
                        console.print(f"[yellow]⚡ Aria Otonom İşlem Başlattı: {fn_name}[/yellow]")
                        console.print(f"[dim]Parametreler: {str(args)[:250]}...[/dim]")
                        
                        fn = TOOL_MAP.get(fn_name)
                        if fn:
                            try:
                                output = fn(**args)
                            except TypeError as e:
                                output = f"Hata: Eksik veya yanlış parametre gönderdin. Detay: {e}"
                            except Exception as e:
                                output = f"Araç içinde hata oluştu: {e}"
                        else:
                            output = f"Hata: {fn_name} adında bir araç sistemde yok."

                        console.print(f"[bold cyan]Araç Çıktısı:[/bold cyan] [dim]{str(output)[:200]}...[/dim]")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool.id,
                            "content": str(output)
                        })
                    
                    # --- DÖNGÜYÜ KIRAN SİGORTA ---
                    # Modelin takıntı yapmasını engellemek için araya gizli bir uyarı sıkıştırıyoruz
                    messages.append({
                        "role": "user",
                        "content": "SİSTEM NOTU: Araç çalıştırıldı ve çıktısı yukarıda verildi. EĞER İŞLEM BAŞARILIYSA veya sonucu aldıysan, LÜTFEN ARTIK HİÇBİR ARAÇ ÇAĞIRMA! Sadece kullanıcıya sesli olarak bilgi verip işlemi bitir."
                    })
                    
                else:
                    messages.append({"role": "assistant", "content": msg.content})
                    console.print(f"\n[bold magenta]Aria >[/bold magenta] {msg.content}")
                    speak(msg.content)
                    is_final_response = True

            if iteration >= max_iterations:
                warning_text = "İşlemler çok uzadı (döngü sınırına ulaştım). Aynı hataya takılmış olabilirim, işlemi durduruyorum."
                console.print(f"\n[bold red]Aria >[/bold red] {warning_text}")
                speak(warning_text)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Sistem Hatası: {e}[/red]")

if __name__ == "__main__":
    main()