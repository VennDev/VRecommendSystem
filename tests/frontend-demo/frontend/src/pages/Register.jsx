import React from 'react'

const Register = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-md mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            📝 Đăng ký
          </h1>
          <p className="text-gray-600">
            Tạo tài khoản để bắt đầu nhận gợi ý sản phẩm AI
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-8">
          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tên đăng nhập
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập tên đăng nhập"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập địa chỉ email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Họ và tên
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập họ và tên"
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Xác nhận mật khẩu
              </label>
              <input
                type="password"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Nhập lại mật khẩu"
              />
            </div>

            <div className="flex items-center">
              <input type="checkbox" className="rounded border-gray-300" />
              <span className="ml-2 text-sm text-gray-600">
                Tôi đồng ý với{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  Điều khoản sử dụng
                </a>{' '}
                và{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  Chính sách bảo mật
                </a>
              </span>
            </div>

            <button
              type="submit"
              className="w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              Đăng ký tài khoản
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-200 text-center">
            <span className="text-gray-600">Đã có tài khoản?</span>{' '}
            <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Đăng nhập ngay
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register
