import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Calendar, Building2, FileText, Tag } from 'lucide-react'
import * as Tabs from '@radix-ui/react-tabs'
import { api } from '@/lib/api'
import { formatDate, docTypeLabel, docTypeBadgeColor, cn } from '@/lib/utils'
import SummaryPanel from '@/components/ai/SummaryPanel'
import ContentGenerator from '@/components/ai/ContentGenerator'
import EnrichmentPanel from '@/components/ai/EnrichmentPanel'

interface Document {
  id: number
  title: string
  meeting_date?: string
  committee?: string
  document_type?: string
  source?: string
  raw_text?: string
  created_at: string
}

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [doc, setDoc] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const docId = Number(id)

  useEffect(() => {
    if (!docId) return
    api.get(`/documents/${docId}`)
      .then((r) => setDoc(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [docId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-hoyre-blue border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !doc) {
    return (
      <div className="p-6">
        <button className="btn-ghost mb-4" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Tilbake
        </button>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-red-700 dark:text-red-300">
          {error || 'Dokumentet ble ikke funnet'}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4 flex-shrink-0">
        <button className="btn-ghost mb-2 -ml-2" onClick={() => navigate(-1)}>
          <ArrowLeft size={15} />
          Tilbake
        </button>
        <h1 className="text-lg font-bold leading-snug">{doc.title}</h1>
        <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
          {doc.document_type && (
            <span className={cn('badge', docTypeBadgeColor(doc.document_type))}>
              <Tag size={10} className="mr-1" />
              {docTypeLabel(doc.document_type)}
            </span>
          )}
          {doc.meeting_date && (
            <span className="flex items-center gap-1">
              <Calendar size={13} />
              {formatDate(doc.meeting_date)}
            </span>
          )}
          {doc.committee && (
            <span className="flex items-center gap-1">
              <Building2 size={13} />
              {doc.committee}
            </span>
          )}
          {doc.source && (
            <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">
              {doc.source === 'upload' ? 'Opplastet' : 'Skrapet'}
            </span>
          )}
        </div>
      </div>

      {/* Split view */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: raw text */}
        <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-6">
          <div className="flex items-center gap-2 mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">
            <FileText size={15} />
            Originaltekst
          </div>
          {doc.raw_text ? (
            <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">
              {doc.raw_text}
            </pre>
          ) : (
            <p className="text-sm text-gray-400">Ingen tekst tilgjengelig</p>
          )}
        </div>

        {/* Right: AI panel */}
        <div className="w-1/2 overflow-y-auto">
          <Tabs.Root defaultValue="summary" className="flex flex-col h-full">
            <Tabs.List className="flex border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex-shrink-0 px-6">
              {[
                { value: 'summary', label: 'Oppsummering' },
                { value: 'tale', label: 'Tale' },
                { value: 'leserinnlegg', label: 'Leserinnlegg' },
                { value: 'enrichments', label: 'Berikelser' },
              ].map(({ value, label }) => (
                <Tabs.Trigger
                  key={value}
                  value={value}
                  className={cn(
                    'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                    'data-[state=active]:border-hoyre-blue data-[state=active]:text-hoyre-blue',
                    'data-[state=inactive]:border-transparent data-[state=inactive]:text-gray-500 data-[state=inactive]:hover:text-gray-700 dark:data-[state=inactive]:hover:text-gray-300',
                  )}
                >
                  {label}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <div className="flex-1 overflow-y-auto p-6">
              <Tabs.Content value="summary">
                <SummaryPanel documentId={docId} />
              </Tabs.Content>
              <Tabs.Content value="tale">
                <ContentGenerator documentId={docId} contentType="tale" />
              </Tabs.Content>
              <Tabs.Content value="leserinnlegg">
                <ContentGenerator documentId={docId} contentType="leserinnlegg" />
              </Tabs.Content>
              <Tabs.Content value="enrichments">
                <EnrichmentPanel documentId={docId} />
              </Tabs.Content>
            </div>
          </Tabs.Root>
        </div>
      </div>
    </div>
  )
}
