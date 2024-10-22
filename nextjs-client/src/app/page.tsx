"use client";
import { useState, useRef } from "react";

export default function Home() {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);

  const handleRecording = async () => {
    if (!recording) {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);

        mediaRecorderRef.current.ondataavailable = (event) => {
          const audioChunk = event.data;
          console.log("Audio chunk:", audioChunk);
          // Later, send audioChunk to backend for processing
        };

        mediaRecorderRef.current.start(1000); // Collect data in 1-second chunks
        setRecording(true);
      } catch (err) {
        console.error("Error accessing microphone:", err);
      }
    } else {
      // Stop recording
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return (
      <div className="flex items-center justify-center min-h-screen">
        <button
            onClick={handleRecording}
            className="bg-blue-500 text-white px-6 py-3 rounded-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
        >
          {recording ? "Stop Recording" : "Start Recording"}
        </button>
      </div>
  );
}
