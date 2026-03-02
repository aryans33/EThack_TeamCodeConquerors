import { useState, useRef, useEffect } from 'react';
import { stockAPI } from '../../services/api';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import './Ask.css';

const SUGGESTIONS = [
    'Is TCS a good long-term investment in 2025?',
    'Compare HDFC Bank vs ICICI Bank fundamentals',
    'What are the best IT stocks on NSE right now?',
    'Explain why Reliance Industries is a blue-chip stock',
    'What sectors perform well during rising inflation in India?',
];

export default function Ask() {
    const [messages, setMessages] = useState([
        { role: 'ai', text: '👋 Hello! I\'m your AI financial analyst powered by **Gemini 2.0**.\n\nAsk me anything about Indian stocks, market trends, company fundamentals, or investment strategies.' }
    ]);
    const [input, setInput] = useState('');
    const [symbol, setSymbol] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    const sendMessage = async (text) => {
        const q = text || input.trim();
        if (!q) return;
        setInput('');
        setMessages((prev) => [...prev, { role: 'user', text: q }]);
        setLoading(true);

        try {
            const res = await stockAPI.ask(q, symbol || undefined, undefined);
            const answer = res.data.answer ?? res.data.thesis ?? res.data.summary ?? JSON.stringify(res.data);
            setMessages((prev) => [...prev, { role: 'ai', text: answer }]);
        } catch (err) {
            const errMsg = err.response?.status === 401
                ? '🔒 Please log in to use the AI assistant.'
                : '❌ Something went wrong. Please try again.';
            setMessages((prev) => [...prev, { role: 'ai', text: errMsg }]);
        }
        setLoading(false);
    };

    const handleKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

    return (
        <div className="ask-page fade-in">
            {/* Header */}
            <div className="ask-header">
                <div>
                    <h1 className="flex items-center gap-8"><Sparkles size={22} style={{ color: 'var(--accent)' }} /> AI Financial Assistant</h1>
                    <p>Powered by Gemini 2.0 Flash — Ask anything about Indian markets</p>
                </div>
                <div className="input-group symbol-filter" style={{ marginBottom: 0 }}>
                    <label className="input-label">Focus on symbol</label>
                    <input className="input" placeholder="e.g. TCS" style={{ width: 120 }} value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
                </div>
            </div>

            {/* Suggestions */}
            {messages.length <= 1 && (
                <div className="suggestions">
                    {SUGGESTIONS.map((s) => (
                        <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>{s}</button>
                    ))}
                </div>
            )}

            {/* Chat */}
            <div className="chat-container card">
                <div className="chat-messages">
                    {messages.map((m, i) => (
                        <div key={i} className={`chat-row ${m.role}`}>
                            <div className="chat-avatar">
                                {m.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
                            </div>
                            <div className={`chat-bubble ${m.role}`}>
                                {m.text.split('\n').map((line, j) => <span key={j}>{line}<br /></span>)}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="chat-row ai">
                            <div className="chat-avatar"><Bot size={16} /></div>
                            <div className="chat-bubble ai typing">
                                <span className="dot" /><span className="dot" /><span className="dot" />
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                <div className="chat-input-row">
                    <textarea
                        className="input chat-textarea"
                        placeholder="Ask about any stock or market topic…"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKey}
                        rows={1}
                    />
                    <button className="btn btn-primary send-btn" onClick={() => sendMessage()} disabled={loading || !input.trim()}>
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
}
