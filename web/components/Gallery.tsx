"use client";

interface GalleryProps {
  images: string[];
  onImageClick: (idx: number) => void;
}

export default function Gallery({ images, onImageClick }: GalleryProps) {
  if (images.length === 0) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {images.map((img, idx) => (
        <button
          key={idx}
          className="aspect-square overflow-hidden rounded-lg bg-gray-800 transition-transform hover:scale-[1.03] hover:ring-2 hover:ring-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          onClick={() => onImageClick(idx)}
        >
          <img
            src={`data:image/png;base64,${img}`}
            alt={`Generated image ${idx + 1}`}
            className="h-full w-full object-cover"
          />
        </button>
      ))}
    </div>
  );
}
