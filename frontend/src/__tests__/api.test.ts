import { apiClient } from '@/lib/api';

// Mock the window object and navigation
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

describe('API Client - Session Expiry', () => {
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    mockLocationHref.mockClear();

    // Clear localStorage and cookies
    localStorage.clear();
    document.cookie = '';

    // Set up a mock token
    localStorage.setItem('token', 'mock-jwt-token');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Automatic logout on 401', () => {
    it('should redirect to login when receiving 401 response', async () => {
      // Mock a 401 response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 401,
        ok: false,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      // Make an API call
      try {
        await apiClient.get('/api/v1/user/profile');
      } catch (error) {
        // Expected to throw
      }

      // Check that we were redirected to login
      expect(mockLocationHref).toHaveBeenCalledWith('/login');

      // Check that token was cleared from localStorage
      expect(localStorage.getItem('token')).toBeNull();

      // Check that cookie was cleared
      // Note: document.cookie in jsdom doesn't show expired cookies
      expect(document.cookie).not.toContain('token=mock-jwt-token');
    });

    it('should not redirect on 401 when skipAuth is true', async () => {
      // Mock a 401 response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 401,
        ok: false,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      // Make an API call with skipAuth
      const response = await apiClient.post(
        '/api/v1/auth/login',
        { email: 'test@example.com', password: 'password' },
        { skipAuth: true }
      );

      // Should not redirect
      expect(mockLocationHref).not.toHaveBeenCalled();

      // Token should still be in localStorage
      expect(localStorage.getItem('token')).toBe('mock-jwt-token');
    });

    it('should handle successful authenticated requests', async () => {
      // Mock a successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });

      const response = await apiClient.get('/api/v1/user/profile');

      // Check that the Authorization header was added
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-jwt-token',
          }),
        })
      );

      // Should not redirect
      expect(mockLocationHref).not.toHaveBeenCalled();

      expect(response.ok).toBe(true);
    });

    it('should handle requests without a token', async () => {
      // Clear the token
      localStorage.removeItem('token');

      // Mock a successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });

      const response = await apiClient.get('/api/v1/public/data');

      // Check that no Authorization header was added
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        })
      );

      expect(response.ok).toBe(true);
    });

    it('should clear both localStorage and cookie tokens on 401', async () => {
      // Set token in both places
      localStorage.setItem('token', 'localStorage-token');
      document.cookie = 'token=cookie-token; Path=/;';

      // Mock a 401 response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 401,
        ok: false,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      // Make an API call
      try {
        await apiClient.get('/api/v1/user/profile');
      } catch (error) {
        // Expected to throw
      }

      // Both should be cleared
      expect(localStorage.getItem('token')).toBeNull();
      // Note: document.cookie in jsdom doesn't show expired cookies
      expect(document.cookie).not.toContain('token=cookie-token');
    });
  });

  describe('Token retrieval', () => {
    it('should prefer localStorage token over cookie', async () => {
      // Set different tokens in both places
      localStorage.setItem('token', 'localStorage-token');
      document.cookie = 'token=cookie-token; Path=/;';

      // Mock a successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });

      await apiClient.get('/api/v1/user/profile');

      // Should use localStorage token
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer localStorage-token',
          }),
        })
      );
    });

    it('should fall back to cookie if localStorage is empty', async () => {
      // Clear localStorage but set cookie
      localStorage.removeItem('token');
      document.cookie = 'token=cookie-token; Path=/;';

      // Mock a successful response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });

      await apiClient.get('/api/v1/user/profile');

      // Should use cookie token
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer cookie-token',
          }),
        })
      );
    });
  });
});
