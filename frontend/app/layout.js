import './globals.css'

export const metadata = {
  title: 'NotesGuru — Study smarter',
  description: 'Turn handwritten notes into exam-ready study guides',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}