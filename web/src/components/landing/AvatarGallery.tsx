"use client";

const SAMPLE_AVATARS = [
  { id: 1, gradient: "from-purple-400 to-pink-400", letter: "A" },
  { id: 2, gradient: "from-blue-400 to-cyan-400", letter: "M" },
  { id: 3, gradient: "from-green-400 to-emerald-400", letter: "K" },
  { id: 4, gradient: "from-orange-400 to-red-400", letter: "S" },
  { id: 5, gradient: "from-indigo-400 to-purple-400", letter: "R" },
  { id: 6, gradient: "from-pink-400 to-rose-400", letter: "L" },
];

export function AvatarGallery() {
  return (
    <div className="relative w-full max-w-xs mx-auto">
      {/* Central large avatar */}
      <div className="relative mx-auto h-32 w-32 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 shadow-xl shadow-purple-500/30 flex items-center justify-center">
        <span className="text-4xl font-bold text-white">You</span>
        <div className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full bg-green-500 border-4 border-card flex items-center justify-center">
          <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Orbiting smaller avatars */}
      <div className="absolute inset-0 animate-spin-slow" style={{ animationDuration: "20s" }}>
        {SAMPLE_AVATARS.map((avatar, index) => {
          const angle = (index * 360) / SAMPLE_AVATARS.length;
          const radius = 90;
          const x = Math.cos((angle * Math.PI) / 180) * radius;
          const y = Math.sin((angle * Math.PI) / 180) * radius;

          return (
            <div
              key={avatar.id}
              className={`absolute left-1/2 top-1/2 h-10 w-10 -ml-5 -mt-5 rounded-full bg-gradient-to-br ${avatar.gradient} shadow-lg flex items-center justify-center`}
              style={{
                transform: `translate(${x}px, ${y}px)`,
              }}
            >
              <span className="text-sm font-semibold text-white">{avatar.letter}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
