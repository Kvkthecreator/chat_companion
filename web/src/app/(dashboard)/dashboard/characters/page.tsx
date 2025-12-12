"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { CharacterGrid } from "@/components/characters";
import { Skeleton } from "@/components/ui/skeleton";
import type { CharacterSummary, RelationshipWithCharacter } from "@/types";

export default function CharactersPage() {
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [relationships, setRelationships] = useState<RelationshipWithCharacter[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [charactersData, relationshipsData] = await Promise.all([
          api.characters.list(),
          api.relationships.list().catch(() => []),
        ]);
        setCharacters(charactersData);
        setRelationships(relationshipsData);
      } catch (err) {
        console.error("Failed to load characters:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-52 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Characters</h1>
        <p className="text-muted-foreground">
          All your cozy companions in one place
        </p>
      </div>

      <CharacterGrid characters={characters} relationships={relationships} />
    </div>
  );
}
