/**
 * Integration test for authentication flow and automatic logout
 */

import { apiClient } from '@/lib/api';

// Mock window.location
const mockLocationHref = jest.fn();
Object.defineProperty(window, 'location', {
  value: {
    get href() {
      return 'http://localhost:3000/dashboard';
    },
    set href(value) {
      mockLocationHref(value);
    },
  },
  writable: true,
});

// Mock fetch
global.fetch = jest.fn();

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocationHref.mockClear();
    localStorage.clear();
    document.cookie = '';
  });

  it('should handle complete authentication flow', async () => {
    // 1. User logs in successfully
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      ok: true,
      json: async () => ({
        access_token: 'valid-jwt-token',
        token_type: 'bearer',
      }),
    });

    const loginResponse = await apiClient.post(
      '/api/v1/auth/token',
      new URLSearchParams({
        username: 'test@example.com',
        password: 'password123',
      }),
      { skipAuth: true }
    );

    expect(loginResponse.ok).toBe(true);
    const loginData = await loginResponse.json();

    // Store the token (normally done by Login component)
    localStorage.setItem('token', loginData.access_token);
    document.cookie = `token=${loginData.access_token}; path=/`;

    // 2. User makes authenticated requests successfully
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      ok: true,
      json: async () => ({
        id: '1',
        email: 'test@example.com',
        bookings: [],
      }),
    });

    const profileResponse = await apiClient.get('/api/v1/user/profile');
    expect(profileResponse.ok).toBe(true);

    // Verify auth header was sent
    expect(global.fetch).toHaveBeenLastCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer valid-jwt-token',
        }),
      })
    );

    // 3. Session expires and API returns 401
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 401,
      ok: false,
      json: async () => ({ detail: 'Token expired' }),
    });

    // Make another request that will fail with 401
    try {
      await apiClient.get('/api/v1/user/bookings');
    } catch (error) {
      expect((error as Error).message).toBe('Authentication required');
    }

    // 4. Verify automatic logout behavior
    expect(mockLocationHref).toHaveBeenCalledWith('/login');
    expect(localStorage.getItem('token')).toBeNull();
    expect(document.cookie).not.toContain('valid-jwt-token');
  });

  it('should handle authentication flow with cookie-based token', async () => {
    // Set token only in cookie
    document.cookie = 'token=cookie-jwt-token; path=/';

    // Make authenticated request
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      ok: true,
      json: async () => ({ data: 'success' }),
    });

    const response = await apiClient.get('/api/v1/user/profile');
    expect(response.ok).toBe(true);

    // Verify cookie token was used
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer cookie-jwt-token',
        }),
      })
    );

    // Session expires
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 401,
      ok: false,
      json: async () => ({ detail: 'Token expired' }),
    });

    try {
      await apiClient.get('/api/v1/user/data');
    } catch (error) {
      // Expected
    }

    // Verify logout
    expect(mockLocationHref).toHaveBeenCalledWith('/login');
    expect(document.cookie).not.toContain('cookie-jwt-token');
  });

  it('should not interfere with public endpoints', async () => {
    // No token set

    // Access public endpoint
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      ok: true,
      json: async () => ({ message: 'Public data' }),
    });

    const response = await apiClient.get('/api/v1/public/info', {
      skipAuth: true,
    });

    expect(response.ok).toBe(true);
    expect(mockLocationHref).not.toHaveBeenCalled();

    // Verify no auth header was sent
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.not.objectContaining({
          Authorization: expect.anything(),
        }),
      })
    );
  });
});
