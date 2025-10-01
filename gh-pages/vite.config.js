import { defineConfig } from "vite";

export default defineConfig({
  // Set the base path for GitHub Pages deployment
  // This should match your repository name
  base: "/cv/",

  // Build configuration
  build: {
    // Output directory (default is 'dist')
    outDir: "dist",

    // Generate relative paths for assets
    // This ensures assets work when deployed to a subdirectory
    assetsDir: "assets",

    // Rollup options for build optimization
    rollupOptions: {
      input: {
        main: "index.html",
      },
    },

    // Copy additional files that Vite doesn't process automatically
    copyPublicDir: true,
  },

  // Development server configuration
  server: {
    port: 3000,
    open: true,
  },

  // Public directory configuration
  publicDir: "public",

  // Asset handling
  assetsInclude: ["**/*.pdf", "**/*.wasm"],
});
