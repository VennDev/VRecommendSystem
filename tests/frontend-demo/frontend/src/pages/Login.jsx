import React from 'react'

const Login = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-md mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🔐 Đăng nhập
          </h1>
          <p className="text-gray-600">
            Đăng nhập để nhận gợi ý sản phẩm cá nhân hóa
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-8">
          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tên đăng nhập hoặc Email
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập tên đăng nhập hoặc email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mật khẩu
              </label>
              <input
                type="password"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập mật khẩu"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="rounded border-gray-300" />
                <span className="ml-2 text-sm text-gray-600">Ghi nhớ đăng nhập</span>
              </label>
              <a href="#" className="text-sm text-primary-600 hover:text-primary-700">
                Quên mật khẩu?
              </a>
            </div>

            <button
              type="submit"
              className="w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              Đăng nhập
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h3 className="font-medium text-blue-800 mb-2">🔑 Tài khoản Demo</h3>
              <div className="text-sm text-blue-700 space-y-1">
                <div><strong>Username:</strong> demo_user</div>
                <div><strong>Password:</strong> 123456</div>
              </div>
            </div>

            <div className="text-center">
              <span className="text-gray-600">Chưa có tài khoản?</span>{' '}
              <a href="/register" className="text-primary-600 hover:text-primary-700 font-medium">
                Đăng ký ngay
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
