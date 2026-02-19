import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './contexts/ToastContext'
import Toast from './components/Toast'
import SearchPage from './pages/SearchPage'
import AdminLogin from './pages/AdminLogin'
import AdminPanel from './pages/AdminPanel'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ToastProvider>
      <BrowserRouter>
        <Toast />
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  </React.StrictMode>,
)
