/* global self, Response */

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (
    request.mode !== "navigate" ||
    request.method !== "GET" ||
    url.origin !== self.location.origin ||
    url.pathname === "/api" ||
    url.pathname.startsWith("/api/")
  ) {
    return;
  }

  event.respondWith(
    fetch(request).catch(
      () =>
        new Response(
          `<!doctype html>
<html lang="es-AR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b0e15">
<title>Sin conexión | Invertix</title>
<style>
  body { color-scheme: dark; background: #0b0e15; color: #fff; font: 1rem system-ui; margin: 0; }
  main { max-width: 28rem; margin: 15vh auto; padding: 1.5rem; }
  button { font: inherit; padding: .6rem 1rem; }
</style>
<main>
  <h1>Sin conexión</h1>
  <p>Conectate a internet para acceder a Invertix.</p>
  <form method="get" action="/"><button>Volver a intentar</button></form>
</main>
</html>`,
          { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } },
        ),
    ),
  );
});
