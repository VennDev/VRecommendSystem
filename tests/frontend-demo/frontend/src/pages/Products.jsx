import React from 'react'

const Products = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🛍️ Sản phẩm
          </h1>
          <p className="text-gray-600 mb-8">
            Trang sản phẩm đang được phát triển...
          </p>
          <div className="bg-white rounded-lg shadow-sm p-8">
            <div className="text-4xl mb-4">🚧</div>
            <p className="text-gray-500">
              Component này sẽ hiển thị danh sách sản phẩm với tính năng tìm kiếm, lọc và phân trang.
            </p>
            <div className="mt-6">
              <a
                href="/"
                className="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
              >
                Về trang chủ
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Products
