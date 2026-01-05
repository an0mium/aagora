import { renderHook, act } from '@testing-library/react';
import { useAuthToken } from '@/hooks/useAuthToken';

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

// Helper to set URL search params
const setUrlParams = (params: string) => {
  Object.defineProperty(window, 'location', {
    value: { search: params },
    writable: true,
  });
};

describe('useAuthToken', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStorage.clear();
    setUrlParams('');
  });

  describe('initial state', () => {
    it('should return null token when no token is available', () => {
      const { result } = renderHook(() => useAuthToken());

      expect(result.current.token).toBeNull();
    });

    it('should return empty auth headers when no token', () => {
      const { result } = renderHook(() => useAuthToken());

      expect(result.current.getAuthHeaders()).toEqual({});
    });

    it('should return empty query param when no token', () => {
      const { result } = renderHook(() => useAuthToken());

      expect(result.current.getAuthQueryParam()).toBe('');
    });
  });

  describe('token from URL parameters', () => {
    it('should extract token from URL params', async () => {
      setUrlParams('?token=test-token-123');

      const { result } = renderHook(() => useAuthToken());

      // Wait for useEffect to run
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.token).toBe('test-token-123');
    });

    it('should store URL token in sessionStorage', async () => {
      setUrlParams('?token=persist-me');

      renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'aragora_auth_token',
        'persist-me'
      );
    });

    it('should handle URL token with special characters', async () => {
      setUrlParams('?token=abc%3D123%26key');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.token).toBe('abc=123&key');
    });
  });

  describe('token from sessionStorage', () => {
    it('should load token from sessionStorage when no URL param', async () => {
      mockSessionStorage.getItem.mockReturnValue('stored-token');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.token).toBe('stored-token');
    });

    it('should prefer URL token over sessionStorage', async () => {
      mockSessionStorage.getItem.mockReturnValue('old-stored-token');
      setUrlParams('?token=new-url-token');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.token).toBe('new-url-token');
    });
  });

  describe('getAuthHeaders', () => {
    it('should return Authorization header with Bearer token', async () => {
      setUrlParams('?token=bearer-token');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.getAuthHeaders()).toEqual({
        'Authorization': 'Bearer bearer-token',
      });
    });
  });

  describe('getAuthQueryParam', () => {
    it('should return encoded query param', async () => {
      setUrlParams('?token=test-token');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.getAuthQueryParam()).toBe('token=test-token');
    });

    it('should properly encode special characters', async () => {
      mockSessionStorage.getItem.mockReturnValue('token=with&special');

      const { result } = renderHook(() => useAuthToken());

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(result.current.getAuthQueryParam()).toBe('token=token%3Dwith%26special');
    });
  });
});
