'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import styles from './dashboard.module.css'

const API = process.env.NEXT_PUBLIC_API_URL

function authHeaders() {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [view, setView] = useState('upload') // upload | guides | syllabus
  const [file, setFile] = useState(null)
  const [subject, setSubject] = useState('')
  const [syllabusId, setSyllabusId] = useState(1)
  const [status, setStatus] = useState('idle')
  const [step, setStep] = useState('')
  const [percent, setPercent] = useState(0)
  const [guide, setGuide] = useState(null)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [guides, setGuides] = useState([])
  const [selectedGuide, setSelectedGuide] = useState(null)
  const [syllabuses, setSyllabuses] = useState([])
  const [showNewSyllabus, setShowNewSyllabus] = useState(false)
  const [newSyllabus, setNewSyllabus] = useState({ title: '', subject: '', semester: '', chapters: [{ unit_number: 1, title: '', description: '' }] })
  const [gaps, setGaps] = useState(null)
  const fileRef = useRef()
  const pollRef = useRef()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    fetch(`${API}/auth/me`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d) router.push('/login'); else setUser(d) })
  }, [])

  useEffect(() => {
    if (view === 'guides') loadGuides()
    if (view === 'syllabus') loadSyllabuses()
    if (view === 'upload') loadSyllabuses()
  }, [view])

  async function loadGuides() {
    const res = await fetch(`${API}/guides/`, { headers: authHeaders() })
    if (res.ok) setGuides(await res.json())
  }

  async function loadSyllabuses() {
    const res = await fetch(`${API}/syllabus/`, { headers: authHeaders() })
    if (res.ok) setSyllabuses(await res.json())
  }

  async function loadGuide(id) {
    const res = await fetch(`${API}/guides/${id}`, { headers: authHeaders() })
    if (res.ok) setSelectedGuide(await res.json())
  }

  async function loadGaps(syllabusId) {
    const res = await fetch(`${API}/syllabus/${syllabusId}/gaps`, { headers: authHeaders() })
    if (res.ok) setGaps(await res.json())
  }

  async function createSyllabus() {
    const res = await fetch(`${API}/syllabus/`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(newSyllabus),
    })
    if (res.ok) {
      setShowNewSyllabus(false)
      setNewSyllabus({ title: '', subject: '', semester: '', chapters: [{ unit_number: 1, title: '', description: '' }] })
      loadSyllabuses()
    }
  }

  function addChapter() {
    setNewSyllabus(s => ({
      ...s,
      chapters: [...s.chapters, { unit_number: s.chapters.length + 1, title: '', description: '' }]
    }))
  }

  function handleDrop(e) {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) setFile(f)
  }

  async function handleProcess() {
    if (!file) return
    setStatus('uploading'); setError(''); setGuide(null)
    const formData = new FormData()
    formData.append('file', file)
    if (subject) formData.append('subject', subject)
    try {
      const res = await fetch(`${API}/notes/process?syllabus_id=${syllabusId}`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Upload failed'); setStatus('error'); return }
      setStatus('processing')
      pollTask(data.task_id)
    } catch { setError('Upload failed.'); setStatus('error') }
  }

  function pollTask(taskId) {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/notes/status/${taskId}`, { headers: authHeaders() })
        const data = await res.json()
        if (data.status === 'processing') { setStep(data.step || ''); setPercent(data.percent || 0) }
        if (data.status === 'done') { clearInterval(pollRef.current); setStatus('done'); setGuide(data.result); setPercent(100) }
        if (data.status === 'failed') { clearInterval(pollRef.current); setError(data.error || 'Processing failed'); setStatus('error') }
      } catch { clearInterval(pollRef.current); setError('Lost connection'); setStatus('error') }
    }, 2000)
  }

  function reset() {
    clearInterval(pollRef.current)
    setFile(null); setStatus('idle'); setStep(''); setPercent(0); setGuide(null); setError('')
  }

  const stepLabels = { preprocessing: 'Cleaning image...', ocr: 'Reading notes...', matching: 'Matching syllabus...', generating: 'Generating guide...', done: 'Done' }

  if (!user) return <div className={styles.loading}><div className={styles.spinner} /></div>

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.sideTop}>
          <span className={styles.logo}>NotesGuru</span>
          <nav className={styles.nav}>
            <button className={`${styles.navItem} ${view === 'upload' ? styles.active : ''}`} onClick={() => { reset(); setView('upload') }}>
              <span className={styles.navIcon}>↑</span> Upload
            </button>
            <button className={`${styles.navItem} ${view === 'guides' ? styles.active : ''}`} onClick={() => setView('guides')}>
              <span className={styles.navIcon}>◫</span> My Guides
            </button>
            <button className={`${styles.navItem} ${view === 'syllabus' ? styles.active : ''}`} onClick={() => setView('syllabus')}>
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
          <button className={styles.signOut} onClick={() => { localStorage.removeItem('token'); router.push('/login') }}>Sign out</button>
        </div>
      </aside>

      <main className={styles.main}>

        {/* ── UPLOAD VIEW ── */}
        {view === 'upload' && status === 'idle' && (
          <div className={styles.uploadView}>
            <div className={styles.pageHeader}>
              <h1 className={styles.pageTitle}>Upload notes</h1>
              <p className={styles.pageDesc}>Photo, screenshot, or typed — anything works.</p>
            </div>
            <div
              className={`${styles.dropzone} ${dragging ? styles.dragging : ''} ${file ? styles.hasFile : ''}`}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
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
            <div className={styles.subjectRow}>
              <select
                className={styles.subjectInput}
                value={syllabusId}
                onChange={e => setSyllabusId(Number(e.target.value))}
              >
                <option value={0}>No syllabus (general)</option>
                {syllabuses.map(s => (
                  <option key={s.id} value={s.id}>{s.title} — {s.subject}</option>
                ))}
              </select>
            </div>
            <div className={styles.subjectRow}>
              <input className={styles.subjectInput} placeholder="Subject (optional) — e.g. Computer Networks" value={subject} onChange={e => setSubject(e.target.value)} />
            </div>
            <div className={styles.actions}>
              {file && <button className={styles.clearBtn} onClick={() => setFile(null)}>Remove</button>}
              <button className={styles.processBtn} onClick={handleProcess} disabled={!file}>Generate study guide →</button>
            </div>
          </div>
        )}

        {view === 'upload' && (status === 'uploading' || status === 'processing') && (
          <div className={styles.processingView}>
            <div className={styles.processingCard}>
              <div className={styles.processingIcon}><div className={styles.spinner} /></div>
              <h2 className={styles.processingTitle}>{status === 'uploading' ? 'Uploading...' : stepLabels[step] || 'Processing...'}</h2>
              <p className={styles.processingDesc}>This takes about 30 seconds. Don't close the tab.</p>
              <div className={styles.progressBar}><div className={styles.progressFill} style={{ width: `${percent}%` }} /></div>
              <div className={styles.progressSteps}>
                {['preprocessing', 'ocr', 'matching', 'generating'].map((s, i) => (
                  <div key={s} className={`${styles.progressStep} ${percent >= (i + 1) * 25 ? styles.stepDone : ''} ${step === s ? styles.stepActive : ''}`}>{stepLabels[s]}</div>
                ))}
              </div>
            </div>
          </div>
        )}

        {view === 'upload' && status === 'error' && (
          <div className={styles.errorView}>
            <div className={styles.errorCard}>
              <h2 className={styles.errorTitle}>Something went wrong</h2>
              <p className={styles.errorMsg}>{error}</p>
              <button className={styles.retryBtn} onClick={reset}>Try again</button>
            </div>
          </div>
        )}

        {view === 'upload' && status === 'done' && guide && (
          <div className={styles.guideView}>
            <div className={styles.guideHeader}>
              <div>
                <div className={styles.guideMeta}>
                  {guide.matched && <span className={styles.matchBadge}>{guide.chapter_title} · {Math.round(guide.match_score * 100)}% match</span>}
                  <span className={styles.ocrBadge}>via {guide.ocr_source}</span>
                </div>
                <h2 className={styles.guideTitle}>{guide.chapter_title || 'Study Guide'}</h2>
              </div>
              <button className={styles.newBtn} onClick={reset}>← Upload another</button>
            </div>
            <div className={`${styles.guideContent} markdown`}>
              <ReactMarkdown>{guide.guide_content}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* ── GUIDES VIEW ── */}
        {view === 'guides' && !selectedGuide && (
          <div className={styles.uploadView}>
            <div className={styles.pageHeader}>
              <h1 className={styles.pageTitle}>My Guides</h1>
              <p className={styles.pageDesc}>All your generated study guides.</p>
            </div>
            {guides.length === 0 ? (
              <div className={styles.emptyState}>
                <p className={styles.emptyText}>No guides yet.</p>
                <button className={styles.processBtn} onClick={() => setView('upload')}>Upload your first note →</button>
              </div>
            ) : (
              <div className={styles.guidesList}>
                {guides.map(g => (
                  <div key={g.id} className={styles.guideCard} onClick={() => loadGuide(g.id)}>
                    <div className={styles.guideCardTitle}>{g.title}</div>
                    <div className={styles.guideCardMeta}>{g.chapter_name} · {new Date(g.created_at).toLocaleDateString()}</div>
                    <p className={styles.guideCardPreview}>{g.content_preview}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {view === 'guides' && selectedGuide && (
          <div className={styles.guideView}>
            <div className={styles.guideHeader}>
              <div>
                <div className={styles.guideMeta}>
                  <span className={styles.ocrBadge}>{new Date(selectedGuide.created_at).toLocaleDateString()}</span>
                </div>
                <h2 className={styles.guideTitle}>{selectedGuide.title}</h2>
              </div>
              <button className={styles.newBtn} onClick={() => setSelectedGuide(null)}>← All guides</button>
            </div>
            <div className={`${styles.guideContent} markdown`}>
              <ReactMarkdown>{selectedGuide.content}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* ── SYLLABUS VIEW ── */}
        {view === 'syllabus' && (
          <div className={styles.uploadView}>
            <div className={styles.pageHeader}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h1 className={styles.pageTitle}>Syllabus</h1>
                  <p className={styles.pageDesc}>Create your syllabus so notes match the right chapters.</p>
                </div>
                <button className={styles.processBtn} onClick={() => setShowNewSyllabus(!showNewSyllabus)}>
                  {showNewSyllabus ? 'Cancel' : '+ New syllabus'}
                </button>
              </div>
            </div>

            {showNewSyllabus && (
              <div className={styles.newSyllabusForm}>
                <div className={styles.formRow}>
                  <input className={styles.subjectInput} placeholder="Syllabus title — e.g. Optimization Techniques" value={newSyllabus.title} onChange={e => setNewSyllabus(s => ({ ...s, title: e.target.value }))} />
                </div>
                <div className={styles.formRow}>
                  <input className={styles.subjectInput} placeholder="Subject" value={newSyllabus.subject} onChange={e => setNewSyllabus(s => ({ ...s, subject: e.target.value }))} />
                  <input className={styles.subjectInput} placeholder="Semester (optional)" value={newSyllabus.semester} onChange={e => setNewSyllabus(s => ({ ...s, semester: e.target.value }))} />
                </div>
                <div className={styles.aiPasteSection}>
                  <p className={styles.chaptersLabel}>✦ Paste syllabus text — AI splits into topics automatically</p>
                  <textarea
                    className={styles.syllabusTextarea}
                    placeholder="Paste your full syllabus here e.g: Unconstrained Optimization: Gradient Descent, Newton Method. Constrained Optimization: Lagrange Multipliers, KKT Conditions. Dynamic Programming: Principle of Optimality..."
                    value={newSyllabus.syllabus_text || ''}
                    onChange={e => setNewSyllabus(s => ({ ...s, syllabus_text: e.target.value }))}
                    rows={5}
                  />
                  <button
                    className={styles.aiParseBtn}
                    onClick={async () => {
                      if (!newSyllabus.title || !newSyllabus.subject || !newSyllabus.syllabus_text) return
                      setNewSyllabus(s => ({ ...s, parsing: true }))
                      try {
                        const res = await fetch(`${API}/syllabus/parse-text`, {
                          method: 'POST',
                          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
                          body: JSON.stringify({ title: newSyllabus.title, subject: newSyllabus.subject, semester: newSyllabus.semester, syllabus_text: newSyllabus.syllabus_text }),
                        })
                        if (res.ok) {
                          setShowNewSyllabus(false)
                          setNewSyllabus({ title: '', subject: '', semester: '', chapters: [{ unit_number: 1, title: '', description: '' }] })
                          loadSyllabuses()
                        }
                      } finally {
                        setNewSyllabus(s => ({ ...s, parsing: false }))
                      }
                    }}
                    disabled={!newSyllabus.title || !newSyllabus.subject || !newSyllabus.syllabus_text || newSyllabus.parsing}
                  >
                    {newSyllabus.parsing ? 'Parsing with AI...' : '✦ Parse & create with AI'}
                  </button>
                </div>
                <div className={styles.orDivider}><span>or add chapters manually</span></div>
                <div className={styles.chaptersSection}>
                  <p className={styles.chaptersLabel}>Chapters</p>
                  {newSyllabus.chapters.map((ch, i) => (
                    <div key={i} className={styles.chapterRow}>
                      <span className={styles.chapterNum}>{i + 1}</span>
                      <input className={styles.subjectInput} placeholder="Chapter title" value={ch.title} onChange={e => { const chs = [...newSyllabus.chapters]; chs[i].title = e.target.value; setNewSyllabus(s => ({ ...s, chapters: chs })) }} />
                      <input className={styles.subjectInput} placeholder="Description (optional)" value={ch.description} onChange={e => { const chs = [...newSyllabus.chapters]; chs[i].description = e.target.value; setNewSyllabus(s => ({ ...s, chapters: chs })) }} />
                    </div>
                  ))}
                  <button className={styles.addChapterBtn} onClick={addChapter}>+ Add chapter</button>
                </div>
                <div className={styles.actions}>
                  <button className={styles.processBtn} onClick={createSyllabus} disabled={!newSyllabus.title || !newSyllabus.subject}>Create syllabus manually</button>
                </div>
              </div>
            )}


            {syllabuses.length === 0 && !showNewSyllabus ? (
              <div className={styles.emptyState}>
                <p className={styles.emptyText}>No syllabuses yet.</p>
                <button className={styles.processBtn} onClick={() => setShowNewSyllabus(true)}>Create your first syllabus →</button>
              </div>
            ) : (
              <div className={styles.syllabusCards}>
                {syllabuses.map(s => (
                  <div key={s.id} className={styles.syllabusCard}>
                    <div className={styles.syllabusCardHeader}>
                      <div>
                        <div className={styles.syllabusCardTitle}>{s.title}</div>
                        <div className={styles.syllabusCardMeta}>{s.subject} {s.semester && `· ${s.semester}`} · {s.chapter_count} chapters</div>
                      </div>
                      <button className={styles.gapBtn} onClick={() => loadGaps(s.id)}>View gaps</button>
                    </div>
                    <div className={styles.chapterList}>
                      {s.chapters.map(c => (
                        <div key={c.id} className={styles.chapterItem}>
                          <span className={styles.chapterItemNum}>U{c.unit_number}</span>
                          <span className={styles.chapterItemTitle}>{c.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {gaps && (
              <div className={styles.gapsPanel}>
                <div className={styles.gapsPanelHeader}>
                  <h3 className={styles.gapsPanelTitle}>Coverage Analysis</h3>
                  <button className={styles.clearBtn} onClick={() => setGaps(null)}>Close</button>
                </div>
                <div className={styles.coverageStat}>
                  <span className={styles.coverageNum}>{gaps.coverage_percent}%</span>
                  <span className={styles.coverageLabel}>covered — {gaps.covered_count} of {gaps.total_chapters} chapters</span>
                </div>
                <div className={styles.coverageBar}>
                  <div className={styles.coverageFill} style={{ width: `${gaps.coverage_percent}%` }} />
                </div>
                {gaps.gap_chapters.length > 0 && (
                  <div className={styles.gapList}>
                    <p className={styles.gapListLabel}>Missing coverage:</p>
                    {gaps.gap_chapters.map(c => (
                      <div key={c.id} className={styles.gapItem}>⚠ {c.title}</div>
                    ))}
                  </div>
                )}
                {gaps.covered_chapters.length > 0 && (
                  <div className={styles.gapList}>
                    <p className={styles.gapListLabel}>Covered:</p>
                    {gaps.covered_chapters.map(c => (
                      <div key={c.id} className={styles.coveredItem}>✓ {c.title}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}