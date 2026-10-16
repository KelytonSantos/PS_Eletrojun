# 📱 Como Gerar e Instalar o APK (.apk)

Guia rápido e passo a passo para compilar o aplicativo Android com o Capacitor e testar no celular.

---

## ⚡ Comandos Rápidos (Direto pelo Terminal)

Na raiz do projeto (`/home/lucas/Documents/front_PS`), execute:

```bash
# 1. Sincroniza as alterações do front (HTML/CSS/JS) com o Android
npx cap sync android

# 2. Compila e gera o arquivo .apk de depuração
cd android && ./gradlew assembleDebug && cd ..
```

---

## 📍 Onde fica o arquivo `.apk` gerado?

O arquivo compilado estará em:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 📲 Como Instalar no Celular

### Opção 1: Direto pelo Cabo USB (Mais rápido)
Com o celular conectado no computador e a **Depuração USB** ativada:

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### Opção 2: Sem Cabos (WhatsApp, Drive ou Telegram)
1. Pegue o arquivo `app-debug.apk`.
2. Envie para você mesmo pelo WhatsApp Web, Telegram ou salve no Google Drive.
3. No celular, clique no arquivo e selecione **Instalar** (permita a instalação de fontes desconhecidas se o Android solicitar).

---

## 🌐 Como Usar na Apresentação (com o Ngrok)

Para o app funcionar em qualquer lugar (4G, Wi-Fi da UnB, etc.):

1. **Suba o backend no computador**:
   ```bash
   cd /home/lucas/Desktop/HailMary/Eletrojun/project_struct
   docker compose up -d
   ```

2. **Inicie o túnel do Ngrok**:
   ```bash
   ngrok http 8080 --url undecadently-incalescent-sabra.ngrok-free.dev
   ```

3. **Abra o app no celular**:
   - O app já está configurado para acessar automaticamente o seu domínio fixo do Ngrok:  
     `https://undecadently-incalescent-sabra.ngrok-free.dev`
   - Se precisar alterar ou conferir, vá na aba **Config.** do aplicativo no celular.

---

## 🛠️ Abrir no Android Studio (Opcional)

Se preferir usar a interface visual do Android Studio:

```bash
npx cap open android
```
No Android Studio: clique em **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
