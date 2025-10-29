import api from './api';

export interface User {
  id: number;
  email: string;
  full_name: string;
  token: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export const authService = {
  async login(email: string, password: string): Promise<User> {
    // Backend uses OAuth2PasswordRequestForm which expects form-data
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post<LoginResponse>('/token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // Decode JWT to get user info
    const token = response.data.access_token;
    const userData = JSON.parse(atob(token.split('.')[1]));
    
    return {
      id: parseInt(userData.sub || '0'),
      email: userData.sub || email,
      full_name: '',
      token: token,
    };
  },

  async register(email: string, password: string, fullName?: string): Promise<User> {
    const response = await api.post<UserResponse>('/users/', { 
      email, 
      password,
      full_name: fullName || email.split('@')[0],
    });
    
    // After registration, automatically log in
    return await this.login(email, password);
  },
};
