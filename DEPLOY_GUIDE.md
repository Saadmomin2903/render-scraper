# Step-by-Step Deployment Guide for Facebook Scraper on Render

## Prerequisites

- A GitHub account
- A Render.com account (free tier is fine)

## Step 1: Prepare Your Local Repository

The repository has already been set up with:

- Dockerfile
- requirements.txt
- render.yaml
- main3.py (the scraper code)

## Step 2: Push to GitHub

1. Create a new repository on GitHub
2. Add the GitHub repository as a remote:

```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy on Render

1. Log in to your Render account at https://dashboard.render.com/
2. Click "New +" in the top right corner and select "Web Service"
3. Connect your GitHub account if you haven't already
4. Select the repository you just created
5. Render will automatically detect the Dockerfile
6. Configure the following settings:
   - **Name**: `facebook-scraper-api` (or any name you prefer)
   - **Environment**: Docker
   - **Region**: Choose the region closest to you
   - **Branch**: main
   - **Plan**: Free

## Step 4: Configure Environment Variables

1. Scroll down to the "Environment" section
2. Add the following environment variables:
   - `FB_EMAIL`: Your Facebook email/username
   - `FB_PASSWORD`: Your Facebook password

## Step 5: Deploy the Service

1. Click "Create Web Service"
2. Render will start building and deploying your application
3. The initial build may take 5-10 minutes
4. Once deployed, you'll see a URL like `https://facebook-scraper-api.onrender.com`

## Step 6: Test Your API

1. Open your browser and go to `https://facebook-scraper-api.onrender.com/docs`
2. You should see the FastAPI Swagger documentation
3. Test the `/scrape-facebook-post` endpoint with a Facebook post URL

## Troubleshooting

- **Build fails**: Check the build logs for errors
- **CAPTCHA issues**: Facebook may detect the scraper as a bot; try logging in manually first
- **Service crashes**: Check the logs in Render dashboard
- **Slow performance**: This is expected on the free tier; the service will spin down after inactivity

## Monitoring and Maintenance

- Check the Render dashboard for service status and logs
- The service will spin down after inactivity on the free tier
- The first request after inactivity may take 1-2 minutes to complete

## Upgrading

If you need better performance:

1. Go to your service in the Render dashboard
2. Click "Change Plan"
3. Select a paid plan with more resources
