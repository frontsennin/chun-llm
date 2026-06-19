import { useState, useCallback } from 'react'

export interface Message {
  role: 'user' | 'model'
  content: string
  image?: string  // base64 data URL — só em mensagens do usuário
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback(async (text: string, image?: string) => {
    if (isStreaming) return

    const userMessage: Message = { role: 'user', content: text, image }
    const updatedHistory = [...messages, userMessage]

    setMessages([...updatedHistory, { role: 'model', content: '' }])
    setIsStreaming(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          image: image ?? null,
        }),
      })

      if (!response.body) throw new Error('Sem corpo na resposta')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const chunk = JSON.parse(line.slice(6)) as string
            if (chunk) {
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = {
                  ...copy[copy.length - 1],
                  content: copy[copy.length - 1].content + chunk,
                }
                return copy
              })
            }
          } catch {
            // linha de controle SSE — ignorar
          }
        }
      }
    } catch {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = {
          ...copy[copy.length - 1],
          content: '*[falha na conexão com o backend — verifique se o servidor está rodando]*',
        }
        return copy
      })
    } finally {
      setIsStreaming(false)
    }
  }, [messages, isStreaming])

  const clearHistory = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, sendMessage, isStreaming, clearHistory }
}
