import { useState, useEffect } from 'react';
import { ShoppingBag, User, BarChart3 } from 'lucide-react';
import { ProductCard } from './components/ProductCard';
import { RecommendationPanel } from './components/RecommendationPanel';
import { productService, interactionService } from './services/api';
import { ensureUser, clearUser } from './utils/session';
import type { Product } from './types';

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [interactions, setInteractions] = useState<Map<string, any>>(new Map());
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string>('');
  const [showStats, setShowStats] = useState(false);

  useEffect(() => {
    initUser();
  }, []);

  const initUser = async () => {
    try {
      const id = await ensureUser();
      setUserId(id);
      loadData(id);
    } catch (error) {
      console.error('Failed to initialize user:', error);
    }
  };

  const loadData = async (uid?: string) => {
    setLoading(true);
    try {
      const currentUserId = uid || userId;
      const [productsData, categoriesData, interactionsData] = await Promise.all([
        productService.getAll(),
        productService.getCategories(),
        interactionService.getUserInteractions(currentUserId)
      ]);

      setProducts(productsData);
      setCategories(['All', ...categoriesData]);

      const interactionMap = new Map<string, any>();
      interactionsData.forEach((interaction: any) => {
        interactionMap.set(interaction.productId, interaction);
      });
      setInteractions(interactionMap);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInteraction = async (productId: string, type: string, rating?: number) => {
    try {
      const updatedInteraction = await interactionService.create(userId, productId, type, rating);

      const newInteractions = new Map(interactions);
      newInteractions.set(productId, updatedInteraction.interaction);
      setInteractions(newInteractions);
    } catch (error) {
      console.error('Failed to save interaction:', error);
    }
  };

  const handleLike = (productId: string) => handleInteraction(productId, 'like');
  const handleDislike = (productId: string) => handleInteraction(productId, 'dislike');
  const handleRate = (productId: string, rating: number) => handleInteraction(productId, 'rating', rating);
  const handleView = (productId: string) => handleInteraction(productId, 'view');

  const handleResetSession = () => {
    if (confirm('Are you sure you want to reset your session? All your interactions will be cleared.')) {
      clearUser();
      window.location.reload();
    }
  };

  const filteredProducts = selectedCategory === 'All'
    ? products
    : products.filter(p => p.category === selectedCategory);

  const stats = {
    totalInteractions: interactions.size,
    likes: Array.from(interactions.values()).filter(i => i.type === 'like').length,
    dislikes: Array.from(interactions.values()).filter(i => i.type === 'dislike').length,
    ratings: Array.from(interactions.values()).filter(i => i.type === 'rating').length,
    views: Array.from(interactions.values()).filter(i => i.type === 'view').length,
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg text-primary"></div>
          <p className="mt-4 text-lg">Loading products...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base-200">
      <div className="navbar bg-base-100 shadow-lg">
        <div className="flex-1">
          <a className="btn btn-ghost normal-case text-xl gap-2">
            <ShoppingBag className="h-6 w-6" />
            Product Recommendation Test
          </a>
        </div>
        <div className="flex-none gap-2">
          <button
            onClick={() => setShowStats(!showStats)}
            className="btn btn-ghost gap-2"
          >
            <BarChart3 className="h-5 w-5" />
            Stats
          </button>
          <div className="dropdown dropdown-end">
            <label tabIndex={0} className="btn btn-ghost gap-2">
              <User className="h-5 w-5" />
              <span className="hidden md:inline">{userId.substring(0, 12)}...</span>
            </label>
            <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a onClick={handleResetSession}>Reset Session</a></li>
            </ul>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {showStats && (
          <div className="stats shadow w-full mb-8">
            <div className="stat">
              <div className="stat-title">Total Interactions</div>
              <div className="stat-value text-primary">{stats.totalInteractions}</div>
            </div>
            <div className="stat">
              <div className="stat-title">Likes</div>
              <div className="stat-value text-success">{stats.likes}</div>
            </div>
            <div className="stat">
              <div className="stat-title">Dislikes</div>
              <div className="stat-value text-warning">{stats.dislikes}</div>
            </div>
            <div className="stat">
              <div className="stat-title">Ratings</div>
              <div className="stat-value text-info">{stats.ratings}</div>
            </div>
            <div className="stat">
              <div className="stat-title">Views</div>
              <div className="stat-value">{stats.views}</div>
            </div>
          </div>
        )}

        <RecommendationPanel onRecommendationsGenerated={loadData} />

        <div className="mb-6 flex items-center gap-2 overflow-x-auto pb-2">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`btn btn-sm ${
                selectedCategory === category ? 'btn-primary' : 'btn-outline'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProducts.map(product => (
            <ProductCard
              key={product.id}
              product={product}
              interaction={interactions.get(product.id) || null}
              onLike={handleLike}
              onDislike={handleDislike}
              onRate={handleRate}
              onView={handleView}
            />
          ))}
        </div>

        {filteredProducts.length === 0 && (
          <div className="text-center py-12">
            <ShoppingBag className="h-16 w-16 mx-auto text-base-content/30 mb-4" />
            <p className="text-lg text-base-content/70">No products found in this category</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
