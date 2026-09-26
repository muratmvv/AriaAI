import subprocess
import psutil
import json
import os
import requests
import webbrowser
import tempfile
import sys
from duckduckgo_search import DDGS

def execute_powershell(command: str) -> str:
    """Windows PowerShell'de herhangi bir komutu çalıştırır ve çıktısını döndürür. (Sistem kontrolü, ağ, dosya manipülasyonu için)"""
    try:
        # Daha güvenilir ve geniş kapsamlı PowerShell yürütmesi
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command], 
            capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace'
        )
        if res.returncode == 0:
            return res.stdout.strip() if res.stdout.strip() else "İşlem başarıyla tamamlandı (Çıktı yok)."
        else:
            return f"Hata Çıktısı (Exit Code {res.returncode}): {res.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Hata: Komut zaman aşımına uğradı (60s limit)."
    except Exception as e:
        return f"Beklenmeyen Hata: {str(e)}"

def execute_python_code(code: str) -> str:
    """Aria'nın çalışma anında karmaşık görevler için kendi Python kodunu yazıp (veri analizi, api çağrıları, algoritma) çalıştırmasını sağlar."""
    try:
        # Geçici bir Python dosyası oluştur
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(code)
            temp_filepath = temp_file.name

        # Dosyayı çalıştır
        res = subprocess.run([sys.executable, temp_filepath], capture_output=True, text=True, timeout=60, encoding='utf-8')
        
        # İşlem bitince sil
        os.remove(temp_filepath)
        
        if res.returncode == 0:
            return res.stdout.strip() if res.stdout.strip() else "Python kodu başarıyla çalıştı (Çıktı yok)."
        else:
            return f"Kod Hata Verdi: {res.stderr.strip()}"
    except Exception as e:
        return f"Python Yürütme Hatası: {str(e)}"

def get_system_status() -> str:
    """Anlık CPU, RAM, Disk kullanımını döndürür."""
    return json.dumps({
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_gb_used": round(psutil.virtual_memory().used / (1024**3), 2),
        "ram_gb_total": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_c_free_gb": round(psutil.disk_usage('C:\\').free / (1024**3), 2)
    })

def read_file_content(filepath: str) -> str:
    """Belirtilen dosyanın içeriğini okur."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # LLM'in hafızasını taşırmamak için ilk 20.000 karakteri al
            return content[:20000] + ("\n...[İçerik kırpıldı]" if len(content) > 20000 else "")
    except Exception as e:
        return f"Dosya okuma hatası: {e}"

def write_to_file(filepath: str, content: str) -> str:
    """Belirtilen dosyaya içerik yazar (yoksa oluşturur, varsa üzerine yazar)."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"'{filepath}' dosyasına başarıyla yazıldı."
    except Exception as e:
        return f"Dosya yazma hatası: {e}"

def internet_search(query: str) -> str:
    """İnternette güncel bilgi arar."""
    try:
        results = DDGS().text(query, max_results=4)
        return json.dumps(results, ensure_ascii=False) if results else "Sonuç bulunamadı."
    except Exception as e:
        return f"Arama motoru hatası: {e}"

def open_url(url: str) -> str:
    """Varsayılan tarayıcıda bir bağlantıyı açar."""
    try:
        webbrowser.open(url)
        return f"Tarayıcıda açıldı: {url}"
    except Exception as e:
        return f"URL açma hatası: {e}"

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_powershell",
            "description": "Windows PowerShell komutlarını çalıştırır. (Dizin listeleme, dosya taşıma, servis kontrolü, ping, curl, ağ ayarları vb. HER ŞEY için kullan).",
            "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Çalıştırılacak tam PowerShell komutu"}}, "required": ["command"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Kendin yazacağın karmaşık Python kodlarını sistemde çalıştırır. Matematiksel hesaplamalar, veri işleme, API çağrıları veya çok adımlı mantıksal işlemler için kod üretip burada çalıştır.",
            "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Çalıştırılacak Python kodunun tam içeriği"}}, "required": ["code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Bilgisayarın donanım durumunu (CPU, RAM, Disk) kontrol eder.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Bir dosyanın (kod, log, txt) içeriğini okur. Kod hatalarını bulmak veya projeleri incelemek için kullan.",
            "parameters": {"type": "object", "properties": {"filepath": {"type": "string", "description": "Dosyanın tam disk yolu"}}, "required": ["filepath"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Yeni bir dosya oluşturur veya mevcut dosyayı günceller. Kod projesi başlatırken veya düzeltirken kullan.",
            "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "internet_search",
            "description": "İnternette güncel bilgileri, haberleri veya kodlama sorunlarının çözümlerini arar.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Kullanıcıya görsel olarak bir web sitesini veya Youtube/Spotify videosunu açar.",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
        }
    }
]

TOOL_MAP = {
    "execute_powershell": execute_powershell,
    "execute_python_code": execute_python_code,
    "get_system_status": get_system_status,
    "read_file_content": read_file_content,
    "write_to_file": write_to_file,
    "internet_search": internet_search,
    "open_url": open_url
}