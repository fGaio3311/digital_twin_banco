# Dockerfile para o frontend React
FROM node:20-alpine AS deps

WORKDIR /app

# Copia apenas os arquivos necessários para instalar dependências
COPY package*.json ./

# Instala dependências com cache
RUN npm ci --only=production

# Estágio de build
FROM node:20-alpine AS builder

WORKDIR /app

# Copia dependências do estágio anterior
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Configura variáveis de ambiente para otimização
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false

# Build da aplicação com otimizações
RUN npm run build

# Estágio final
FROM nginx:alpine

# Copia os arquivos buildados do estágio builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copia configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Estágio de produção com nginx
FROM nginx:alpine

    # Copia os arquivos buildados
    COPY --from=builder /app/build/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
