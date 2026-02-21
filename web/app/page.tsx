"use client";

import { useState, useEffect, useCallback } from "react";
import GeneratorForm from "../components/GeneratorForm";
import ProgressWater from "../components/ProgressWater";
import Gallery from "../components/Gallery";
import Lightbox from "../components/Lightbox";
import { fetchHealth, fetchSamplers, fetchSchedulers, generate } from "../lib/api";
import type {
  SamplerInfo,
  SchedulerInfo,
  GenerationValues,
  HealthResponse,
} from "../lib/types";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [samplers, setSamplers] = useState<SamplerInfo[]>([]);
  const [schedulers, setSchedulers] = useState<SchedulerInfo[]>([]);
  const [images, setImages] = useState<string[]>([]);
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [estimatedMs, setEstimatedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
    fetchSamplers().then(setSamplers).catch(() => {});
    fetchSchedulers().then(setSchedulers).catch(() => {});
  }, []);

  const handleGenerate = useCallback(async (values: GenerationValues) => {
    setError(null);
    const pixels = values.width * values.height;
    const est = 30000 * (pixels / (1024 * 1024)) * (values.steps / 8);
    setEstimatedMs(est);
    setIsGenerating(true);

    try {
      const result = await generate(values);
      setImages((prev) => [...result.images, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setIsGenerating(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <h1 className="text-xl font-bold text-white">Z-Image</h1>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                health?.status === "ok" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-sm text-gray-400">
              {health?.status === "ok"
                ? "Connected"
                : health
                  ? "Degraded"
                  : "Disconnected"}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-8 lg:grid-cols-[400px_1fr]">
          {/* Left column: form */}
          <div className="space-y-6">
            <GeneratorForm
              samplers={samplers}
              schedulers={schedulers}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />

            <ProgressWater
              durationMs={estimatedMs}
              isGenerating={isGenerating}
            />

            {error && (
              <div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Right column: gallery */}
          <div>
            {images.length === 0 ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-gray-800 text-gray-600">
                Generated images will appear here
              </div>
            ) : (
              <Gallery
                images={images}
                onImageClick={(idx) => setLightboxIdx(idx)}
              />
            )}
          </div>
        </div>
      </main>

      {lightboxIdx !== null && (
        <Lightbox
          images={images}
          currentIdx={lightboxIdx}
          onClose={() => setLightboxIdx(null)}
          onNavigate={setLightboxIdx}
        />
      )}
    </div>
  );
}
