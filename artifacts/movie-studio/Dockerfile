FROM node:20-alpine AS build

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY artifacts/movie-studio/package.json ./artifacts/movie-studio/
COPY lib/ ./lib/

RUN pnpm install --frozen-lockfile --filter @workspace/movie-studio...

COPY artifacts/movie-studio/ ./artifacts/movie-studio/

ENV PORT=3000
ENV BASE_PATH=/

RUN pnpm --filter @workspace/movie-studio run build

FROM nginx:alpine AS production

COPY --from=build /app/artifacts/movie-studio/dist/public /usr/share/nginx/html
COPY --from=build /app/artifacts/movie-studio/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
