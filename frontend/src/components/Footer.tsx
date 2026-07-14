function Footer() {
  return (
    <footer className="border-t border-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
        <p>&copy; {new Date().getFullYear()} AI Educational Video Generator</p>
        <p>AI-Based Automated Educational Video Generation System</p>
      </div>
    </footer>
  )
}

export default Footer
