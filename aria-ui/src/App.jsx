import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Terminal } from 'lucide-react';
import './App.css'; // Siyah temayı ekleyeceğiz

function App() {
  const [messages, setMessages] = useState([{ sender: 'Aria', text: 'Sistem çevrimiçi. Nasıl yardımcı olabilirim?' }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef(null);

  // Yeni mesaj geldiğinde en alta kaydır
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userText = input;
    setMessages(prev => [...prev, { sender: 'Sen', text: userText }]);
    setInput('');
    setIsLoading(true);

    try {
      // Python (FastAPI) sunucusuna istek at
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { sender: 'Aria', text: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'Sistem', text: 'API bağlantı hatası. Python sunucusunun açık olduğundan emin ol.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <Terminal size={24} color="#00ffcc" />
        <h1>A.R.I.A CORE</h1>
      </header>
      
      <main className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.sender === 'Sen' ? 'right' : 'left'}`}>
            <div className={`message ${msg.sender === 'Sen' ? 'user' : msg.sender === 'Sistem' ? 'system' : 'aria'}`}>
              <span className="sender-name">{msg.sender}</span>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper left">
            <div className="message aria loading">Aria işlem yapıyor...</div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </main>

      <div className="input-area">
        <button className="icon-btn" title="Sesli Komut (Yakında)"><Mic size={20} /></button>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Komut girin..."
        />
        <button className="icon-btn send" onClick={sendMessage} disabled={isLoading}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}

export default App;