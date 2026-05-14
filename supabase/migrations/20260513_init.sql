-- Create users table if not exists
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT,
    role TEXT DEFAULT 'patient',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create voice_sessions table
CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create consolidated interactions table
-- This stores the transcript, emotional analysis, and AI response
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES voice_sessions(id),
    user_id UUID REFERENCES users(id),
    
    -- Input
    transcript TEXT,
    raw_audio_url TEXT,
    
    -- Audio Features
    pitch_mean FLOAT,
    jitter FLOAT,
    loudness FLOAT,
    
    -- Emotional Analysis
    emotion TEXT,
    stress_level INTEGER,
    tone TEXT,
    contradiction_detected BOOLEAN,
    hidden_emotion TEXT,
    
    -- AI Response
    response_text TEXT,
    tts_audio_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security) - basic public access for hackathon
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public Access" ON users FOR ALL USING (true);
CREATE POLICY "Public Access" ON voice_sessions FOR ALL USING (true);
CREATE POLICY "Public Access" ON interactions FOR ALL USING (true);
