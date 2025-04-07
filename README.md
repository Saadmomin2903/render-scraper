# Facebook Post Scraper API

A FastAPI-based API for scraping Facebook posts and comments using headless browser automation with Playwright.

## Deployment on Render

### Option 1: Deploy via GitHub (Recommended)

1. Push this code to a GitHub repository
2. Log in to [Render.com](https://render.com)
3. Click on "New Web Service"
4. Select "Build and deploy from a Git repository"
5. Connect your GitHub account and select the repository
6. Render will automatically detect the Dockerfile
7. Configure the following:
   - Name: facebook-scraper-api (or any name you prefer)
   - Environment: Docker
   - Branch: main (or your preferred branch)
   - Plan: Free
8. Add environment variables:
   - FB_EMAIL: Your Facebook email
   - FB_PASSWORD: Your Facebook password
9. Click "Create Web Service"

### Option 2: Deploy via Render Blueprint

1. Push this code with the render.yaml file to a GitHub repository
2. Create a new Blueprint in your Render dashboard
3. Connect to your GitHub repository
4. Render will automatically set up the service based on the render.yaml configuration
5. Add your Facebook credentials as environment variables

## API Usage

Once deployed, your API will be available at:
`https://your-service-name.onrender.com/docs`

### Endpoints

- **POST** `/scrape-facebook-post`
  - Request body: `{"post_url": "https://www.facebook.com/..."}`
  - Returns: JSON with post content, comments, and metadata

## Notes on Free Tier Limitations

- The free tier on Render has limited CPU and memory resources
- The service will spin down after periods of inactivity and may take 1-2 minutes to restart
- Consider upgrading to a paid plan for production use if you need:
  - More reliability
  - No spin-down behavior
  - More resources for faster scraping

## Troubleshooting

- If you encounter CAPTCHA issues, you may need to temporarily use a paid plan to use a residential IP
- For persistent errors, check the Render logs in your dashboard
