// User types
export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
  username?: string;
  full_name?: string;
}

// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  confirm_password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
}

// Booking types
export interface Booking {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  studio?: string;
  location?: string;
  status: string;
  price?: number;
  record_url?: string;
  created_at?: string;
  updated_at?: string;
}

// Credentials types
export interface Credentials {
  gibney_email?: string;
  gibney_password?: string;
  outlook_email?: string;
  outlook_password?: string;
}

export interface CredentialsFormData {
  gibney_email: string;
  gibney_password: string;
}

// Component prop types
export interface LoginProps {
  onLogin: (token: string, userData: User) => void;
}

export interface RegisterProps {
  onLogin: (token: string, userData: User) => void;
}

export interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

export interface DashboardProps {
  user: User;
}

export interface CredentialsProps {
  user: User;
}

// Form state types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData extends LoginFormData {
  confirmPassword: string;
}

// API function types
export type ApiFunction<T = any> = (...args: any[]) => Promise<T>;