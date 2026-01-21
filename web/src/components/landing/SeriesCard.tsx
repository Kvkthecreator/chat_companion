import Link from "next/link";
import Image from "next/image";

interface SeriesCardProps {
  title: string;
  tagline: string | null;
  episodeCount: number;
  coverUrl: string | null;
  href: string;
  genre: string | null;
}

export function SeriesCard({
  title,
  tagline,
  episodeCount,
  coverUrl,
  href,
  genre,
}: SeriesCardProps) {
  return (
    <Link
      href={href}
      className="group relative overflow-hidden rounded-xl border bg-card transition-all hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10"
    >
      {/* Cover image or gradient */}
      <div className="relative aspect-[16/9] overflow-hidden bg-gradient-to-br from-purple-500/20 to-pink-500/20">
        {coverUrl ? (
          <Image
            src={coverUrl}
            alt={title}
            fill
            className="object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-4xl opacity-50">
              {title[0]}
            </span>
          </div>
        )}
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-card via-card/50 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative p-4 -mt-8">
        {genre && (
          <span className="inline-block mb-2 rounded-full bg-purple-100 dark:bg-purple-900/50 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:text-purple-300">
            {genre}
          </span>
        )}
        <h3 className="font-semibold text-foreground group-hover:text-purple-500 transition-colors">
          {title}
        </h3>
        {tagline && (
          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {tagline}
          </p>
        )}
        <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
          <span>{episodeCount} episode{episodeCount !== 1 ? "s" : ""}</span>
        </div>
      </div>
    </Link>
  );
}
