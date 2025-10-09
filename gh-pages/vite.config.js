import { defineConfig } from "vite";
import { ViteMinifyPlugin } from "vite-plugin-minify";

export default defineConfig({
  // Set the base path for GitHub Pages deployment
  // This should match your repository name
  base: "/cv/",

  // Plugins
  plugins: [
    ViteMinifyPlugin({
      // html-minifier-terser options
      removeComments: true,
      collapseWhitespace: true,
    }),
  ],

  // Build configuration
  build: {
    // Output directory (default is 'dist')
    outDir: "dist",

    // Generate relative paths for assets
    // This ensures assets work when deployed to a subdirectory
    assetsDir: "assets",

    // Minify HTML
    minify: "terser",

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
