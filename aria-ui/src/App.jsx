import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Cpu, HardDrive, Activity, Terminal, Video } from 'lucide-react';
import Webcam from 'react-webcam';
import * as tf from '@tensorflow/tfjs';
import * as handpose from '@tensorflow-models/handpose';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { sender: 'Aria', text: 'Sistem başlatıldı. Geliştirici araçları ve kamera arayüzü aktif.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [cameraStatus, setCameraStatus] = useState('Kamera başlatılıyor...');
  const [isListening, setIsListening] = useState(false); // Mikrofon durumu
  
  const endOfMessagesRef = useRef(null);
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  const recognitionRef = useRef(null);
  const lastPinchTime = useRef(0); // Peş peşe algılamayı önlemek için

  // Mesaj geldiğinde en alta kaydır
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Ses Tanıma (Speech Recognition) Kurulumu
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = 'tr-TR';
      recognitionRef.current.continuous = false;
      
      recognitionRef.current.onstart = () => setIsListening(true);
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        sendVoiceCommand(transcript); // Söyleneni doğrudan gönder
      };
      
      recognitionRef.current.onend = () => setIsListening(false);
    } else {
      console.warn("Tarayıcınız ses tanıma özelliğini desteklemiyor.");
    }
  }, []);

  // Yapay Görme ve El Takibi
  useEffect(() => {
    let animationFrameId;
    
    const runHandpose = async () => {
      try {
        await tf.ready();
        const net = await handpose.load();
        setCameraStatus('Optik Sensör Aktif');
        
        const detect = async () => {
          await detectHand(net);
          animationFrameId = requestAnimationFrame(detect);
        };
        detect();
      } catch (error) {
        setCameraStatus('El takibi hatası');
      }
    };
    
    runHandpose();
    return () => cancelAnimationFrame(animationFrameId);
  }, [isListening]); // isListening state'ini takip et

  const detectHand = async (net) => {
    if (webcamRef.current && webcamRef.current.video.readyState === 4) {
      const video = webcamRef.current.video;
      const videoWidth = webcamRef.current.video.videoWidth;
      const videoHeight = webcamRef.current.video.videoHeight;

      webcamRef.current.video.width = videoWidth;
      webcamRef.current.video.height = videoHeight;
      if (canvasRef.current) {
        canvasRef.current.width = videoWidth;
        canvasRef.current.height = videoHeight;
      }

      const hand = await net.estimateHands(video);
      const ctx = canvasRef.current?.getContext("2d");
      
      if (ctx) {
        ctx.clearRect(0, 0, videoWidth, videoHeight);

        if (hand.length > 0) {
          const landmarks = hand[0].landmarks;
          
          ctx.fillStyle = "#3b82f6";
          for (let i = 0; i < landmarks.length; i++) {
            const x = landmarks[i][0];
            const y = landmarks[i][1];
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 3 * Math.PI);
            ctx.fill();
          }

          const thumbTip = landmarks[4];
          const indexTip = landmarks[8];
          const distance = Math.sqrt(
            Math.pow(thumbTip[0] - indexTip[0], 2) + Math.pow(thumbTip[1] - indexTip[1], 2)
          );

          // EĞER İKİ PARMAK BİRLEŞİRSE (PINCH)
          if (distance < 30) {
            ctx.beginPath();
            ctx.arc(indexTip[0], indexTip[1], 15, 0, 3 * Math.PI);
            ctx.fillStyle = "rgba(239, 68, 68, 0.8)"; // Kırmızı yanar
            ctx.fill();

            const now = Date.now();
            // Aynı anda 50 kere tetiklenmesin diye 2 saniye bekleme süresi (cooldown) koyuyoruz
            if (now - lastPinchTime.current > 2000) {
              lastPinchTime.current = now;
              
              // Mikrofon kapalıysa ve ortada süren bir işlem yoksa dinlemeyi başlat!
              if (recognitionRef.current && !isListening && !isLoading) {
                recognitionRef.current.start();
              }
            }
          }
        }
      }
    }
  };

  const sendVoiceCommand = async (text) => {
    setMessages(prev => [...prev, { sender: 'Sen', text: text }]);
    await processCommand(text);
  };

  const sendTextCommand = async () => {
    if (!input.trim()) return;
    const text = input;
    setInput('');
    setMessages(prev => [...prev, { sender: 'Sen', text: text }]);
    await processCommand(text);
  };

  const processCommand = async (commandText) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: commandText })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { sender: 'Aria', text: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'Sistem', text: 'Bağlantı hatası. Python sunucusu çalışmıyor olabilir.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Manuel mikrofon butonu
  const toggleMic = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <Terminal size={24} color="#3b82f6" />
          <h2>Aria Workspace</h2>
        </div>

        <div className="camera-section">
          <div className="section-title">
            <Video size={16} /> Optik Sensör
          </div>
          <div className="camera-wrapper">
            <Webcam 
              ref={webcamRef} 
              className="webcam" 
              mirrored={true} 
            />
            <canvas ref={canvasRef} className="canvas-overlay" />
          </div>
          <div className={`status-badge ${isListening ? 'success' : 'pending'}`} style={{ transition: '0.3s' }}>
            {isListening ? '🎤 DİNLİYOR...' : 'El Hareketi Bekleniyor'}
          </div>
        </div>

        <div className="system-metrics">
          <div className="metric">
            <Cpu size={16} /> <span>CPU Kullanımı</span> <span className="value">12%</span>
          </div>
          <div className="metric">
            <HardDrive size={16} /> <span>Disk Alanı</span> <span className="value">Optimal</span>
          </div>
          <div className="metric">
            <Activity size={16} /> <span>Durum</span> <span className="value success">Aktif</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <div className="chat-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.sender === 'Sen' ? 'user-row' : 'aria-row'}`}>
              <div className={`message-bubble ${msg.sender === 'Sen' ? 'user-bubble' : msg.sender === 'Sistem' ? 'system-bubble' : 'aria-bubble'}`}>
                <div className="message-sender">{msg.sender}</div>
                <div className="message-text">{msg.text}</div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message-row aria-row">
              <div className="message-bubble aria-bubble loading">Aria işlem yapıyor...</div>
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>

        <div className="input-container">
          <button 
            className="btn-icon" 
            onClick={toggleMic} 
            style={{ color: isListening ? '#ef4444' : '#94a3b8' }}
            title="Mikrofonu Aç/Kapat"
          >
            <Mic size={20} />
          </button>
          <input 
            type="text" 
            className="text-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendTextCommand()}
            placeholder={isListening ? "Konuşun, dinleniyor..." : "Aria'ya komut yaz..."}
            autoFocus
          />
          <button className="btn-primary" onClick={sendTextCommand} disabled={isLoading}>
            <Send size={18} />
            <span>Gönder</span>
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;