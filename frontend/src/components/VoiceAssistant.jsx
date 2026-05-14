import { useRef, useState, useEffect } from 'react'
import axios from 'axios'
import { Mic, Square, Activity, Sparkles, BrainCircuit, HeartPulse, Zap } from 'lucide-react'

// ─── Credits Tracker ────────────────────────────────────────────────
const DAILY_REQUEST_LIMIT = 100

function getUsageData() {
    const today = new Date().toISOString().split('T')[0]
    const stored = JSON.parse(localStorage.getItem('groq_usage') || '{}')
    if (stored.date !== today) {
        const fresh = { date: today, requests: 0 }
        localStorage.setItem('groq_usage', JSON.stringify(fresh))
        return fresh
    }
    return stored
}

function incrementUsage() {
    const usage = getUsageData()
    usage.requests = (usage.requests || 0) + 1
    localStorage.setItem('groq_usage', JSON.stringify(usage))
    return usage
}

function CreditsBar({ requests }) {
    const used = requests || 0
    const remaining = Math.max(0, DAILY_REQUEST_LIMIT - used)
    const pct = Math.max(0, Math.min(100, (remaining / DAILY_REQUEST_LIMIT) * 100))

    const barColor = pct > 50 ? 'from-emerald-400 to-green-500'
        : pct > 20 ? 'from-amber-400 to-yellow-500'
        : 'from-red-400 to-rose-500'
    const textColor = pct > 50 ? 'text-emerald-600' : pct > 20 ? 'text-amber-600' : 'text-rose-600'
    const bgColor = pct > 50 ? 'bg-emerald-50 border-emerald-200' : pct > 20 ? 'bg-amber-50 border-amber-200' : 'bg-rose-50 border-rose-200'

    return (
        <div className={`relative z-10 mb-6 p-4 rounded-2xl border ${bgColor}`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Zap className={`w-4 h-4 ${textColor}`} />
                    <span className={`text-xs font-bold uppercase tracking-wider ${textColor}`}>Groq API Credits</span>
                </div>
                <span className={`text-sm font-bold ${textColor}`}>{pct.toFixed(0)}% remaining</span>
            </div>
            <div className="w-full h-2.5 bg-white/60 rounded-full overflow-hidden border border-white/80">
                <div className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700 ease-out`}
                    style={{ width: `${pct}%` }} />
            </div>
            <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-slate-400">{used} requests used today</span>
                <span className="text-xs text-slate-400">~{remaining} remaining</span>
            </div>
        </div>
    )
}

// ─── Audio Analysis via Web Audio API ───────────────────────────────
// Extracts real voice features (volume, pitch, trembling) from the mic stream
// These are sent to the backend so the AI truly understands the voice state
function analyzeAudioStream(stream, onFeatures) {
    const ctx = new AudioContext()
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 2048
    const source = ctx.createMediaStreamSource(stream)
    source.connect(analyser)

    const bufferLen = analyser.frequencyBinCount
    const freqData = new Uint8Array(bufferLen)
    const timeData = new Uint8Array(analyser.fftSize)

    const volumeSamples = []
    const pitchSamples = []

    const interval = setInterval(() => {
        analyser.getByteFrequencyData(freqData)
        analyser.getByteTimeDomainData(timeData)

        // RMS Volume
        const rms = Math.sqrt(freqData.reduce((sum, v) => sum + v * v, 0) / freqData.length)
        volumeSamples.push(rms)

        // Spectral centroid (rough pitch feel)
        const totalPower = freqData.reduce((s, v) => s + v, 0) + 0.001
        const centroid = freqData.reduce((s, v, i) => s + v * i, 0) / totalPower
        pitchSamples.push(centroid)
    }, 80)

    const stop = () => {
        clearInterval(interval)
        ctx.close()

        if (volumeSamples.length < 2) return null

        const avgVol = volumeSamples.reduce((a, b) => a + b, 0) / volumeSamples.length
        const volVariance = volumeSamples.reduce((s, v) => s + Math.pow(v - avgVol, 2), 0) / volumeSamples.length
        const volStdDev = Math.sqrt(volVariance)

        const avgPitch = pitchSamples.reduce((a, b) => a + b, 0) / pitchSamples.length
        const pitchVariance = pitchSamples.reduce((s, v) => s + Math.pow(v - avgPitch, 2), 0) / pitchSamples.length
        const pitchStdDev = Math.sqrt(pitchVariance)

        const loudness = avgVol / 255
        const jitter = volStdDev / 255  // High = trembling, crying, unstable

        // Voice state descriptions for the AI
        const isTrembling = volStdDev > 18
        const isSinging = pitchStdDev > 30 && avgVol > 40
        const isCrying = volStdDev > 15 && pitchStdDev > 20 && avgVol > 20
        const isWhispering = avgVol < 15
        const isShakingVoice = volStdDev > 25

        let voiceDescription = []
        if (isSinging) voiceDescription.push('melodic/singing voice pattern with wide pitch variation')
        if (isCrying) voiceDescription.push('crying or tearful — irregular volume with unstable pitch')
        if (isTrembling) voiceDescription.push('trembling or shaking voice — high amplitude instability')
        if (isWhispering) voiceDescription.push('very quiet, almost whispering')
        if (isShakingVoice) voiceDescription.push('severely unstable voice suggesting strong emotion')
        if (voiceDescription.length === 0) voiceDescription.push('stable and composed voice')

        const features = {
            pitch_mean: parseFloat((avgPitch * 0.5).toFixed(2)),  // scale to Hz-like range
            jitter: parseFloat(jitter.toFixed(4)),
            loudness: parseFloat(loudness.toFixed(4)),
            volume_std_dev: parseFloat(volStdDev.toFixed(2)),
            pitch_std_dev: parseFloat(pitchStdDev.toFixed(2)),
            is_trembling: isTrembling,
            is_singing: isSinging,
            is_crying: isCrying,
            is_whispering: isWhispering,
            voice_description: voiceDescription.join('; ')
        }

        onFeatures(features)
        return features
    }

    return stop
}

// ─── Main Component ──────────────────────────────────────────────────
export default function VoiceAssistant() {
    const mediaRecorderRef = useRef(null)
    const streamRef = useRef(null)           // Keep stream reference to stop mic properly
    const audioChunksRef = useRef([])
    const stopAudioAnalysisRef = useRef(null)
    const audioFeaturesRef = useRef(null)

    const [recording, setRecording] = useState(false)
    const [transcript, setTranscript] = useState('')
    const [emotionData, setEmotionData] = useState(null)
    const [response, setResponse] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [requests, setRequests] = useState(0)
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [selectedVoice, setSelectedVoice] = useState('Rachel')
    const [previewLoading, setPreviewLoading] = useState(false)

    const voices = [
        { name: 'Amelia', gender: 'female', icon: '👩‍💼' },
        { name: 'Rachel', gender: 'female', icon: '👩' },
        { name: 'Josh', gender: 'male', icon: '🧔' },
        { name: 'Nathan', gender: 'male', icon: '👨' },
        { name: 'Sam', gender: 'male', icon: '🧑' },
    ]

    useEffect(() => {
        const usage = getUsageData()
        setRequests(usage.requests || 0)
    }, [])

    // ── Preview Voice ──
    const previewVoice = async () => {
        setPreviewLoading(true)
        try {
            const formData = new FormData()
            formData.append('voice_name', selectedVoice)
            const res = await axios.post('http://localhost:8000/preview-voice', formData)
            if (res.data.audio_url) {
                const audio = new Audio(res.data.audio_url)
                audio.play()
            }
        } catch (err) {
            console.error("Preview failed", err)
        }
        setPreviewLoading(false)
    }

    // ── Web Speech API TTS — browser fallback ──
    const speakResponse = (text) => {
        if (!window.speechSynthesis) return
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(text)
        const voices = window.speechSynthesis.getVoices()
        const femaleVoice = voices.find(v =>
            v.name.toLowerCase().includes('samantha') ||
            v.name.toLowerCase().includes('karen') ||
            v.name.toLowerCase().includes('victoria') ||
            v.name.toLowerCase().includes('zira') ||
            v.name.toLowerCase().includes('female') ||
            (v.lang.startsWith('en') && v.name.toLowerCase().includes('google'))
        )
        if (femaleVoice) utterance.voice = femaleVoice
        utterance.rate = 0.92
        utterance.pitch = 1.1
        utterance.volume = 1.0
        utterance.onstart = () => setIsSpeaking(true)
        utterance.onend = () => setIsSpeaking(false)
        utterance.onerror = () => setIsSpeaking(false)
        window.speechSynthesis.speak(utterance)
    }

    // ── Start Recording ──
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            streamRef.current = stream  // save so we can stop all tracks later

            const mediaRecorder = new MediaRecorder(stream)
            mediaRecorderRef.current = mediaRecorder
            audioChunksRef.current = []
            audioFeaturesRef.current = null

            // Start real-time audio feature analysis
            stopAudioAnalysisRef.current = analyzeAudioStream(stream, (features) => {
                audioFeaturesRef.current = features
            })

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data)
            }

            mediaRecorder.onstop = async () => {
                // IMPORTANT: Stop all mic tracks so the browser mic indicator turns off
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(track => track.stop())
                    streamRef.current = null
                }

                // Stop audio analysis and get computed features
                if (stopAudioAnalysisRef.current) {
                    stopAudioAnalysisRef.current()
                    stopAudioAnalysisRef.current = null
                }

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
                const formData = new FormData()
                formData.append('file', audioBlob, 'recording.webm')

                // Attach real voice features computed by Web Audio API
                if (audioFeaturesRef.current) {
                    formData.append('audio_analysis', JSON.stringify(audioFeaturesRef.current))
                }
                formData.append('voice_name', selectedVoice)

                setLoading(true)
                setError('')

                try {
                    const res = await axios.post('http://localhost:8000/process-voice', formData, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    })

                    setTranscript(res.data.transcript)
                    setEmotionData(res.data.emotion)
                    setResponse(res.data.response)

                    const updated = incrementUsage()
                    setRequests(updated.requests)

                    // Try ElevenLabs backend audio first — most human
                    if (res.data.audio_url) {
                        const audio = new Audio(res.data.audio_url)
                        audio.onplay = () => setIsSpeaking(true)
                        audio.onended = () => setIsSpeaking(false)
                        audio.onerror = () => speakResponse(res.data.response)
                        audio.play().catch(() => speakResponse(res.data.response))
                    } else {
                        speakResponse(res.data.response)
                    }
                } catch (err) {
                    console.error(err)
                    setError(err.response?.data?.detail || 'Failed to process voice. Is the backend running?')
                }

                setLoading(false)
            }

            mediaRecorder.start(250)  // Collect data every 250ms for better chunks
            setRecording(true)
        } catch (err) {
            setError('Microphone access denied. Please allow microphone access and try again.')
        }
    }

    // ── Stop Recording ──
    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop()
        }
        setRecording(false)
    }

    const emotion = emotionData?.emotion || ''
    const contradiction = emotionData?.contradiction_detected
    const hiddenEmotion = emotionData?.hidden_emotion

    return (
        <div className="w-full max-w-2xl relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300 rounded-[2.5rem] blur opacity-40"></div>

            <div className="relative bg-white/70 backdrop-blur-2xl rounded-3xl p-8 sm:p-10 shadow-2xl border border-white/50 overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>

                {/* Header */}
                <div className="text-center mb-8 relative z-10">
                    <div className="inline-flex items-center justify-center p-3 bg-indigo-50 rounded-2xl mb-4 border border-indigo-100 shadow-sm">
                        <BrainCircuit className="text-indigo-600 w-8 h-8" />
                    </div>
                    <h1 className="text-4xl sm:text-5xl font-extrabold mb-3 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-700 via-purple-700 to-indigo-700">
                        NeuroNest AI
                    </h1>
                    <p className="text-indigo-900/60 font-medium text-lg flex items-center justify-center gap-2">
                        <Sparkles className="w-4 h-4 text-pink-500" />
                        Emotionally-aware voice assistant
                        <Sparkles className="w-4 h-4 text-pink-500" />
                    </p>
                </div>

                {/* Credits Bar */}
                <CreditsBar requests={requests} />

                {/* Voice Selection Dropdown */}
                <div className="relative z-10 mb-8 bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100/50">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex-1">
                            <label className="block text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-1.5 ml-1">
                                Choose AI Voice Model
                            </label>
                            <div className="relative">
                                <select 
                                    value={selectedVoice}
                                    onChange={(e) => setSelectedVoice(e.target.value)}
                                    className="w-full bg-white border border-indigo-200 text-indigo-900 text-sm rounded-xl focus:ring-indigo-500 focus:border-indigo-500 block p-3 shadow-sm appearance-none cursor-pointer hover:border-indigo-300 transition-colors"
                                >
                                    {voices.map(v => (
                                        <option key={v.name} value={v.name}>
                                            {v.icon} {v.name} ({v.gender})
                                        </option>
                                    ))}
                                </select>
                                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-indigo-400">
                                    <Zap size={14} />
                                </div>
                            </div>
                        </div>
                        <button 
                            onClick={previewVoice}
                            disabled={previewLoading}
                            className={`mt-5 px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition-all flex items-center gap-2 shadow-sm
                                ${previewLoading 
                                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                                    : 'bg-white text-indigo-600 border border-indigo-100 hover:bg-indigo-50 hover:scale-105 active:scale-95'
                                }`}
                        >
                            {previewLoading ? (
                                <Activity className="w-3 h-3 animate-spin" />
                            ) : (
                                <Sparkles className="w-3 h-3" />
                            )}
                            Preview
                        </button>
                    </div>
                </div>

                {/* Mic Button */}
                <div className="flex justify-center mb-8 relative z-10">
                    <div className="relative">
                        {recording && (
                            <div className="absolute -inset-4 bg-red-400/30 rounded-full blur-xl animate-pulse"></div>
                        )}
                        {!recording ? (
                            <button onClick={startRecording}
                                className="relative bg-gradient-to-b from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 p-8 rounded-full transition-all duration-300 shadow-[0_10px_40px_rgba(99,102,241,0.3)] hover:shadow-[0_10px_60px_rgba(99,102,241,0.5)] hover:scale-105">
                                <Mic size={40} className="text-white drop-shadow-sm" />
                            </button>
                        ) : (
                            <button onClick={stopRecording}
                                className="relative bg-gradient-to-b from-red-500 to-rose-600 hover:from-red-400 hover:to-rose-500 p-8 rounded-full transition-all duration-300 shadow-[0_10px_40px_rgba(239,68,68,0.4)] animate-pulse">
                                <Square size={40} className="text-white fill-white drop-shadow-sm" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Status Label */}
                <div className="text-center mb-6 text-sm text-indigo-400 font-medium">
                    {recording ? '🔴 Recording — speak freely, then click stop' : '🎙️ Click mic to start'}
                </div>

                {/* Loading */}
                {loading && (
                    <div className="flex flex-col items-center justify-center text-indigo-600 mb-8 space-y-4 animate-pulse">
                        <Activity className="w-8 h-8 text-indigo-500" />
                        <span className="font-medium tracking-wide">Analyzing your voice & emotion...</span>
                    </div>
                )}

                {/* Speaking Indicator */}
                {isSpeaking && !loading && (
                    <div className="flex flex-col items-center justify-center mb-6 space-y-3">
                        <div className="flex items-end gap-1 h-8">
                            {[0.4, 0.7, 1.0, 0.8, 0.6, 0.9, 0.5].map((h, i) => (
                                <div key={i}
                                    className="w-1.5 bg-gradient-to-t from-indigo-500 to-purple-400 rounded-full animate-pulse"
                                    style={{ height: `${h * 100}%`, animationDelay: `${i * 0.12}s` }} />
                            ))}
                        </div>
                        <span className="text-sm font-medium text-indigo-600 tracking-wide">NeuroNest is speaking...</span>
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div className="bg-red-50/80 p-4 rounded-xl border border-red-200 text-center mb-6">
                        <p className="text-red-600 font-medium">{error}</p>
                    </div>
                )}

                {/* Results */}
                {transcript && !loading && (
                    <div className="space-y-5 relative z-10">
                        {/* Transcript */}
                        <div className="bg-white/80 backdrop-blur-md p-6 rounded-2xl border border-indigo-50 shadow-sm hover:shadow-md transition-all">
                            <h2 className="text-sm font-bold uppercase tracking-wider mb-3 text-indigo-600 flex items-center gap-2">
                                <Mic className="w-4 h-4" /> Transcript
                            </h2>
                            <p className="text-slate-700 leading-relaxed text-lg">{transcript}</p>
                        </div>

                        {/* Emotion */}
                        <div className="bg-white/80 backdrop-blur-md p-6 rounded-2xl border border-pink-100 shadow-sm hover:shadow-md transition-all">
                            <h2 className="text-sm font-bold uppercase tracking-wider mb-3 text-pink-600 flex items-center gap-2">
                                <HeartPulse className="w-4 h-4" /> Detected Emotion
                            </h2>
                            <div className="flex flex-wrap gap-3 items-center">
                                <div className="inline-block bg-pink-50 px-4 py-2 rounded-xl border border-pink-200">
                                    <p className="capitalize text-pink-600 font-semibold text-lg tracking-wide">{emotion}</p>
                                </div>
                                {emotionData?.stress_level !== undefined && (
                                    <div className="text-sm text-slate-500">
                                        Stress: <span className="font-semibold text-slate-700">{emotionData.stress_level}/100</span>
                                    </div>
                                )}
                                {emotionData?.tone && (
                                    <div className="text-sm text-slate-500">
                                        Tone: <span className="font-semibold text-slate-700 capitalize">{emotionData.tone}</span>
                                    </div>
                                )}
                            </div>
                            {contradiction && hiddenEmotion && (
                                <div className="mt-3 p-3 bg-amber-50 rounded-xl border border-amber-200">
                                    <p className="text-amber-700 text-sm font-medium">
                                        Contradiction detected — hidden: <span className="font-bold">{hiddenEmotion}</span>
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* AI Response */}
                        <div className="bg-indigo-50/80 backdrop-blur-md p-6 rounded-2xl border border-indigo-200 shadow-sm hover:shadow-md relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-200/40 rounded-full blur-3xl"></div>
                            <h2 className="text-sm font-bold uppercase tracking-wider mb-3 text-indigo-700 flex items-center gap-2">
                                <BrainCircuit className="w-4 h-4" /> AI Response
                            </h2>
                            <p className="text-indigo-950 leading-relaxed text-lg relative z-10">{response}</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}