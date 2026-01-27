"use client";

import { useState, useEffect, useCallback } from "react";
import { api, Artifact, ArtifactAvailability, ArtifactListItem } from "@/lib/api/client";

export function useArtifactAvailability() {
  const [availability, setAvailability] = useState<ArtifactAvailability | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.checkAvailability();
      setAvailability(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { availability, isLoading, error, reload: load };
}

export function useArtifacts(meaningfulOnly: boolean = true) {
  const [artifacts, setArtifacts] = useState<ArtifactListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.list(meaningfulOnly);
      setArtifacts(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [meaningfulOnly]);

  useEffect(() => {
    load();
  }, [load]);

  return { artifacts, isLoading, error, reload: load };
}

export function useThreadJourney(threadId: string | null) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async (regenerate: boolean = false) => {
    if (!threadId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.getThreadJourney(threadId, regenerate);
      setArtifact(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  useEffect(() => {
    if (threadId) {
      load();
    }
  }, [threadId, load]);

  return { artifact, isLoading, error, reload: load, regenerate: () => load(true) };
}

export function useDomainHealth(domain: string | null) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async (regenerate: boolean = false) => {
    if (!domain) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.getDomainHealth(domain, regenerate);
      setArtifact(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [domain]);

  useEffect(() => {
    if (domain) {
      load();
    }
  }, [domain, load]);

  return { artifact, isLoading, error, reload: load, regenerate: () => load(true) };
}

export function useCommunicationProfile() {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async (regenerate: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.getCommunicationProfile(regenerate);
      setArtifact(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { artifact, isLoading, error, reload: load, regenerate: () => load(true) };
}

export function useRelationshipSummary() {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async (regenerate: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.artifacts.getRelationshipSummary(regenerate);
      setArtifact(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { artifact, isLoading, error, reload: load, regenerate: () => load(true) };
}
