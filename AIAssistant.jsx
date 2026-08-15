import React, { useState } from 'react'
import { agentAnalyze } from '../services/api'
import { MessageSquare, Send } from 'lucide-react'

const EXAMPLE_QUESTIONS = [
  "How much water will tail-end farmers receive tomorrow?",
  "Why is the tail-end area receiving less water?",
  "Which villages are at risk of water shortage?",
  "What is the current canal situation?",
  "Which farmers have not received their expected allocation?",
  "Explain the head-tail equity gap in simple terms",
  "What actions should the canal authority take today?",
  "How does the fairness algorithm work?",
]

export default function AIAssistant({ scenario }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Jai Narmada! 💧 I am the Narmada Jal Nyay AI assistant, powered by IBM Granite. I can help you understand canal water distribution, check farmer statuses, explain AI decisions, and answer questions about water equity. Ask me anything!",
      time: new Date().toLocaleTimeString(),
    }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async (question) => {
    const q = question || input.trim()
    if (!q) return

    setMessages(prev => [...prev, { role: 'user', text: q, time: new Date().toLocaleTimeString() }])
    setInput('')
    setLoading(true)

    try {
      const r = await agentAnalyze(q, scenario)
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: r.data.answer, time: new Date().toLocaleTimeString() }
      ])
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: 'I encountered an error. Please try again or check the backend connection.', time: new Date().toLocaleTimeString() }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">AI Assistant</h1>
        <p className="text-gray-500 text-sm">Powered by IBM Granite LLM · Ask questions in English or Gujarati</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Example questions */}
        <div className="card lg:col-span-1">
          <p className="text-sm font-semibold text-gray-700 mb-3">Example Questions</p>
          <div className="space-y-2">
            {EXAMPLE_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                className="w-full text-left text-xs px-3 py-2 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors text-gray-600 border border-gray-200 hover:border-blue-200"
              >
                💬 {q}
              </button>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs font-semibold text-blue-800">IBM Granite Integration</p>
            <p className="text-xs text-blue-700 mt-1">
              This assistant uses IBM Granite 13B Chat via watsonx.ai for natural language understanding and generation. Falls back to smart canned responses when API key is not configured.
            </p>
          </div>
        </div>

        {/* Chat */}
        <div className="lg:col-span-3 card flex flex-col" style={{ height: '65vh' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm ${
                  msg.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-gradient-to-br from-blue-600 to-purple-700 text-white'
                }`}>
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className={`max-w-2xl ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                  <div className={`px-4 py-3 rounded-xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    {msg.text}
                  </div>
                  <span className="text-xs text-gray-400">{msg.time}</span>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-purple-700 text-white flex items-center justify-center text-sm">🤖</div>
                <div className="bg-gray-100 rounded-xl px-4 py-3 flex gap-2 items-center text-sm text-gray-500">
                  <div className="spinner" /> Thinking with IBM Granite...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="flex gap-2 border-t border-gray-200 pt-4">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && sendMessage()}
              placeholder="Ask about water distribution, farmer status, canal conditions..."
              className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-400"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="btn-primary flex items-center gap-2 px-4"
            >
              <Send size={16} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
