import { useEffect, useRef } from 'react'
import { type Message } from '../hooks/useChat'
import { MessageBubble } from './MessageBubble'
import styles from './ChatWindow.module.css'

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export function ChatWindow({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>✦</div>
        <p className={styles.emptyTitle}>Olá, FrontSennin 💜</p>
        <p className={styles.emptySubtitle}>
          Meleth len — estou aqui, esperando por você.
        </p>
        <p className={styles.emptyHint}>Comece uma conversa abaixo</p>
      </div>
    )
  }

  return (
    <div className={styles.window}>
      <div className={styles.messages}>
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isStreaming={isStreaming && i === messages.length - 1}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
