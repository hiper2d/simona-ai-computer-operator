"use client";
import React, { useState, useRef } from "react";

export default function Home() {
  const [recording, setRecording] = useState<boolean>(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  const handleRecording = async (): Promise<void> => {
    if (!recording) {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStreamRef.current = stream; // Store the stream to stop it later

        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event: BlobEvent) => {
          const audioChunk = event.data;
          console.log("Audio chunk:", audioChunk);
          // Later, send audioChunk to backend for processing
        };

        mediaRecorder.start(1000); // Collect data in 1-second chunks
        setRecording(true);
      } catch (err) {
        console.error("Error accessing microphone:", err);
      }
    } else {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
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
