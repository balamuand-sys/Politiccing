import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import DocumentLibrary from '@/pages/DocumentLibrary'
import DocumentDetail from '@/pages/DocumentDetail'
import Memory from '@/pages/Memory'
import Settings from '@/pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DocumentLibrary />} />
          <Route path="documents/:id" element={<DocumentDetail />} />
          <Route path="memory" element={<Memory />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
