const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface ApiOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private static instance: ApiClient;

  private constructor() {}

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') {
      // Server-side: can't access localStorage or document.cookie
      return null;
    }

    // Try localStorage first (for client-side)
    const localToken = localStorage.getItem('token');
    if (localToken) return localToken;

    // Fall back to cookies
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('token='))
      ?.split('=')[1];
    return token || null;
  }

  private handleAuthError() {
    // Clear authentication data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      document.cookie =
        'token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';

      // Redirect to login
      window.location.href = '/login';
    }
  }

  async fetch(endpoint: string, options: ApiOptions = {}): Promise<Response> {
    const { skipAuth = false, headers = {}, ...restOptions } = options;

    const requestHeaders: Record<string, string> = {
      ...(headers as Record<string, string>),
    };

    // Add auth header if not skipped
    if (!skipAuth) {
      const token = this.getToken();
      if (token) {
        requestHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const url = `${API_BASE}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...restOptions,
        headers: requestHeaders,
      });

      // Handle authentication errors
      if (response.status === 401 && !skipAuth) {
        this.handleAuthError();
        throw new Error('Authentication required');
      }

      return response;
    } catch (error) {
      // Re-throw the error after handling
      throw error;
    }
  }

  // Convenience methods
  async get(endpoint: string, options?: ApiOptions): Promise<Response> {
    return this.fetch(endpoint, { ...options, method: 'GET' });
  }

  async post(
    endpoint: string,
    body?: any,
    options?: ApiOptions
  ): Promise<Response> {
    const config: ApiOptions = {
      ...options,
      method: 'POST',
    };

    if (body) {
      if (body instanceof FormData || body instanceof URLSearchParams) {
        config.body = body;
      } else {
        config.headers = {
          'Content-Type': 'application/json',
          ...config.headers,
        };
        config.body = JSON.stringify(body);
      }
    }

    return this.fetch(endpoint, config);
  }

  async put(
    endpoint: string,
    body?: any,
    options?: ApiOptions
  ): Promise<Response> {
    const config: ApiOptions = {
      ...options,
      method: 'PUT',
    };

    if (body) {
      config.headers = {
        'Content-Type': 'application/json',
        ...config.headers,
      };
      config.body = JSON.stringify(body);
    }

    return this.fetch(endpoint, config);
  }

  async delete(endpoint: string, options?: ApiOptions): Promise<Response> {
    return this.fetch(endpoint, { ...options, method: 'DELETE' });
  }
}

// Export singleton instance
export const apiClient = ApiClient.getInstance();
