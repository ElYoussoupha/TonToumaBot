import { create } from 'zustand';
import { Entity, Instance } from '@/types';

interface AppState {
    // Current Context
    currentEntity: Entity | null;
    currentInstance: Instance | null;

    // Actions
    setCurrentEntity: (entity: Entity | null) => void;
    setCurrentInstance: (instance: Instance | null) => void;

    // UI State
    isLoading: boolean;
    setLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
    currentEntity: null,
    currentInstance: null,
    isLoading: false,

    setCurrentEntity: (entity) => set({ currentEntity: entity }),
    setCurrentInstance: (instance) => set({ currentInstance: instance }),
    setLoading: (loading) => set({ isLoading: loading }),
}));
