import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2, Trash2, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { sendChat } from '../api'
import useAuthStore from '../store/authStore'

const suggestions = [
  'Who is absent today?',
  'How many students are late?',
  'What is the attendance rate?',
  'Who has the lowest attendance?',
]

export default function Chatbot() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const { orgId } = useAuthStore()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const history = messages.slice(-10)
      const { data } = await sendChat(msg, orgId, history)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch {
      toast.error('Failed to get response')
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">AI Assistant</h1>
          <p className="page-subtitle mt-1">Ask anything about attendance</p>
        </div>
        {messages.length > 0 && (
          <button onClick={() => setMessages([])} className="btn-secondary flex items-center gap-2 text-sm">
            <Trash2 size={14} /> Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-16">
            <div className="w-16 h-16 bg-primary-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles size={28} className="text-primary-400" />
            </div>
            <p className="text-slate-300 font-semibold text-lg">How can I help you?</p>
            <p className="text-slate-500 text-sm mt-1">Ask about today's attendance data</p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {suggestions.map(s => (
                <button key={s} onClick={() => send(s)}
                  className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 border border-surface-700 text-sm text-slate-300 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  m.role === 'user' ? 'bg-primary-600' : 'bg-surface-800 border border-surface-700'
                }`}>
                  {m.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-primary-400" />}
                </div>
                <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-primary-600 text-white rounded-tr-sm'
                    : 'bg-surface-800 border border-surface-700 text-slate-200 rounded-tl-sm'
                }`}>
                  {m.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-surface-800 border border-surface-700">
              <Bot size={14} className="text-primary-400" />
            </div>
            <div className="bg-surface-800 border border-surface-700 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center h-4">
                {[0,1,2].map(i => (
                  <motion.div key={i} className="w-1.5 h-1.5 bg-slate-500 rounded-full"
                    animate={{ y: [0, -4, 0] }}
                    transition={{ repeat: Infinity, delay: i * 0.15, duration: 0.6 }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-3">
        <input
          className="input flex-1"
          placeholder="Ask about attendance..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          disabled={loading}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          className="btn-primary px-4 flex items-center gap-2"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  )
}
