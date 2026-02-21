"use client";

import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import {
  ASPECT_RATIOS,
  type GenerationMode,
  type GenerationValues,
  type SamplerInfo,
  type SchedulerInfo,
} from "../lib/types";

interface GeneratorFormProps {
  samplers: SamplerInfo[];
  schedulers: SchedulerInfo[];
  onGenerate: (values: GenerationValues) => void;
  isGenerating: boolean;
}

const MODES: { value: GenerationMode; label: string }[] = [
  { value: "txt2img", label: "Text to Image" },
  { value: "img2img", label: "Image to Image" },
  { value: "inpaint", label: "Inpaint" },
];

function roundTo64(n: number): number {
  return Math.round(n / 64) * 64;
}

function clamp64(n: number): number {
  return Math.max(64, Math.min(2048, roundTo64(n)));
}

export default function GeneratorForm({
  samplers,
  schedulers,
  onGenerate,
  isGenerating,
}: GeneratorFormProps) {
  const [mode, setMode] = useState<GenerationMode>("txt2img");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [selectedRatio, setSelectedRatio] = useState("1:1");
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);
  const [steps, setSteps] = useState(8);
  const [cfgScale, setCfgScale] = useState(1.0);
  const [seed, setSeed] = useState(-1);
  const [batchSize, setBatchSize] = useState(1);
  const [samplerName, setSamplerName] = useState("");
  const [scheduler, setScheduler] = useState("");
  const [clipSkip, setClipSkip] = useState(-1);
  const [strength, setStrength] = useState(0.75);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [image, setImage] = useState<File | null>(null);
  const [mask, setMask] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [maskPreview, setMaskPreview] = useState<string | null>(null);

  const imageInputRef = useRef<HTMLInputElement>(null);
  const maskInputRef = useRef<HTMLInputElement>(null);

  const handleRatioSelect = (label: string) => {
    setSelectedRatio(label);
    const ratio = ASPECT_RATIOS.find((r) => r.label === label);
    if (ratio) {
      setWidth(ratio.width);
      setHeight(ratio.height);
    }
  };

  const handleFileDrop =
    (setter: (f: File) => void, previewSetter: (s: string) => void) =>
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        setter(file);
        previewSetter(URL.createObjectURL(file));
      }
    };

  const handleFileSelect =
    (setter: (f: File) => void, previewSetter: (s: string) => void) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setter(file);
        previewSetter(URL.createObjectURL(file));
      }
    };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isGenerating) return;
    onGenerate({
      mode,
      prompt: prompt.trim(),
      negative_prompt: negativePrompt,
      width,
      height,
      steps,
      cfg_scale: cfgScale,
      seed,
      batch_size: batchSize,
      sampler_name: samplerName,
      scheduler,
      clip_skip: clipSkip,
      strength,
      image: image ?? undefined,
      mask: mask ?? undefined,
    });
  };

  const isCustomRatio = selectedRatio === "Custom";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Mode tabs */}
      <div className="flex gap-1 rounded-lg bg-gray-800 p-1">
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              mode === m.value
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
            onClick={() => setMode(m.value)}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Prompt */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Prompt
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          rows={3}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        />
      </div>

      {/* Aspect ratio */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Aspect Ratio
        </label>
        <div className="flex flex-wrap gap-2">
          {ASPECT_RATIOS.map((r) => (
            <button
              key={r.label}
              type="button"
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                selectedRatio === r.label
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-white"
              }`}
              onClick={() => handleRatioSelect(r.label)}
            >
              {r.label}
            </button>
          ))}
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isCustomRatio
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
            onClick={() => setSelectedRatio("Custom")}
          >
            Custom
          </button>
        </div>
        {isCustomRatio && (
          <div className="mt-2 flex gap-3">
            <div>
              <label className="text-xs text-gray-400">Width</label>
              <input
                type="number"
                value={width}
                onChange={(e) => setWidth(clamp64(Number(e.target.value)))}
                step={64}
                min={64}
                max={2048}
                className="mt-1 w-24 rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400">Height</label>
              <input
                type="number"
                value={height}
                onChange={(e) => setHeight(clamp64(Number(e.target.value)))}
                step={64}
                min={64}
                max={2048}
                className="mt-1 w-24 rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* Image upload for img2img / inpaint */}
      {(mode === "img2img" || mode === "inpaint") && (
        <div className="space-y-3">
          <DropZone
            label="Input Image"
            preview={imagePreview}
            onDrop={handleFileDrop(setImage, setImagePreview)}
            onClick={() => imageInputRef.current?.click()}
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileSelect(setImage, setImagePreview)}
          />
          {mode === "inpaint" && (
            <>
              <DropZone
                label="Mask Image"
                preview={maskPreview}
                onDrop={handleFileDrop(setMask, setMaskPreview)}
                onClick={() => maskInputRef.current?.click()}
              />
              <input
                ref={maskInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect(setMask, setMaskPreview)}
              />
            </>
          )}
        </div>
      )}

      {/* Strength slider for img2img / inpaint */}
      {(mode === "img2img" || mode === "inpaint") && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Strength: {strength.toFixed(2)}
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={strength}
            onChange={(e) => setStrength(Number(e.target.value))}
            className="w-full accent-blue-500"
          />
        </div>
      )}

      {/* Advanced settings */}
      <div>
        <button
          type="button"
          className="text-sm text-gray-400 hover:text-white transition-colors"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? "▾" : "▸"} Advanced Settings
        </button>
        {showAdvanced && (
          <div className="mt-3 space-y-3 rounded-lg border border-gray-700 bg-gray-800/50 p-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Negative Prompt
              </label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="Things to avoid..."
                rows={2}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Sampler
                </label>
                <select
                  value={samplerName}
                  onChange={(e) => setSamplerName(e.target.value)}
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="">Default</option>
                  {samplers.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Scheduler
                </label>
                <select
                  value={scheduler}
                  onChange={(e) => setScheduler(e.target.value)}
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="">Default</option>
                  {schedulers.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Steps: {steps}
              </label>
              <input
                type="range"
                min={1}
                max={150}
                value={steps}
                onChange={(e) => setSteps(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  CFG Scale
                </label>
                <input
                  type="number"
                  value={cfgScale}
                  onChange={(e) => setCfgScale(Number(e.target.value))}
                  min={0}
                  max={30}
                  step={0.5}
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Seed</label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  min={-1}
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={batchSize}
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                  min={1}
                  max={8}
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">
                CLIP Skip
              </label>
              <input
                type="number"
                value={clipSkip}
                onChange={(e) => setClipSkip(Number(e.target.value))}
                min={-1}
                max={12}
                className="w-24 rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="ml-2 text-xs text-gray-500">
                -1 = server default
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Generate button */}
      <button
        type="submit"
        disabled={
          !prompt.trim() ||
          isGenerating
        }
        className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isGenerating ? "Generating..." : "Generate"}
      </button>
    </form>
  );
}

function DropZone({
  label,
  preview,
  onDrop,
  onClick,
}: {
  label: string;
  preview: string | null;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  onClick: () => void;
}) {
  const [isDragOver, setIsDragOver] = useState(false);

  return (
    <div
      className={`relative rounded-lg border-2 border-dashed p-4 text-center cursor-pointer transition-colors ${
        isDragOver
          ? "border-blue-500 bg-blue-500/10"
          : "border-gray-700 hover:border-gray-500"
      }`}
      onDrop={(e) => {
        setIsDragOver(false);
        onDrop(e);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onClick={onClick}
    >
      {preview ? (
        <img
          src={preview}
          alt={label}
          className="mx-auto max-h-32 rounded object-contain"
        />
      ) : (
        <div className="text-gray-500">
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs mt-1">Drop an image or click to browse</p>
        </div>
      )}
    </div>
  );
}
