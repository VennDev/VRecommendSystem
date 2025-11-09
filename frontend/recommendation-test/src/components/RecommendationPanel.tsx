import { useState, useEffect } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import { recommendationService, modelService, productService } from '../services/api';
import { getUserId } from '../utils/session';
import type { Product } from '../types';

interface RecommendationPanelProps {
  onRecommendationsGenerated: () => void;
}

export function RecommendationPanel({ onRecommendationsGenerated }: RecommendationPanelProps) {
  const [models, setModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [numRecommendations, setNumRecommendations] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const modelData = await modelService.listModels();
      const modelList = Object.values(modelData).filter((m: any) => m.status === 'completed');
      setModels(modelList as any[]);
      if (modelList.length > 0) {
        setSelectedModel((modelList[0] as any).model_id);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
      setError('Failed to load models');
    }
  };

  const handleGetRecommendations = async () => {
    if (!selectedModel) {
      setError('Please select a model');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations([]);

    try {
      const userId = getUserId();
      const result = await recommendationService.getRecommendations(
        userId,
        selectedModel,
        numRecommendations
      );

      if (result.data && result.data.recommendations) {
        const productIds = Object.keys(result.data.recommendations);

        if (productIds.length === 0) {
          setError('No recommendations available. Please interact with more products.');
          return;
        }

        const products = await productService.getAll();
        const recommendedProducts = products.filter(p => productIds.includes(p.id));

        const recsWithScores = recommendedProducts.map(p => ({
          ...p,
          score: result.data.recommendations[p.id]
        }));

        recsWithScores.sort((a, b) => b.score - a.score);
        setRecommendations(recsWithScores);

        await recommendationService.saveRecommendations(
          userId,
          productIds.map(id => ({
            product_id: id,
            model_id: selectedModel,
            score: result.data.recommendations[id]
          }))
        );

        onRecommendationsGenerated();
      } else {
        setError('No recommendations returned from the model');
      }
    } catch (err) {
      console.error('Failed to get recommendations:', err);
      setError('Failed to generate recommendations. Make sure you have interacted with some products first.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg p-6 mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="h-6 w-6 text-primary" />
        <h2 className="text-2xl font-bold">Get Personalized Recommendations</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="form-control">
          <label className="label">
            <span className="label-text font-semibold">Select AI Model</span>
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="select select-bordered w-full"
            disabled={loading || models.length === 0}
          >
            {models.length === 0 ? (
              <option>No models available</option>
            ) : (
              models.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {model.model_name} ({model.algorithm})
                </option>
              ))
            )}
          </select>
        </div>

        <div className="form-control">
          <label className="label">
            <span className="label-text font-semibold">Number of Recommendations</span>
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={numRecommendations}
            onChange={(e) => setNumRecommendations(parseInt(e.target.value) || 5)}
            className="input input-bordered w-full"
            disabled={loading}
          />
        </div>

        <div className="form-control">
          <label className="label">
            <span className="label-text">&nbsp;</span>
          </label>
          <button
            onClick={handleGetRecommendations}
            disabled={loading || !selectedModel}
            className="btn btn-primary w-full gap-2"
          >
            {loading ? (
              <>
                <span className="loading loading-spinner loading-sm"></span>
                Generating...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Get Recommendations
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-bold mb-4">Your Personalized Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {recommendations.map((product: any, index) => (
              <div key={product.id} className="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
                <figure className="relative h-32">
                  <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                  <div className="absolute top-2 left-2 badge badge-primary">
                    #{index + 1}
                  </div>
                  <div className="absolute top-2 right-2 badge badge-success">
                    {(product.score * 100).toFixed(0)}%
                  </div>
                </figure>
                <div className="card-body p-3">
                  <h4 className="font-semibold text-sm line-clamp-1">{product.name}</h4>
                  <p className="text-xs text-base-content/70">{product.category}</p>
                  <p className="text-sm font-bold text-primary">${product.price.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
