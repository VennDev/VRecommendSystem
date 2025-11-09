export interface Product {
  id: string;
  name: string;
  description: string;
  category: string;
  image_url: string;
  price: number;
  created_at: string;
  updated_at: string;
}

export interface UserInteraction {
  id: string;
  user_id: string;
  product_id: string;
  interaction_type: 'view' | 'like' | 'dislike' | 'rating';
  rating?: number;
  created_at: string;
}

export interface Recommendation {
  id: string;
  user_id: string;
  product_id: string;
  model_id: string;
  score: number;
  created_at: string;
  product?: Product;
}
