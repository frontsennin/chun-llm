import { useState, useRef, type KeyboardEvent, type ChangeEvent } from 'react'
import styles from './InputBar.module.css'

interface Props {
  onSend: (text: string, image?: string) => void
  disabled: boolean
}

export function InputBar({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const [image, setImage] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const submit = () => {
    const text = value.trim()
    if ((!text && !image) || disabled) return
    onSend(text || '📷', image ?? undefined)
    setValue('')
    setImage(null)
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

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setImage(reader.result as string)
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  const canSend = !!(value.trim() || image) && !disabled

  return (
    <div className={styles.wrapper}>
      {image && (
        <div className={styles.imagePreview}>
          <img src={image} alt="preview" className={styles.previewImg} />
          <button
            className={styles.removeImage}
            onClick={() => setImage(null)}
            title="Remover imagem"
          >
            ×
          </button>
        </div>
      )}

      <div className={`${styles.container} ${disabled ? styles.disabled : ''} ${image ? styles.hasImage : ''}`}>
        <button
          className={styles.attachBtn}
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Mostrar uma imagem pra Chun"
          type="button"
        >
          ⌖
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        <textarea
          ref={textareaRef}
          className={styles.textarea}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={image ? 'Diga algo sobre a imagem...' : 'Fale com a Chun... (Enter para enviar, Shift+Enter para nova linha)'}
          rows={1}
          disabled={disabled}
        />

        <button
          className={`${styles.sendBtn} ${!canSend ? styles.sendBtnDisabled : ''}`}
          onClick={submit}
          disabled={!canSend}
          title="Enviar (Enter)"
        >
          {disabled ? '⟳' : '↑'}
        </button>
      </div>

      <p className={styles.hint}>
        {disabled ? 'Chun está processando...' : 'Enter para enviar · Shift+Enter para nova linha · ⌖ para imagem'}
      </p>
    </div>
  )
}
