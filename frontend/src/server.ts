const server = Bun.serve({
  port: 3000,
  async fetch(request) {
    const url = new URL(request.url);

    // Proxy requests to the backend
    if (
      url.pathname.startsWith('/pixels') ||
      url.pathname.startsWith('/session') ||
      url.pathname.startsWith('/ws')
    ){
      const target = `http://backend:8000${url.pathname}${url.search}`;

      return fetch(
        target,
        {
          method: request.method,
          headers: request.headers,
          body: request.body
        }
      )
    }

    // Serve static files for the frontend
    const filepath = url.pathname === '/'
      ? "./src/index.html"
      : `./src${url.pathname}`;

    const file = Bun.file(filepath);
    if (await file.exists()) {
      return new Response(file);
    }

    return new Response('Not Found', { status: 404 });
  },
});

console.log(`Frontend running on http://localhost:${server.port}`);
