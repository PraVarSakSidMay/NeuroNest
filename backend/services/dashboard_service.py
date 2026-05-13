dashboard_memory = []

def update_dashboard(transcript, emotion_data):

    dashboard_memory.append({
        "transcript": transcript,
        "emotion": emotion_data["emotion"],
        "stress_level": emotion_data["stress_level"]
    })

    return dashboard_memory
