// 'use client';

// import { useState } from 'react';
// import ResultCard from '@/components/ResultCard';

// export default function Home() {
//   const [image, setImage] = useState<File | null>(null);
//   const [preview, setPreview] = useState<string | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [result, setResult] = useState<any>(null);

//   const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     if (e.target.files && e.target.files[0]) {
//       const file = e.target.files[0];
//       setImage(file);
//       setPreview(URL.createObjectURL(file));
//       setResult(null); // Reset hasil jika ganti gambar
//     }
//   };

//   const analyzeImage = async () => {
//     if (!image) return;
//     setLoading(true);
//     setResult(null); // Kosongkan hasil sebelumnya
    
//     const formData = new FormData();
//     formData.append('file', image);

//     try {
//       const response = await fetch('http://localhost:8000/analyze', {
//         method: 'POST',
//         body: formData,
//       });
      
//       const data = await response.json();

//       // CEK STATUS RESPONSE
//       if (!response.ok) {
//         throw new Error(data.detail || "Terjadi kesalahan pada server");
//       }
      
//       setResult(data);
//     } catch (error: any) {
//       console.error("Gagal menganalisis gambar:", error);
//       alert(error.message || "Terjadi kesalahan saat menghubungi server.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <main className="min-h-screen bg-neutral-950 text-neutral-200 font-sans flex flex-col items-center py-12 px-4">
//       <div className="max-w-3xl w-full space-y-8">
        
//         {/* Header */}
//         <div className="text-center space-y-2">
//           <h1 className="text-4xl font-semibold tracking-tight text-white">
//             Lens<span className="text-emerald-400">Arthropoda</span>
//           </h1>
//           <p className="text-neutral-400">Identifikasi serangga dan temukan fakta uniknya.</p>
//         </div>

//         {/* Upload Section */}
//         <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-2xl flex flex-col items-center justify-center gap-6">
//           <label 
//             className={`flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${preview ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-neutral-700 hover:border-neutral-500 hover:bg-neutral-800/50'}`}
//           >
//             {preview ? (
//               // eslint-disable-next-line @next/next/no-img-element
//               <img src={preview} alt="Preview" className="h-full object-contain p-2 rounded-lg" />
//             ) : (
//               <div className="flex flex-col items-center justify-center pt-5 pb-6">
//                 <svg className="w-10 h-10 mb-3 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
//                 <p className="mb-2 text-sm text-neutral-400"><span className="font-semibold">Klik untuk upload</span> atau drag and drop</p>
//                 <p className="text-xs text-neutral-500">PNG, JPG or JPEG (MAX. 5MB)</p>
//               </div>
//             )}
//             <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
//           </label>

//           <button 
//             onClick={analyzeImage}
//             disabled={!image || loading}
//             className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 disabled:bg-neutral-800 disabled:text-neutral-500 text-white font-medium rounded-xl transition-all duration-200 flex justify-center items-center gap-2"
//           >
//             {loading ? (
//               <span className="animate-pulse">Menganalisis...</span>
//             ) : (
//               "Analisis Serangga"
//             )}
//           </button>
//         </div>

//         {/* Result Section */}
//         {result && <ResultCard result={result} />}

//       </div>
//     </main>
//   );
// }

"use client";

import { useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ── Types ───────────────────────────────────────────────────────────────────
interface TopKPrediction {
  class_name: string;
  confidence: number;
}

interface PredictionResponse {
  predicted_class: string;
  confidence: number;
  top_k: TopKPrediction[];
  ai_insights: string | null;
  ai_available: boolean;
  fallback_message: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ── Component ───────────────────────────────────────────────────────────────
export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl]     = useState<string | null>(null);
  const [result, setResult]             = useState<PredictionResponse | null>(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [isDragging, setIsDragging]     = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Harap unggah file gambar (JPG/PNG/WebP).");
      return;
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0]);
  }, []);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Error ${res.status}`);
      }

      const data: PredictionResponse = await res.json();
      setResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Terjadi kesalahan tidak diketahui.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-950 via-teal-900 to-cyan-900 text-white">
      {/* ── Header ── */}
      <header className="py-8 text-center">
        <div className="inline-flex items-center gap-3 mb-2">
          <span className="text-4xl">🔬</span>
          <h1 className="text-4xl font-bold tracking-tight">
            <span className="text-white">Lens</span>
            <span className="text-emerald-400">Arthropoda</span>
          </h1>
        </div>
        <p className="text-teal-300 text-sm mt-1 opacity-80">
          Identifikasi serangga dari gambar & temukan fakta uniknya
        </p>
      </header>

      <div className="max-w-3xl mx-auto px-4 pb-16 space-y-6">

        {/* ── Upload Card ── */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6">
          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => !selectedFile && fileInputRef.current?.click()}
            className={`relative rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer
              ${isDragging ? "border-emerald-400 bg-emerald-500/10" : "border-white/30 hover:border-emerald-400/60"}
              ${selectedFile ? "cursor-default" : ""}
              min-h-[200px] flex flex-col items-center justify-center p-4`}
          >
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="preview"
                className="max-h-64 rounded-lg object-contain shadow-lg"
              />
            ) : (
              <div className="text-center space-y-2">
                <span className="text-5xl">🦋</span>
                <p className="text-sm text-white/60">
                  Seret & lepas gambar ke sini, atau klik untuk pilih file
                </p>
                <p className="text-xs text-white/40">JPG · PNG · WebP</p>
              </div>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleInputChange}
          />

          {/* File info */}
          {selectedFile && (
            <p className="text-xs text-teal-300 mt-2 text-center">
              📁 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}

          {/* Buttons */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
              className="flex-1 py-3 rounded-xl font-semibold bg-emerald-500 hover:bg-emerald-400 
                         disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200
                         shadow-lg shadow-emerald-500/20 text-white"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  AI sedang menganalisis...
                </span>
              ) : "🔍 Analisis Serangga"}
            </button>

            {selectedFile && (
              <button
                onClick={handleReset}
                className="px-4 py-3 rounded-xl bg-white/10 hover:bg-white/20 transition-all duration-200 text-sm"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="bg-red-500/20 border border-red-400/40 rounded-xl p-4 text-red-200 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* ── Result ── */}
        {result && (
          <div className="space-y-4 animate-fadeIn">

            {/* Prediction Header */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6">
              <p className="text-xs text-emerald-400 uppercase tracking-widest mb-1">
                Hasil Prediksi Utama
              </p>
              <h2 className="text-3xl font-bold text-white mb-4">
                {result.predicted_class}
              </h2>

              {/* Top-K badges */}
              <div className="flex flex-wrap gap-2">
                {result.top_k.map((item, i) => (
                  <span
                    key={i}
                    className={`px-3 py-1 rounded-full text-xs font-medium
                      ${i === 0
                        ? "bg-emerald-500/80 text-white"
                        : "bg-white/10 text-white/70"}`}
                  >
                    {item.class_name}{" "}
                    <span className="opacity-80">{(item.confidence * 100).toFixed(1)}%</span>
                  </span>
                ))}
              </div>

              {/* Confidence bar */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-white/50 mb-1">
                  <span>Kepercayaan Model</span>
                  <span>{(result.confidence * 100).toFixed(2)}%</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700"
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* AI Insights */}
            {result.ai_available && result.ai_insights ? (
              <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6">
                <p className="text-xs text-teal-400 uppercase tracking-widest mb-3">
                  🤖 Informasi Spesies (AI Insights)
                </p>
                <div className="prose prose-invert prose-sm max-w-none
                  prose-headings:text-emerald-300 prose-strong:text-white
                  prose-li:text-white/80 prose-p:text-white/80">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {result.ai_insights}
                  </ReactMarkdown>
                </div>
              </div>
            ) : (
              <div className="bg-yellow-500/10 border border-yellow-400/30 rounded-xl p-4 text-yellow-200 text-sm">
                ⚠️ {result.fallback_message || "AI Insights tidak tersedia saat ini."}
              </div>
            )}

          </div>
        )}
      </div>
    </main>
  );
}
