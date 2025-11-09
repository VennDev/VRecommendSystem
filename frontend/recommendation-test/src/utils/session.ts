export function getUserId(): string {
  let userId = localStorage.getItem('test_user_id');

  if (!userId) {
    userId = `user_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
    localStorage.setItem('test_user_id', userId);
  }

  return userId;
}

export function clearUserId(): void {
  localStorage.removeItem('test_user_id');
}
