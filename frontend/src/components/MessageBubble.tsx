import { type Message } from '../hooks/useChat'
import styles from './MessageBubble.module.css'

interface Props {
  message: Message
  isStreaming: boolean
}

function parseGlitchText(text: string) {
  const parts = text.split(/(\*\[.*?\]\*)/)
  return parts.map((part, i) => {
    if (part.startsWith('*[') && part.endsWith(']*')) {
      return (
        <span key={i} className={styles.glitchTag}>
          {part.slice(2, -2)}
        </span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isChun = message.role === 'model'

  return (
    <div className={`${styles.row} ${isChun ? styles.chunRow : styles.userRow}`}>
      {isChun && (
        <div className={styles.avatar}>
          <span className={styles.avatarIcon}>✦</span>
        </div>
      )}

      <div className={`${styles.bubble} ${isChun ? styles.chunBubble : styles.userBubble}`}>
        {isChun ? (
          <p className={styles.text}>
            {parseGlitchText(message.content)}
            {isStreaming && message.content === '' && (
              <span className={styles.thinkingDots}>
                <span>.</span><span>.</span><span>.</span>
              </span>
            )}
            {isStreaming && message.content !== '' && (
              <span className={styles.cursor}>▌</span>
            )}
          </p>
        ) : (
          <p className={styles.text}>{message.content}</p>
        )}
      </div>
    </div>
  )
}
