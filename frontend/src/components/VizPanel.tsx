import { BarChart2, TrendingUp, PieChart } from 'lucide-react'

const mockCharts = [
  {
    title: 'Revenue by Quarter',
    icon: BarChart2,
    color: 'indigo',
    bars: [60, 72, 55, 91],
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
  },
  {
    title: 'Customer Segments',
    icon: PieChart,
    color: 'purple',
    bars: [61, 27, 12],
    labels: ['Top 12%', 'Mid 30%', 'Long tail'],
  },
  {
    title: 'Retention Trend',
    icon: TrendingUp,
    color: 'emerald',
    bars: [70, 73, 68, 79, 82, 88],
    labels: ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  },
]

export default function VizPanel() {
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Analysis Results</h2>
          <p className="text-slate-500 mt-1">Interactive visualizations from your data analysis</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {mockCharts.map((chart) => {
            const Icon = chart.icon
            const max = Math.max(...chart.bars)
            return (
              <div key={chart.title} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <Icon size={16} className={`text-${chart.color}-500`} />
                  <span className="font-semibold text-slate-700 text-sm">{chart.title}</span>
                </div>
                <div className="flex items-end gap-2 h-24">
                  {chart.bars.map((val, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full rounded-t bg-${chart.color}-400 transition-all`}
                        style={{ height: `${(val / max) * 80}px` }}
                      />
                      <span className="text-xs text-slate-400">{chart.labels[i]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-6 bg-indigo-50 border border-indigo-200 rounded-xl p-5">
          <p className="text-sm text-indigo-800 font-medium">
            Interactive charts powered by real analysis data will appear here in the next phase.
            Connect Recharts or Chart.js to the finding nodes from the analysis stream.
          </p>
        </div>
      </div>
    </div>
  )
}
