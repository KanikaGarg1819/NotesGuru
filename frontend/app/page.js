'use client'
import Link from 'next/link'
import styles from './page.module.css'

export default function Home() {
  return (
    <main className={styles.main}>
      <nav className={styles.nav}>
        <span className={styles.logo}>NotesGuru</span>
        <div className={styles.navLinks}>
          <Link href="/login" className={styles.navLink}>Sign in</Link>
          <Link href="/signup" className={styles.navBtn}>Get started</Link>
        </div>
      </nav>

      <section className={styles.hero}>
        <div className={styles.eyebrow}>AI-powered study portal</div>
        <h1 className={styles.headline}>
          Your notes,<br />
          <em>exam-ready.</em>
        </h1>
        <p className={styles.sub}>
          Upload a photo of your handwritten notes. NotesGuru maps them to your syllabus,
          finds what you haven't covered, and generates a structured study guide — instantly.
        </p>
        <div className={styles.heroActions}>
          <Link href="/signup" className={styles.primaryBtn}>Start for free</Link>
          <Link href="/login" className={styles.ghostBtn}>I already have an account</Link>
        </div>
      </section>

      <section className={styles.steps}>
        <div className={styles.step}>
          <div className={styles.stepNum}>01</div>
          <div className={styles.stepText}>
            <h3>Upload your notes</h3>
            <p>Photo, screenshot, or typed — any format works.</p>
          </div>
        </div>
        <div className={styles.stepDivider} />
        <div className={styles.step}>
          <div className={styles.stepNum}>02</div>
          <div className={styles.stepText}>
            <h3>Map to syllabus</h3>
            <p>Each note is matched to the right chapter automatically.</p>
          </div>
        </div>
        <div className={styles.stepDivider} />
        <div className={styles.step}>
          <div className={styles.stepNum}>03</div>
          <div className={styles.stepText}>
            <h3>Get your guide</h3>
            <p>Clean notes, definitions, exam tips, practice questions.</p>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        Built for students who study late.
      </footer>
    </main>
  )
}