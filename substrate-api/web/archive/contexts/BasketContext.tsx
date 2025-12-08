"use client";

import React, { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useUniversalChanges } from '@/lib/hooks/useUniversalChanges';
import type { DocumentDTO } from '@/shared/contracts/documents';

// Think of this as a "shared data store" that all components can access
// Like having a central database that updates everywhere at once

interface Basket {
  id: string;
  name: string | null;
  description?: string | null; // Mapped from origin_template
  status?: string | null;
  created_at: string;
  last_activity_ts?: string | null;
  workspace_id: string;
  tags?: string[] | null;
  origin_template?: string | null;
}

interface BasketContextType {
  basket: Basket | null;
  documents: DocumentDTO[];
  updateBasketName: (newName: string) => Promise<void>;
  setBasket: (basket: Basket) => void;
  setDocuments: (docs: DocumentDTO[]) => void;
  isLoading: boolean;
  error: string | null;
}

// Create the context (think of it as creating the shared space)
const BasketContext = createContext<BasketContextType | undefined>(undefined);

// Provider component that wraps around parts of your app
export function BasketProvider({
  children,
  initialBasket,
  initialDocuments = []
}: {
  children: ReactNode;
  initialBasket: Basket | null;
  initialDocuments?: DocumentDTO[];
}) {
  const [basket, setBasket] = useState<Basket | null>(initialBasket);
  const [documents, setDocuments] = useState<DocumentDTO[]>(initialDocuments);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get universal changes hook for this basket
  const changeManager = useUniversalChanges(basket?.id || '');

  // Function to update basket name using Universal Change System
  const updateBasketName = useCallback(async (newName: string) => {
    if (!basket) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Optimistically update the UI (show change immediately)
      setBasket(prev => prev ? { ...prev, name: newName } : null);
      
      // Submit change through unified system
      const result = await changeManager.updateBasket({ name: newName });

      if (result.success) {
        // Update with the applied data from the universal system
        if (result.appliedData) {
          setBasket(result.appliedData);
        }
      } else {
        throw new Error(result.errors?.[0] || 'Failed to update basket name');
      }
      
    } catch (err) {
      // Revert on error
      setBasket(basket);
      setError(err instanceof Error ? err.message : 'Failed to update basket name');
      console.error('❌ Failed to update basket name via Universal Changes:', err);
    } finally {
      setIsLoading(false);
    }
  }, [basket, changeManager]);

  return (
    <BasketContext.Provider value={{
      basket,
      documents,
      updateBasketName,
      setBasket,
      setDocuments,
      isLoading,
      error
    }}>
      {children}
    </BasketContext.Provider>
  );
}

// Hook to use the basket context
export function useBasket() {
  const context = useContext(BasketContext);
  if (context === undefined) {
    throw new Error('useBasket must be used within a BasketProvider');
  }
  return context;
}

// 🎯 Product Manager Explanation:
// This creates a "single source of truth" for basket data
// When you update the basket name here, it automatically updates everywhere
// No need for page refreshes or complex syncing - it just works!
