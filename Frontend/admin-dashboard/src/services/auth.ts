import { get, post, MOCK_MODE } from './api';
import type { User, TokenOut } from '../models';
import { mockUser, mockToken } from '../mocks';

export interface LoginParams { email: string; password: string; }

export async function login(params: LoginParams): Promise<TokenOut> {
  if (MOCK_MODE) return mockToken();
  return post<TokenOut>('/api/v1/auth/login', params);
}

export async function getMe(): Promise<User> {
  if (MOCK_MODE) return mockUser();
  return get<User>('/api/v1/auth/me');
}
