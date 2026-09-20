/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_BACKEND_URL?: string;
  readonly VITE_DEV_SCREENSHOT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
