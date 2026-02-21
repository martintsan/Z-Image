"use client";

interface ProgressWaterProps {
  durationMs: number;
  isGenerating: boolean;
}

export default function ProgressWater({
  durationMs,
  isGenerating,
}: ProgressWaterProps) {
  if (!isGenerating) return null;

  return (
    <div className="relative h-24 rounded-xl overflow-hidden bg-gray-800">
      <div
        className="water-wave absolute bottom-0 left-0 right-0 bg-blue-500/80"
        style={{
          animation: `rise ${durationMs}ms ease-out forwards`,
          height: "0%",
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <span className="text-white font-semibold text-lg tracking-wide">
          Generating...
        </span>
      </div>
      <style jsx>{`
        @keyframes rise {
          from {
            height: 0%;
          }
          to {
            height: 100%;
          }
        }
      `}</style>
    </div>
  );
}
