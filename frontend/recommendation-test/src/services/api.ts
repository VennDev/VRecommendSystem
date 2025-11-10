import type { Product } from '../types';

const LOCAL_SERVER_URL = 'http://localhost:3001';
const AI_SERVER_URL = 'http://localhost:9999';
const API_SERVER_URL = 'http://localhost:2030';

export const authService = {
  async login(username: string): Promise<any> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username }),
      });

      if (!response.ok) {
        throw new Error('Failed to login');
      }

      return await response.json();
    } catch (error) {
      console.error('Error logging in:', error);
      throw error;
    }
  }
};

export const productService = {
  async getAll(): Promise<Product[]> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/products`);

      if (!response.ok) {
        throw new Error('Failed to fetch products');
      }

      const result = await response.json();
      return result.products || [];
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  },

  async getByCategory(category: string): Promise<Product[]> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/products?category=${category}`);

      if (!response.ok) {
        throw new Error('Failed to fetch products');
      }

      const result = await response.json();
      return result.products || [];
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  },

  async getCategories(): Promise<string[]> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/products/categories`);

      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }

      const result = await response.json();
      return result.categories || [];
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  }
};

export const interactionService = {
  async create(userId: string, productId: string, type: string, rating?: number): Promise<any> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/interactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          productId,
          type,
          value: rating,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create interaction');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating interaction:', error);
      throw error;
    }
  },

  async getUserInteractions(userId: string): Promise<any[]> {
    try {
      const response = await fetch(`${LOCAL_SERVER_URL}/api/interactions/${userId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch interactions');
      }

      const result = await response.json();
      return result.interactions || [];
    } catch (error) {
      console.error('Error fetching interactions:', error);
      throw error;
    }
  },

  async getProductInteraction(userId: string, productId: string): Promise<any | null> {
    try {
      const interactions = await this.getUserInteractions(userId);
      const productInteractions = interactions.filter((i: any) => i.productId === productId);
      return productInteractions.length > 0 ? productInteractions[0] : null;
    } catch (error) {
      console.error('Error fetching product interaction:', error);
      return null;
    }
  },
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
