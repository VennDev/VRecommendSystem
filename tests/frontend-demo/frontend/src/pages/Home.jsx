import React from 'react'

const Home = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 VRecommendation Demo
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Hệ thống gợi ý sản phẩm thông minh sử dụng AI để đưa ra những gợi ý cá nhân hóa dựa trên hành vi và sở thích của bạn.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/products"
              className="bg-primary-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
            >
              Xem sản phẩm
            </a>
            <a
              href="/login"
              className="border border-primary-600 text-primary-600 px-8 py-3 rounded-lg font-medium hover:bg-primary-50 transition-colors"
            >
              Đăng nhập để có gợi ý cá nhân
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Gợi ý chính xác
            </h3>
            <p className="text-gray-600">
              AI phân tích hành vi và đưa ra gợi ý sản phẩm phù hợp với sở thích của bạn.
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Thời gian thực
            </h3>
            <p className="text-gray-600">
              Gợi ý được cập nhật liên tục dựa trên các tương tác mới nhất của bạn.
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="text-4xl mb-4">🔒</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Bảo mật dữ liệu
            </h3>
            <p className="text-gray-600">
              Thông tin cá nhân được bảo vệ và chỉ sử dụng để cải thiện trải nghiệm.
            </p>
          </div>
        </div>

        {/* Demo Stats */}
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Demo Statistics
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div>
              <div className="text-3xl font-bold text-primary-600">12</div>
              <div className="text-gray-600">Sản phẩm demo</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">6</div>
              <div className="text-gray-600">Danh mục</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">4</div>
              <div className="text-gray-600">Người dùng demo</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">AI</div>
              <div className="text-gray-600">Gợi ý thông minh</div>
            </div>
          </div>
        </div>

        {/* Getting Started */}
        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Bắt đầu với VRecommendation
          </h2>
          <div className="max-w-3xl mx-auto">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex flex-col items-center">
                <div className="bg-primary-100 w-12 h-12 rounded-full flex items-center justify-center mb-3">
                  <span className="text-primary-600 font-bold">1</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Đăng ký tài khoản</h3>
                <p className="text-gray-600 text-sm">Tạo tài khoản để bắt đầu nhận gợi ý cá nhân hóa</p>
              </div>
              <div className="flex flex-col items-center">
                <div className="bg-primary-100 w-12 h-12 rounded-full flex items-center justify-center mb-3">
                  <span className="text-primary-600 font-bold">2</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Tương tác với sản phẩm</h3>
                <p className="text-gray-600 text-sm">Like, xem và tương tác với các sản phẩm yêu thích</p>
              </div>
              <div className="flex flex-col items-center">
                <div className="bg-primary-100 w-12 h-12 rounded-full flex items-center justify-center mb-3">
                  <span className="text-primary-600 font-bold">3</span>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Nhận gợi ý AI</h3>
                <p className="text-gray-600 text-sm">Xem gợi ý sản phẩm được cá nhân hóa cho bạn</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
