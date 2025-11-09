import { Heart, Star, Eye } from 'lucide-react';
import type { Product, UserInteraction } from '../types';

interface ProductCardProps {
  product: Product;
  interaction: UserInteraction | null;
  onLike: (productId: string) => void;
  onDislike: (productId: string) => void;
  onRate: (productId: string, rating: number) => void;
  onView: (productId: string) => void;
}

export function ProductCard({ product, interaction, onLike, onDislike, onRate, onView }: ProductCardProps) {
  const isLiked = interaction?.interaction_type === 'like';
  const isDisliked = interaction?.interaction_type === 'dislike';
  const currentRating = interaction?.rating || 0;

  const handleImageClick = () => {
    onView(product.id);
  };

  return (
    <div className="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow duration-200">
      <figure className="relative h-48 overflow-hidden cursor-pointer" onClick={handleImageClick}>
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
        />
        <div className="absolute top-2 right-2 badge badge-primary">{product.category}</div>
      </figure>
      <div className="card-body p-4">
        <h3 className="card-title text-base">{product.name}</h3>
        <p className="text-sm text-base-content/70 line-clamp-2">{product.description}</p>
        <div className="text-lg font-bold text-primary">${product.price.toFixed(2)}</div>

        <div className="divider my-2"></div>

        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => onRate(product.id, star)}
                className={`btn btn-xs btn-ghost p-0 ${
                  star <= currentRating ? 'text-warning' : 'text-base-content/30'
                }`}
              >
                <Star className="h-4 w-4" fill={star <= currentRating ? 'currentColor' : 'none'} />
              </button>
            ))}
          </div>

          <div className="flex gap-1">
            <button
              onClick={() => onLike(product.id)}
              className={`btn btn-sm ${isLiked ? 'btn-error' : 'btn-ghost'}`}
              title="Like"
            >
              <Heart className="h-4 w-4" fill={isLiked ? 'currentColor' : 'none'} />
            </button>
            <button
              onClick={() => onDislike(product.id)}
              className={`btn btn-sm ${isDisliked ? 'btn-warning' : 'btn-ghost'}`}
              title="Dislike"
            >
              <Heart className="h-4 w-4 rotate-180" fill={isDisliked ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        {interaction && (
          <div className="text-xs text-base-content/50 mt-2">
            Last interaction: {new Date(interaction.created_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}
