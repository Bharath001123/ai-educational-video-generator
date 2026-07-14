type Props = {
  children: React.ReactNode
  onClose: () => void
}

export default function Modal({ children, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-900 rounded-xl shadow-xl max-w-3xl w-full mx-4 p-6" onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}
