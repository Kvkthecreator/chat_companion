# Vercel Deployment (Frontend)

## Prerequisites

- Vercel account
- GitHub repository connected to Vercel
- Backend API deployed (see [RENDER.md](RENDER.md))

## Deployment Steps

### 1. Import Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Select the `web` directory as the root

### 2. Configure Build Settings

| Setting | Value |
|---------|-------|
| Framework Preset | Next.js |
| Root Directory | `web` |
| Build Command | `npm run build` |
| Output Directory | `.next` |

### 3. Environment Variables

Add these in Vercel dashboard → Settings → Environment Variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://gncuzrstnmwhghzoyllo.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API URL
NEXT_PUBLIC_API_URL=https://chat-companion-api.onrender.com

# Site URL (update after first deploy)
NEXT_PUBLIC_SITE_URL=https://your-app.vercel.app
```

### 4. Deploy

Click "Deploy" - Vercel will build and deploy automatically.

## Post-Deployment

### Update CORS on API

Add your Vercel URL to the API's CORS_ORIGINS in Render:

```
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

### Verify Deployment

1. Visit your Vercel URL
2. Sign up / log in
3. Complete onboarding
4. Send a test message

## Custom Domain

1. Go to Vercel dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `NEXT_PUBLIC_SITE_URL` environment variable

## Troubleshooting

### Build fails
- Check Node.js version matches local (18+)
- Ensure all dependencies are in package.json
- Check for TypeScript errors

### API calls fail
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS is configured on API
- Inspect browser console for errors

### Auth not working
- Verify Supabase keys are correct
- Check Supabase Auth settings allow your domain
- Add Vercel URL to Supabase Auth → URL Configuration
