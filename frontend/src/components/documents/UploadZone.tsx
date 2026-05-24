import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface UploadZoneProps {
  onUploaded: () => void
  onClose: () => void
}

export default function UploadZone({ onUploaded, onClose }: UploadZoneProps) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return
    const file = acceptedFiles[0]
    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
    } catch (e: unknown) {
      setError((e as Error).message || 'Opplasting feilet')
    } finally {
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  })

  if (result) {
    return (
      <div className="p-6 space-y-4">
        <div className="flex items-center gap-3 text-green-600 dark:text-green-400">
          <CheckCircle size={24} />
          <span className="font-medium">Dokument lastet opp</span>
        </div>
        <div className="card p-4 space-y-2 text-sm">
          <div><span className="text-gray-500">Tittel:</span> <strong>{result.title as string}</strong></div>
          {result.meeting_date && (
            <div><span className="text-gray-500">Møtedato:</span> {result.meeting_date as string}</div>
          )}
          {result.committee && (
            <div><span className="text-gray-500">Utvalg:</span> {result.committee as string}</div>
          )}
          {result.document_type && (
            <div><span className="text-gray-500">Type:</span> {result.document_type as string}</div>
          )}
        </div>
        <div className="flex gap-3">
          <button
            className="btn-primary"
            onClick={() => { onUploaded(); onClose() }}
          >
            Gå til dokumentbibliotek
          </button>
          <button className="btn-secondary" onClick={() => setResult(null)}>
            Last opp nytt
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Last opp PDF</h2>
        <button onClick={onClose} className="btn-ghost p-1">
          <X size={18} />
        </button>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-hoyre-blue bg-hoyre-blue-pale dark:bg-hoyre-blue/10'
            : 'border-gray-300 dark:border-gray-600 hover:border-hoyre-blue hover:bg-gray-50 dark:hover:bg-gray-800',
          uploading && 'pointer-events-none opacity-60',
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3 text-gray-500 dark:text-gray-400">
          {uploading ? (
            <>
              <div className="w-10 h-10 border-2 border-hoyre-blue border-t-transparent rounded-full animate-spin" />
              <p className="text-sm">Analyserer dokument med AI...</p>
            </>
          ) : (
            <>
              <Upload size={36} className={isDragActive ? 'text-hoyre-blue' : ''} />
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">
                  {isDragActive ? 'Slipp filen her' : 'Dra og slipp PDF her'}
                </p>
                <p className="text-sm mt-1">eller klikk for å velge fil</p>
              </div>
              <div className="flex items-center gap-2 text-xs bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full">
                <FileText size={12} />
                Kun PDF-filer
              </div>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <p className="text-xs text-gray-500">
        Dokumentet analyseres automatisk med AI for å ekstrahere tittel, dato, utvalg og type.
      </p>
    </div>
  )
}
