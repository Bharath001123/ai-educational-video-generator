type Props = {
  title: string
  value: string | number
  icon?: React.ReactNode
}

export default function StatisticCard({ title, value, icon }: Props) {
  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 shadow-xl hover:shadow-2xl transition-shadow flex items-center">
      {icon && <div className="mr-4 text-brand-400 text-3xl">{icon}</div>}
      <div>
        <p className="text-sm text-slate-400">{title}</p>
        <p className="text-2xl font-semibold text-white">{value}</p>
      </div>
    </div>
  )
}
