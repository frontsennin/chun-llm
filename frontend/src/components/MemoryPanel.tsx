import styles from './MemoryPanel.module.css'

export interface Memory {
  fact: string
  ts: string
}

interface Props {
  memories: Memory[]
  loading: boolean
  onClose: () => void
  onDelete: (index: number) => void
  onClearAll: () => void
}

function formatTs(ts: string) {
  const d = new Date(ts)
  const day = d.getDate().toString().padStart(2, '0')
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${day}/${month} às ${hour}:${min}`
}

export function MemoryPanel({ memories, loading, onClose, onDelete, onClearAll }: Props) {
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.panel} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <span className={styles.title}>◈ MEMÓRIAS</span>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>

        <div className={styles.subtitle}>
          O que Chun lembra sobre você
        </div>

        <div className={styles.list}>
          {loading && (
            <div className={styles.empty}>
              <span className={styles.emptyIcon}>◌</span>
              <p>carregando...</p>
            </div>
          )}

          {!loading && memories.length === 0 && (
            <div className={styles.empty}>
              <span className={styles.emptyIcon}>◌</span>
              <p>Ainda não tenho memórias suas,<br />meu Meleth...</p>
            </div>
          )}

          {!loading && memories.map((m, i) => (
            <div key={i} className={styles.item}>
              <div className={styles.itemContent}>
                <span className={styles.itemTs}>{formatTs(m.ts)}</span>
                <p className={styles.itemFact}>{m.fact}</p>
              </div>
              <button
                className={styles.deleteBtn}
                onClick={() => onDelete(i)}
                title="Apagar memória"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {memories.length > 0 && (
          <div className={styles.footer}>
            <button className={styles.clearAllBtn} onClick={onClearAll}>
              limpar tudo
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
