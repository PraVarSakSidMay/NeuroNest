import VoiceAssistant from './components/VoiceAssistant'

export default function App() {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-purple-50 to-white text-slate-900 flex items-center justify-center p-8 selection:bg-indigo-200">
      <VoiceAssistant />
    </div>
  )
}