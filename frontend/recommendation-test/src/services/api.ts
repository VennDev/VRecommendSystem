import { supabase } from './supabase';
import type { Product, UserInteraction, Recommendation } from '../types';

const AI_SERVER_URL = import.meta.env.VITE_AI_SERVER_URL || 'http://localhost:9999';
const API_SERVER_URL = import.meta.env.VITE_API_SERVER_URL || 'http://localhost:2030';

export const productService = {
  async getAll(): Promise<Product[]> {
    const { data, error } = await supabase
      .from('products')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  async getByCategory(category: string): Promise<Product[]> {
    const { data, error } = await supabase
      .from('products')
      .select('*')
      .eq('category', category)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  async getCategories(): Promise<string[]> {
    const { data, error } = await supabase
      .from('products')
      .select('category')
      .order('category');

    if (error) throw error;

    const categories = [...new Set((data || []).map(p => p.category))];
    return categories;
  }
};

export const interactionService = {
  async create(userId: string, productId: string, type: string, rating?: number): Promise<UserInteraction> {
    const { data, error } = await supabase
      .from('user_interactions')
      .insert({
        user_id: userId,
        product_id: productId,
        interaction_type: type,
        rating: rating
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async getUserInteractions(userId: string): Promise<UserInteraction[]> {
    const { data, error } = await supabase
      .from('user_interactions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  async getProductInteraction(userId: string, productId: string): Promise<UserInteraction | null> {
    const { data, error } = await supabase
      .from('user_interactions')
      .select('*')
      .eq('user_id', userId)
      .eq('product_id', productId)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) throw error;
    return data;
  },

  async update(id: string, type: string, rating?: number): Promise<UserInteraction> {
    const { data, error } = await supabase
      .from('user_interactions')
      .update({
        interaction_type: type,
        rating: rating
      })
      .eq('id', id)
      .select()
      .single();

    if (error) throw error;
    return data;
  }
};

export const recommendationService = {
  async getRecommendations(userId: string, modelId: string, n: number = 10): Promise<any> {
    try {
      const response = await fetch(
        `${API_SERVER_URL}/api/v1/recommend?user_id=${userId}&model_id=${modelId}&n=${n}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get recommendations');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting recommendations:', error);
      throw error;
    }
  },

  async saveRecommendations(userId: string, recommendations: Array<{product_id: string, model_id: string, score: number}>): Promise<void> {
    const records = recommendations.map(rec => ({
      user_id: userId,
      product_id: rec.product_id,
      model_id: rec.model_id,
      score: rec.score
    }));

    const { error } = await supabase
      .from('recommendations')
      .insert(records);

    if (error) throw error;
  },

  async getUserRecommendations(userId: string): Promise<Recommendation[]> {
    const { data, error } = await supabase
      .from('recommendations')
      .select(`
        *,
        product:products(*)
      `)
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  }
};

export const modelService = {
  async listModels(): Promise<any> {
    try {
      const response = await fetch(`${AI_SERVER_URL}/api/v1/list_models`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to list models');
      }

      const result = await response.json();
      return result.data || {};
    } catch (error) {
      console.error('Error listing models:', error);
      throw error;
    }
  }
};
