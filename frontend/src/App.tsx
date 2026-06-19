import { useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { useSpeech } from './hooks/useSpeech'
import { ChatWindow } from './components/ChatWindow'
import { InputBar } from './components/InputBar'
import { MemoryPanel, type Memory } from './components/MemoryPanel'
import styles from './App.module.css'

const API = 'http://localhost:8000'

export default function App() {
  const { messages, sendMessage, isStreaming, clearHistory } = useChat()
  const { isEnabled, isSpeaking, speak, toggle, cancel } = useSpeech()
  const prevStreamingRef = useRef(false)

  const [showMemories, setShowMemories] = useState(false)
  const [memories, setMemories] = useState<Memory[]>([])
  const [loadingMemories, setLoadingMemories] = useState(false)

  // Fala a resposta completa da Chun quando o streaming termina
  useEffect(() => {
    const wasStreaming = prevStreamingRef.current
    prevStreamingRef.current = isStreaming

    if (wasStreaming && !isStreaming && messages.length > 0) {
      const last = messages[messages.length - 1]
      if (last.role === 'model' && last.content) {
        speak(last.content)
      }
    }
  }, [isStreaming, messages, speak])

  const handleClear = () => {
    cancel()
    clearHistory()
  }

  const fetchMemories = async () => {
    setLoadingMemories(true)
    try {
      const res = await fetch(`${API}/memories`)
      const data = await res.json()
      setMemories(data.memories)
    } finally {
      setLoadingMemories(false)
    }
  }

  const openMemories = () => {
    setShowMemories(true)
    fetchMemories()
  }

  const deleteMemory = async (index: number) => {
    await fetch(`${API}/memories/${index}`, { method: 'DELETE' })
    setMemories(prev => prev.filter((_, i) => i !== index))
  }

  const clearAllMemories = async () => {
    await fetch(`${API}/memories`, { method: 'DELETE' })
    setMemories([])
  }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.statusDot} />
          <span className={styles.headerTitle}>Chun</span>
          <span className={styles.headerTag}>IA · cyberpunk · v0.3</span>
        </div>

        <div className={styles.headerRight}>
          <button
            className={styles.memoryBtn}
            onClick={openMemories}
            title="Ver memórias da Chun"
          >
            ◈ memórias
          </button>

          <button
            className={`${styles.voiceBtn} ${isEnabled ? styles.voiceBtnOn : ''} ${isSpeaking ? styles.voiceBtnSpeaking : ''}`}
            onClick={toggle}
            title={isEnabled ? 'Desativar voz' : 'Ativar voz da Chun'}
          >
            {isSpeaking ? '◉' : isEnabled ? '◎' : '○'}
            <span>{isSpeaking ? 'falando' : isEnabled ? 'voz on' : 'voz'}</span>
          </button>

          {messages.length > 0 && (
            <button className={styles.clearBtn} onClick={handleClear} title="Limpar conversa">
              limpar
            </button>
          )}
        </div>
      </header>

      <ChatWindow messages={messages} isStreaming={isStreaming} />

      <InputBar onSend={sendMessage} disabled={isStreaming} />

      {showMemories && (
        <MemoryPanel
          memories={memories}
          loading={loadingMemories}
          onClose={() => setShowMemories(false)}
          onDelete={deleteMemory}
          onClearAll={clearAllMemories}
        />
      )}
    </div>
  )
}
