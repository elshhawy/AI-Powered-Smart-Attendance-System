import { useState, useRef, useCallback } from 'react'
import Webcam from 'react-webcam'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera as CameraIcon, Upload, CheckCircle, XCircle, Clock, RefreshCw, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { processFrame } from '../api'

const KIOSK_KEY = import.meta.env.VITE_KIOSK_KEY || 'kiosk-secret-key-change-this-in-production-123'

export default function Camera() {
  const webcamRef = useRef(null)
  const [mode, setMode] = useState('upload') // 'webcam' | 'upload'
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)

  const process = async (file) => {
    setProcessing(true)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('frame', file)
      const { data } = await processFrame(fd)
      setResult(data)
    } catch (e) {
      const msg = e.response?.data?.detail || 'Processing failed'
      toast.error(msg)
      setResult({ error: msg })
    } finally {
      setProcessing(false)
    }
  }

  const handleUpload = (e) => {
    const f = e.target.files[0]
    if (!f) return
    setPreview(URL.createObjectURL(f))
    process(f)
  }

  const handleCapture = useCallback(() => {
    const img = webcamRef.current?.getScreenshot()
    if (!img) return
    setPreview(img)
    fetch(img).then(r => r.blob()).then(b => process(new File([b], 'capture.jpg', { type: 'image/jpeg' })))
  }, [webcamRef])

  const reset = () => { setResult(null); setPreview(null) }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto">
      <div>
        <h1 className="page-title">Camera</h1>
        <p className="page-subtitle mt-1">Record attendance via face recognition</p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-2 p-1 bg-surface-900 rounded-xl border border-surface-800 w-fit">
        {[['upload','Upload Photo'],['webcam','Live Camera']].map(([m, l]) => (
          <button
            key={m}
            onClick={() => { setMode(m); reset() }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              mode === m ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Camera/Upload */}
        <div className="card p-6 flex flex-col gap-4">
          {mode === 'upload' ? (
            <>
              <label className="flex flex-col items-center justify-center h-56 border-2 border-dashed border-surface-700 rounded-xl cursor-pointer hover:border-primary-500/50 transition-all overflow-hidden">
                {preview ? (
                  <img src={preview} className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center gap-3 text-slate-500">
                    <Upload size={32} />
                    <div className="text-center">
                      <p className="text-sm font-medium text-slate-400">Upload a photo</p>
                      <p className="text-xs mt-1">JPG, PNG supported</p>
                    </div>
                  </div>
                )}
                <input type="file" accept="image/*" className="hidden" onChange={handleUpload} />
              </label>
              {preview && (
                <button onClick={reset} className="btn-secondary text-sm flex items-center justify-center gap-2">
                  <RefreshCw size={14} /> Try Another
                </button>
              )}
            </>
          ) : (
            <>
              <div className="rounded-xl overflow-hidden bg-black h-56">
                <Webcam ref={webcamRef} screenshotFormat="image/jpeg" className="w-full h-full object-cover" />
              </div>
              <button
                onClick={handleCapture}
                disabled={processing}
                className="btn-primary flex items-center justify-center gap-2 py-3"
              >
                {processing ? <Loader2 size={16} className="animate-spin" /> : <><CameraIcon size={16} /> Capture & Process</>}
              </button>
            </>
          )}
        </div>

        {/* Right: Result */}
        <div className="card p-6 flex flex-col items-center justify-center">
          <AnimatePresence mode="wait">
            {processing ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center space-y-4">
                <div className="w-16 h-16 rounded-full border-4 border-primary-500/30 border-t-primary-500 animate-spin mx-auto" />
                <p className="text-slate-400 text-sm">Analyzing face...</p>
              </motion.div>
            ) : result && !result.error ? (
              <motion.div key="result" initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-center space-y-4">
                {result.already_marked ? (
                  <Clock size={48} className="text-amber-400 mx-auto" />
                ) : result.is_late ? (
                  <Clock size={48} className="text-amber-400 mx-auto" />
                ) : (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: [0, 1.2, 1] }}
                    transition={{ duration: 0.5 }}
                  >
                    <CheckCircle size={56} className="text-emerald-400 mx-auto" />
                  </motion.div>
                )}
                <div>
                  <p className="text-xl font-bold text-slate-100">{result.student_name}</p>
                  <p className="text-sm text-slate-400 mt-1">{result.message}</p>
                </div>
                <div className="flex gap-3 justify-center">
                  <span className={result.is_late ? 'badge-late' : 'badge-present'}>
                    {result.is_late ? 'Late' : 'On Time'}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-surface-800 text-slate-400">
                    {Math.round(result.confidence * 100)}% confidence
                  </span>
                </div>
                <button onClick={reset} className="btn-secondary text-sm mt-2">
                  Next Student
                </button>
              </motion.div>
            ) : result?.error ? (
              <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-3">
                <XCircle size={48} className="text-red-400 mx-auto" />
                <p className="text-red-400 text-sm font-medium">{result.error}</p>
                <button onClick={reset} className="btn-secondary text-sm">Try Again</button>
              </motion.div>
            ) : (
              <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-3">
                <CameraIcon size={48} className="text-slate-700 mx-auto" />
                <p className="text-slate-500 text-sm">Upload or capture a photo<br />to record attendance</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
