# Inversión Online

Estamos haciendo un proyecto de una página para invertir online al estilo IOL.  Asi que hace una pagina web para este tipo de aplicacion en Type script y deja los enpoints comentados para completarlos más tarde

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/43efba98-3673-4451-8203-0b0aab1ee6d4).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

For local development, leave `VITE_API_URL` empty and run the backend on
`http://127.0.0.1:8000`. Vite proxies `/api` requests to the backend, so the
browser uses the frontend's origin and does not need cross-origin CORS access.

On Windows, run `start-dev.bat` from the repository root. From another device
on the same network, open `http://<IP-LAN-de-esta-PC>:5173`. If the page cannot
be reached, allow the frontend's port through Windows Firewall on the private
network. Do not set `VITE_API_URL` to `127.0.0.1` for this setup: that address
would refer to the other device itself.
