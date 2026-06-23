import React from 'react'
import ReactDOM from 'react-dom/client'
import { appRenderDebug } from './utils/logger'

appRenderDebug('Mounting IOPHA application root')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <h1>IOPHA - Interactive Obesity Prevention Health Assistant</h1>
  </React.StrictMode>
)