import '@testing-library/jest-dom';

// Mock Next.js dynamic imports
jest.mock('next/dynamic', () => func => {
  const DynamicComponent = (...args) => {
    const component = func();
    if (component.then) {
      return component.then(mod => mod.default || mod);
    }
    return component.default || component;
  };
  DynamicComponent.displayName = 'DynamicComponent';
  return DynamicComponent;
});

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    };
  },
}));

// Mock environment variables
process.env.NEXT_PUBLIC_API_BASE = 'http://localhost:8000';
