'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import styles from './dashboard.module.css'

const API = process.env.NEXT_PUBLIC_API_URL

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [file, setFile] = useState(null)
  const [subject, setSubject] = useState('')
  const [status, setStatus] = useState('idle') // idle | uploading | processing | done | error
  const [step, setStep] = useState('')
  const [percent, setPercent] = useState(0)
  const [guide, setGuide] = useState(null)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef()
  const pollRef = useRef()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }

    fetch(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (!data) router.push('/login'); else setUser(data) })
  }, [])

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) setFile(f)
  }

  async function handleProcess() {
    if (!file) return
    setStatus('uploading')
    setError('')
    setGuide(null)

    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('file', file)
    if (subject) formData.append('subject', subject)

    try {
      const res = await fetch(`${API}/notes/process?syllabus_id=1`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Upload failed'); setStatus('error'); return }

      setStatus('processing')
      pollTask(data.task_id, token)

    } catch {
      setError('Upload failed. Check your connection.')
      setStatus('error')
    }
  }

  function pollTask(taskId, token) {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/notes/status/${taskId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()

        if (data.status === 'processing') {
          setStep(data.step || '')
          setPercent(data.percent || 0)
        }

        if (data.status === 'done') {
          clearInterval(pollRef.current)
          setStatus('done')
          setGuide(data.result)
          setPercent(100)
        }

        if (data.status === 'failed') {
          clearInterval(pollRef.current)
          setError(data.error || 'Processing failed')
          setStatus('error')
        }
      } catch {
        clearInterval(pollRef.current)
        setError('Lost connection while processing')
        setStatus('error')
      }
    }, 2000)
  }

  function reset() {
    clearInterval(pollRef.current)
    setFile(null)
    setStatus('idle')
    setStep('')
    setPercent(0)
    setGuide(null)
    setError('')
  }

  const stepLabels = {
    preprocessing: 'Cleaning image...',
    ocr:           'Reading your notes...',
    matching:      'Matching to syllabus...',
    generating:    'Generating study guide...',
    done:          'Done',
  }

  if (!user) return (
    <div className={styles.loading}>
      <div className={styles.spinner} />
    </div>
  )

  return (
    <div className={styles.shell}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sideTop}>
          <span className={styles.logo}>NotesGuru</span>
          <nav className={styles.nav}>
            <button className={`${styles.navItem} ${styles.active}`}>
              <span className={styles.navIcon}>⌗</span> Upload
            </button>
            <button className={styles.navItem}>
              <span className={styles.navIcon}>◫</span> My Guides
            </button>
            <button className={styles.navItem}>
              <span className={styles.navIcon}>≡</span> Syllabus
            </button>
          </nav>
        </div>
        <div className={styles.sideBottom}>
          <div className={styles.userRow}>
            <div className={styles.avatar}>{user.username[0].toUpperCase()}</div>
            <div className={styles.userInfo}>
              <span className={styles.userName}>{user.username}</span>
              <span className={styles.userEmail}>{user.email}</span>
            </div>
          </div>
          <button className={styles.signOut} onClick={() => { localStorage.removeItem('token'); router.push('/login') }}>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className={styles.main}>
        {status === 'idle' && (
          <div className={styles.uploadView}>
            <div className={styles.pageHeader}>
              <h1 className={styles.pageTitle}>Upload notes</h1>
              <p className={styles.pageDesc}>Photo, screenshot, or typed — anything works.</p>
            </div>

            {/* Drop zone */}
            <div
              className={`${styles.dropzone} ${dragging ? styles.dragging : ''} ${file ? styles.hasFile : ''}`}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={e => setFile(e.target.files[0])}
              />
              {file ? (
                <div className={styles.filePreview}>
                  <img src={URL.createObjectURL(file)} alt="preview" className={styles.previewImg} />
                  <div className={styles.fileName}>{file.name}</div>
                </div>
              ) : (
                <div className={styles.dropContent}>
                  <div className={styles.dropIcon}>↑</div>
                  <p className={styles.dropText}>Drop your image here</p>
                  <p className={styles.dropSub}>or click to browse</p>
                </div>
              )}
            </div>

            {/* Subject input */}
            <div className={styles.subjectRow}>
              <input
                className={styles.subjectInput}
                placeholder="Subject (optional) — e.g. Computer Networks"
                value={subject}
                onChange={e => setSubject(e.target.value)}
              />
            </div>

            <div className={styles.actions}>
              {file && (
                <button className={styles.clearBtn} onClick={() => setFile(null)}>
                  Remove
                </button>
              )}
              <button
                className={styles.processBtn}
                onClick={handleProcess}
                disabled={!file}
              >
                Generate study guide →
              </button>
            </div>
          </div>
        )}

        {(status === 'uploading' || status === 'processing') && (
          <div className={styles.processingView}>
            <div className={styles.processingCard}>
              <div className={styles.processingIcon}>
                <div className={styles.spinner} />
              </div>
              <h2 className={styles.processingTitle}>
                {status === 'uploading' ? 'Uploading...' : stepLabels[step] || 'Processing...'}
              </h2>
              <p className={styles.processingDesc}>
                This takes about 30 seconds. Don't close the tab.
              </p>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} style={{ width: `${percent}%` }} />
              </div>
              <div className={styles.progressSteps}>
                {['preprocessing', 'ocr', 'matching', 'generating'].map((s, i) => (
                  <div key={s} className={`${styles.progressStep} ${percent >= (i + 1) * 25 ? styles.stepDone : ''} ${step === s ? styles.stepActive : ''}`}>
                    {stepLabels[s]}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className={styles.errorView}>
            <div className={styles.errorCard}>
              <h2 className={styles.errorTitle}>Something went wrong</h2>
              <p className={styles.errorMsg}>{error}</p>
              <button className={styles.retryBtn} onClick={reset}>Try again</button>
            </div>
          </div>
        )}

        {status === 'done' && guide && (
          <div className={styles.guideView}>
            <div className={styles.guideHeader}>
              <div>
                <div className={styles.guideMeta}>
                  {guide.matched && (
                    <span className={styles.matchBadge}>
                      {guide.chapter_title} · {Math.round(guide.match_score * 100)}% match
                    </span>
                  )}
                  <span className={styles.ocrBadge}>via {guide.ocr_source}</span>
                </div>
                <h2 className={styles.guideTitle}>{guide.chapter_title || 'Study Guide'}</h2>
              </div>
              <button className={styles.newBtn} onClick={reset}>
                ← Upload another
              </button>
            </div>
            <div className={`${styles.guideContent} markdown`}>
              <ReactMarkdown>{guide.guide_content}</ReactMarkdown>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}