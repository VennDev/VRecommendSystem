import { authService } from '../services/api';

export async function ensureUser(): Promise<string> {
  let user = localStorage.getItem('test_user');

  if (!user) {
    const username = `user_${Date.now()}`;
    const response = await authService.login(username);
    user = JSON.stringify(response.user);
    localStorage.setItem('test_user', user);
  }

  const userData = JSON.parse(user);
  return userData.id;
}

export function getUser(): any | null {
  const user = localStorage.getItem('test_user');
  return user ? JSON.parse(user) : null;
}

export function clearUser(): void {
  localStorage.removeItem('test_user');
}
