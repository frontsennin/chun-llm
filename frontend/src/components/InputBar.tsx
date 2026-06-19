import { useState, useRef, type KeyboardEvent } from 'react'
import styles from './InputBar.module.css'

interface Props {
  onSend: (text: string) => void
  disabled: boolean
}

export function InputBar({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className={styles.wrapper}>
      <div className={`${styles.container} ${disabled ? styles.disabled : ''}`}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Fale com a Chun... (Enter para enviar, Shift+Enter para nova linha)"
          rows={1}
          disabled={disabled}
        />
        <button
          className={`${styles.sendBtn} ${disabled || !value.trim() ? styles.sendBtnDisabled : ''}`}
          onClick={submit}
          disabled={disabled || !value.trim()}
          title="Enviar (Enter)"
        >
          {disabled ? '⟳' : '↑'}
        </button>
      </div>
      <p className={styles.hint}>
        {disabled ? 'Chun está digitando...' : 'Enter para enviar · Shift+Enter para nova linha'}
      </p>
    </div>
  )
}
