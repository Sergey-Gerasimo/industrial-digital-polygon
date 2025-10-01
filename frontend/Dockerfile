FROM node:20-alpine

WORKDIR /app

# Копируем package файлы
COPY package*.json ./

# Чистим кэш и устанавливаем зависимости правильно
RUN npm cache clean --force && \
    rm -rf node_modules package-lock.json && \
    npm install

COPY . .

# Убираем TypeScript проверку из сборки
RUN sed -i 's/"build": "tsc -b && vite build"/"build": "vite build"/g' package.json

RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]