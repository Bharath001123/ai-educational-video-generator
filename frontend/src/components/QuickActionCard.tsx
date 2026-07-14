import { NavLink } from 'react-router-dom'

type Props = {
  title: string
  description?: string
  to: string
  bgColor: string // Tailwind bg class, e.g., 'bg-brand-600'
}

export default function QuickActionCard({ title, description, to, bgColor }: Props) {
  return (
    <NavLink
      to={to}
      className={`flex flex-col justify-between p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-shadow ${bgColor} hover:opacity-90`}
    >
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      {description && <p className="text-sm opacity-80">{description}</p>}
    </NavLink>
  )
}
