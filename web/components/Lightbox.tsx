"use client";

import { useEffect, useCallback } from "react";

interface LightboxProps {
  images: string[];
  currentIdx: number;
  onClose: () => void;
  onNavigate: (idx: number) => void;
}

export default function Lightbox({
  images,
  currentIdx,
  onClose,
  onNavigate,
}: LightboxProps) {
  const hasPrev = currentIdx > 0;
  const hasNext = currentIdx < images.length - 1;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft" && hasPrev) onNavigate(currentIdx - 1);
      if (e.key === "ArrowRight" && hasNext) onNavigate(currentIdx + 1);
    },
    [onClose, onNavigate, currentIdx, hasPrev, hasNext]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
      onClick={onClose}
    >
      {hasPrev && (
        <button
          className="absolute left-4 top-1/2 -translate-y-1/2 text-white/80 hover:text-white text-4xl p-2 z-50"
          onClick={(e) => {
            e.stopPropagation();
            onNavigate(currentIdx - 1);
          }}
        >
          &#8249;
        </button>
      )}

      <img
        src={`data:image/png;base64,${images[currentIdx]}`}
        alt={`Generated image ${currentIdx + 1}`}
        className="max-h-[90vh] max-w-[90vw] object-contain"
        onClick={(e) => e.stopPropagation()}
      />

      {hasNext && (
        <button
          className="absolute right-4 top-1/2 -translate-y-1/2 text-white/80 hover:text-white text-4xl p-2 z-50"
          onClick={(e) => {
            e.stopPropagation();
            onNavigate(currentIdx + 1);
          }}
        >
          &#8250;
        </button>
      )}

      <button
        className="absolute top-4 right-4 text-white/80 hover:text-white text-2xl p-2"
        onClick={onClose}
      >
        &#10005;
      </button>

      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/70 text-sm">
        {currentIdx + 1} / {images.length}
      </div>
    </div>
  );
}
