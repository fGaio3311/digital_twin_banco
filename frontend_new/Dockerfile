# Dockerfile para o frontend React
FROM node:20-alpine AS build

WORKDIR /app

# Copia package.json e package-lock.json (se existir)
COPY package*.json ./

# Instala dependências (usando npm install para resolver incompatibilidades)
RUN npm install

# Copia o código fonte
COPY . .

# Build da aplicação
RUN npm run build

# Estágio de produção com nginx
FROM nginx:alpine

# Copia os arquivos buildados
COPY --from=build /app/build /usr/share/nginx/html

# Copia configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
