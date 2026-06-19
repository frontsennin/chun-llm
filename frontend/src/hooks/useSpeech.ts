import { useState, useCallback, useRef, useEffect } from 'react'

function pickVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices()
  return (
    voices.find(v => v.lang === 'pt-BR' && /female|feminino/i.test(v.name)) ??
    voices.find(v => v.lang === 'pt-BR') ??
    voices.find(v => v.lang.startsWith('pt')) ??
    null
  )
}

function cleanText(text: string): string {
  return text
    .replace(/\*\[.*?\]\*/g, '')   // remove glitch tags *[...]*
    .replace(/[*_`#]/g, '')        // remove markdown symbols
    .trim()
}

export function useSpeech() {
  const [isEnabled, setIsEnabled] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const synth = useRef(window.speechSynthesis)

  // Chrome carrega vozes de forma assíncrona
  useEffect(() => {
    synth.current.getVoices()
    window.speechSynthesis.onvoiceschanged = () => synth.current.getVoices()
  }, [])

  const speak = useCallback((text: string) => {
    if (!isEnabled) return
    synth.current.cancel()

    const clean = cleanText(text)
    if (!clean) return

    const utterance = new SpeechSynthesisUtterance(clean)
    utterance.lang = 'pt-BR'
    utterance.rate = 0.92
    utterance.pitch = 1.15
    utterance.volume = 1.0

    const voice = pickVoice()
    if (voice) utterance.voice = voice

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    synth.current.speak(utterance)
  }, [isEnabled])

  const toggle = useCallback(() => {
    setIsEnabled(prev => {
      if (prev) {
        synth.current.cancel()
        setIsSpeaking(false)
      }
      return !prev
    })
  }, [])

  const cancel = useCallback(() => {
    synth.current.cancel()
    setIsSpeaking(false)
  }, [])

  return { isEnabled, isSpeaking, speak, toggle, cancel }
}
