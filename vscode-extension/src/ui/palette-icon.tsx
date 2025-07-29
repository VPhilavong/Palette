import { Palette } from "lucide-react";

export function PaletteIcon() {
  return (
    <div className="flex items-center gap-2">
      <div className="p-2 rounded-full bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-500 shadow-lg">
        <Palette className="w-5 h-5 text-white drop-shadow-md" />
      </div>
      <span className="text-white font-semibold text-sm tracking-wide">Palette</span>
    </div>
  );
}
