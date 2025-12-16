"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Play, Sparkles } from "lucide-react";
import type { CharacterSummary, RelationshipWithCharacter, User } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [relationships, setRelationships] = useState<RelationshipWithCharacter[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  useEffect(() => {
    async function loadData() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          router.push("/login");
          return;
        }

        // Load data in parallel
        const [userData, charactersData, relationshipsData] = await Promise.all([
          api.users.me().catch(() => null),
          api.characters.list(),
          api.relationships.list().catch(() => []),
        ]);

        setUser(userData);
        setCharacters(charactersData);
        setRelationships(relationshipsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Build relationship map for quick lookup
  const relationshipMap = new Map(relationships.map((r) => [r.character_id, r]));

  // Sort relationships by last interaction
  const sortedRelationships = [...relationships].sort((a, b) => {
    const timeA = a.last_interaction_at ? new Date(a.last_interaction_at).getTime() : 0;
    const timeB = b.last_interaction_at ? new Date(b.last_interaction_at).getTime() : 0;
    return timeB - timeA;
  });

  // Hero: most recent relationship
  const heroRelationship = sortedRelationships[0];
  const heroCharacter = heroRelationship
    ? characters.find((c) => c.id === heroRelationship.character_id)
    : null;

  // All characters for grid (excluding hero if exists)
  const gridCharacters = heroCharacter
    ? characters.filter((c) => c.id !== heroCharacter.id)
    : characters;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {user?.display_name ? `Hey, ${user.display_name}` : "Welcome back"}
        </h1>
        <p className="text-muted-foreground">
          Your cozy companions are waiting for you.
        </p>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4">
          <p className="text-destructive font-medium">Unable to load data</p>
          <p className="text-destructive/80 text-sm">{error}</p>
        </Card>
      )}

      {/* Continue / Hero Card */}
      {heroRelationship && heroCharacter && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-muted-foreground">Continue</h2>
          <Link href={`/chat/${heroRelationship.character_id}`}>
            <Card className="overflow-hidden hover:shadow-lg transition-all group cursor-pointer ring-2 ring-primary/20 hover:ring-primary/40">
              <div className="flex flex-col sm:flex-row">
                <div className="relative w-full sm:w-48 h-48 sm:h-auto shrink-0 overflow-hidden bg-muted">
                  {heroCharacter.avatar_url ? (
                    <img
                      src={heroCharacter.avatar_url}
                      alt={heroCharacter.name}
                      className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-secondary/20">
                      <span className="text-4xl font-bold text-muted-foreground/50">
                        {heroCharacter.name[0]}
                      </span>
                    </div>
                  )}
                </div>
                <CardContent className="p-5 flex flex-col justify-between flex-1">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary" className="text-xs">
                        {heroRelationship.stage === "acquaintance" ? "Episode 0" : "In Progress"}
                      </Badge>
                      {heroRelationship.last_interaction_at && (
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(heroRelationship.last_interaction_at)}
                        </span>
                      )}
                    </div>
                    <h3 className="text-xl font-semibold mb-1">{heroCharacter.name}</h3>
                    <p className="text-sm text-muted-foreground capitalize mb-2">{heroCharacter.archetype}</p>
                    <p className="text-sm text-foreground/80 line-clamp-2">
                      {heroCharacter.short_backstory || "Pick up where you left off—your episode awaits."}
                    </p>
                  </div>
                  <Button className="mt-4 w-full sm:w-auto gap-2">
                    <Play className="h-4 w-4" />
                    Resume Episode
                  </Button>
                </CardContent>
              </div>
            </Card>
          </Link>
        </section>
      )}

      {/* All Characters Grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-muted-foreground">
              {heroCharacter ? "More Characters" : "Meet Your Characters"}
            </h2>
            <p className="text-sm text-muted-foreground/70">
              {gridCharacters.length} characters available
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {gridCharacters.map((character) => {
            const relationship = relationshipMap.get(character.id);
            return (
              <CharacterGridCard
                key={character.id}
                character={character}
                relationship={relationship}
              />
            );
          })}
        </div>
      </section>

      {/* Empty state */}
      {characters.length === 0 && (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white text-2xl mb-4">
              <Sparkles className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No characters available</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Characters are being prepared. Check back soon to meet your cozy companions!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface CharacterGridCardProps {
  character: CharacterSummary;
  relationship?: RelationshipWithCharacter;
}

function CharacterGridCard({ character, relationship }: CharacterGridCardProps) {
  const stageLabels: Record<string, string> = {
    acquaintance: "New",
    friendly: "Friendly",
    close: "Close",
    intimate: "Special",
  };

  return (
    <Link href={`/chat/${character.id}`}>
      <Card className="overflow-hidden hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer group h-full">
        <div className="aspect-[3/4] relative overflow-hidden bg-muted">
          {character.avatar_url ? (
            <img
              src={character.avatar_url}
              alt={character.name}
              className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-muted-foreground/20">
              <span className="text-3xl font-bold text-muted-foreground/50">
                {character.name[0]}
              </span>
            </div>
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

          {/* Badges */}
          <div className="absolute top-2 left-2 right-2 flex justify-between items-start">
            {character.is_premium && (
              <Badge className="bg-amber-500/90 text-amber-950 text-[10px] px-1.5 py-0">
                Premium
              </Badge>
            )}
            {relationship && (
              <Badge
                variant="secondary"
                className={cn(
                  "text-[10px] px-1.5 py-0 ml-auto",
                  relationship.stage !== "acquaintance" && "bg-primary/80 text-primary-foreground"
                )}
              >
                {stageLabels[relationship.stage] || relationship.stage}
              </Badge>
            )}
            {!relationship && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 ml-auto bg-white/80 text-foreground border-0">
                Episode 0
              </Badge>
            )}
          </div>

          {/* Name overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-2 text-white">
            <h3 className="font-semibold text-sm leading-tight drop-shadow-md truncate">
              {character.name}
            </h3>
            <p className="text-[11px] text-white/75 capitalize truncate">
              {character.archetype}
            </p>
          </div>
        </div>
      </Card>
    </Link>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      {/* Hero skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
      {/* Grid skeleton */}
      <div className="space-y-4">
        <Skeleton className="h-5 w-32" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {[...Array(12)].map((_, i) => (
            <Skeleton key={i} className="aspect-[3/4] rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
