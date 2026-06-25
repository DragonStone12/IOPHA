/// <reference types="vite/client" />

declare global {
  interface ImportMeta {
    readonly env: {
      readonly DEV: boolean;
      readonly PROD: boolean;
      readonly BASE_URL: string;
    };
  }
}
