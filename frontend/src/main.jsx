import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import BackendTest from './BackendTest.jsx' 

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BackendTest />
  </StrictMode>,
)