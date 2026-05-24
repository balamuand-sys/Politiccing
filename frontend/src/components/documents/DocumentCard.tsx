import { useNavigate } from 'react-router-dom'
import { FileText, Calendar, Building2 } from 'lucide-react'
import { formatDate, docTypeLabel, docTypeBadgeColor, truncate, cn } from '@/lib/utils'

interface DocumentCardProps {
  doc: {
    id: number
    title: string
    meeting_date?: string
    committee?: string
    document_type?: string
    source?: string
    created_at: string
  }
}

export default function DocumentCard({ doc }: DocumentCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/documents/${doc.id}`)}
      className="card p-4 cursor-pointer hover:shadow-md hover:border-hoyre-blue/40 transition-all group"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-hoyre-blue-pale dark:bg-hoyre-blue/20 rounded-lg flex-shrink-0 group-hover:bg-hoyre-blue/20">
          <FileText size={18} className="text-hoyre-blue dark:text-blue-300" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-sm leading-snug line-clamp-2 group-hover:text-hoyre-blue dark:group-hover:text-blue-300 transition-colors">
            {doc.title}
          </h3>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {doc.document_type && (
              <span className={cn('badge', docTypeBadgeColor(doc.document_type))}>
                {docTypeLabel(doc.document_type)}
              </span>
            )}
            {doc.source === 'scrape' && (
              <span className="badge bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
                Skrapet
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
            {doc.meeting_date && (
              <span className="flex items-center gap-1">
                <Calendar size={11} />
                {formatDate(doc.meeting_date)}
              </span>
            )}
            {doc.committee && (
              <span className="flex items-center gap-1">
                <Building2 size={11} />
                {truncate(doc.committee, 40)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
