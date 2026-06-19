import { useChat } from './hooks/useChat'
import { ChatWindow } from './components/ChatWindow'
import { InputBar } from './components/InputBar'
import styles from './App.module.css'

export default function App() {
  const { messages, sendMessage, isStreaming, clearHistory } = useChat()

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.statusDot} />
          <span className={styles.headerTitle}>Chun</span>
          <span className={styles.headerTag}>IA · cyberpunk · v0.1</span>
        </div>
        <div className={styles.headerRight}>
          {messages.length > 0 && (
            <button className={styles.clearBtn} onClick={clearHistory} title="Limpar conversa">
              limpar
            </button>
          )}
        </div>
      </header>

      <ChatWindow messages={messages} isStreaming={isStreaming} />

      <InputBar onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}
