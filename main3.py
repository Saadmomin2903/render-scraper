from fastapi import FastAPI, HTTPException, Body
from typing import Dict
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import uvicorn
from pydantic import BaseModel, Field
import os

app = FastAPI(
    title="Facebook Post Scraper API",
    description="API to scrape Facebook posts and comments using stored credentials",
    version="1.0.0"
)

# Hardcoded Facebook credentials as secrets
# For better security, you can use environment variables instead
FB_CREDENTIALS = {
    "email": os.environ.get("FB_EMAIL", "saadmomin5555@gmail.com"),
    "password": os.environ.get("FB_PASSWORD", "Saad@2903")
}

# Input model for better API documentation
class PostRequest(BaseModel):
    post_url: str = Field(..., description="URL of the Facebook post to scrape")

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "Facebook Post Scraper API"}

@app.post("/scrape-facebook-post", 
         description="Scrape a Facebook post and its comments using stored credentials")
async def get_facebook_comments(request: PostRequest):
    # Get the post URL from the request
    post_url = request.post_url
    
    # Use the hardcoded credentials
    email = FB_CREDENTIALS["email"]
    password = FB_CREDENTIALS["password"]

    # Start the browser session
    async with async_playwright() as p:
        # Use headless mode but with additional configurations to avoid detection
        browser = await p.chromium.launch(
            headless=True,  
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                # Optimize for Render's resources
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-jpeg-decoding',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-decode',
                '--single-process',
                # Memory optimization
                '--js-flags="--max-old-space-size=460"',
                # Original anti-bot args
                '--disable-infobars',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-component-extensions-with-background-pages',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--mute-audio',
            ]
        )
        
        # Create a context with more realistic browser parameters
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},  # Smaller viewport to save memory
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            is_mobile=False,
            has_touch=False,
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            java_script_enabled=True,
            bypass_csp=True,
        )
        
        # Enable JavaScript console logging
        context.on('console', lambda msg: print(f'BROWSER LOG: {msg.text}'))
        
        page = await context.new_page()

        # Add script to remove navigator.webdriver flag
        await page.add_init_script('''() => {
            // Overwrite the 'webdriver' property to undefined
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite the chrome driver related properties
            window.navigator.chrome = { runtime: {} };
            
            // Overwrite the permissions API
            window.navigator.permissions = {
                query: () => Promise.resolve({ state: 'granted' })
            };
            
            // Add missing plugins that a normal browser would have
            const originalPlugins = navigator.plugins;
            const pluginsData = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ];
            
            // Define a new plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = { 
                        ...originalPlugins,
                        length: pluginsData.length 
                    };
                    
                    // Add the missing plugins
                    pluginsData.forEach((plugin, i) => {
                        plugins[i] = plugin;
                    });
                    
                    return plugins;
                }
            });
            
            // Fake the language property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Fake the platform to match a Mac
            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel'
            });
            
            // Add a fake notification API
            if (window.Notification) {
                window.Notification.permission = 'default';
            }
        }''')

        try:
            # Step 1: Login to Facebook
            await page.goto('https://www.facebook.com/', timeout=60000)
            
            # Wait for page to fully load
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # Additional delay
            
            # Accept cookies if present
            try:
                cookie_button = await page.query_selector('button[data-cookiebanner="accept_button"]')
                if cookie_button:
                    await cookie_button.click()
                    await asyncio.sleep(1)
            except Exception:
                print('No cookie banner found')

            # Login
            await page.fill('#email', email)
            await page.fill('#pass', password)
            
            # Click login button
            await page.click('button[name="login"]')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # Check for CAPTCHA or checkpoint
            if 'checkpoint' in page.url:
                print("Detected checkpoint/CAPTCHA page")
                # Wait for user to manually solve CAPTCHA - longer timeout
                await asyncio.sleep(30)  # Give 30 seconds for manual CAPTCHA solving
                
                # Wait for navigation after CAPTCHA is solved
                await page.wait_for_load_state('networkidle')
                
                # Check if we're still on checkpoint page
                if 'checkpoint' in page.url:
                    raise HTTPException(status_code=401, detail='CAPTCHA/checkpoint not solved in time. Please try again.')

            # Check login success
            if 'login' in page.url:
                raise HTTPException(status_code=401, detail='Login failed - Please check credentials')

            # Step 2: Scrape the post and comments
            print(f"Navigating to post URL: {post_url}")
            await page.goto(post_url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)  # Wait longer for all elements to load

            # Get post content
            post_data = await page.evaluate('''() => {
                // Try to get the post description directly from where Facebook actually stores it
                const getPostDescription = () => {
                    // First approach: Get the full text content from the post container
                    const postContainer = document.querySelector('.xjkvuk6, .xuyqlj2');
                    if (postContainer) {
                        // Get all text content divs in the post container
                        const textDivs = Array.from(postContainer.querySelectorAll('div[dir="auto"]'))
                            .map(el => el.textContent.trim())
                            .filter(text => text.length > 10 && !text.includes('See more') && !text.includes('See less'));
                        
                        // Get the full post content by joining all text segments (this gets the complete text even if split across divisions)
                        if (textDivs.length > 0) {
                            return textDivs.join(' ');
                        }
                    }
                    
                    // Second approach: Look for specific post wrapper divs by their class names
                    const wrapperSelectors = [
                        'div.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs',
                        'div.x78zum5.xdt5ytf.x4cne27.xifccgj',
                        'div.xzueoph.x1k70j0n',
                        'div.x1n2onr6'
                    ];
                    
                    for (const selector of wrapperSelectors) {
                        const wrappers = document.querySelectorAll(selector);
                        for (const wrapper of wrappers) {
                            const texts = Array.from(wrapper.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
                                .map(el => el.textContent.trim())
                                .filter(text => 
                                    text.length > 30 && 
                                    !text.includes('See more') && 
                                    !text.includes('See less') &&
                                    !text.includes('#') // Avoid hashtag sections
                                );
                            
                            if (texts.length > 0) {
                                // Sort by length and get the longest text
                                return texts.sort((a, b) => b.length - a.length)[0];
                            }
                        }
                    }
                    
                    // Third approach: look for any lengthy content in the first article element (likely the post itself)
                    const firstArticle = document.querySelector('div[role="article"]');
                    if (firstArticle) {
                        const articleTexts = Array.from(firstArticle.querySelectorAll('div[dir="auto"]'))
                            .map(el => el.textContent.trim())
                            .filter(text => 
                                text.length > 40 && 
                                !text.includes('See more') && 
                                !text.includes('See less')
                            );
                        
                        if (articleTexts.length > 0) {
                            // Sort by length to get the most substantial content
                            return articleTexts.sort((a, b) => b.length - a.length)[0];
                        }
                    }
                    
                    // Final fallback: any meaningful content on the page
                    const allTextElements = Array.from(document.querySelectorAll('div[dir="auto"]'));
                    const allTexts = allTextElements
                    .map(el => el.textContent.trim())
                        .filter(text => text.length > 50);
                        
                    if (allTexts.length > 0) {
                        return allTexts.sort((a, b) => b.length - a.length)[0];
                    }
                    
                    return '';
                };

                return {
                    post_content: getPostDescription(),
                    post_url: window.location.href
                };
            }''')

            # Step 3: Expand all comments using multiple strategies
            max_attempts = 10  # Reduced from 20 to save resources
            attempts = 0
            total_clicks = 0
            last_comment_count = 0
            
            while attempts < max_attempts:
                # Get current comment count to check if we're making progress
                current_comment_count = await page.evaluate('''() => {
                    return document.querySelectorAll('div[role="article"]').length;
                }''')
                
                print(f"Current comment count: {current_comment_count}")
                
                if current_comment_count == last_comment_count and attempts > 3:  # Reduced from 5 to save resources
                    print("No new comments loaded after several attempts, stopping")
                    break
                    
                last_comment_count = current_comment_count
                
                # More efficient scrolling strategy for headless mode
                await page.evaluate('''() => {
                    // Scroll down once with small pause
                    window.scrollTo(0, document.body.scrollHeight);
                    return true;
                }''')
                await asyncio.sleep(2)

                # First strategy: Use standard querySelector methods with text content checking
                click_happened = await page.evaluate('''() => {
                    // Function to simulate human-like clicking
                    const humanClick = (element) => {
                        element.click();
                        return true;
                    };
                    
                    // Try to find spans with the specific text content
                    const allSpans = Array.from(document.querySelectorAll('span'));
                    
                    // Look for spans with the exact class from the example
                    const targetSpans = allSpans.filter(span => {
                        const hasClass = span.className.includes('x193iq5w');
                        const hasText = span.textContent.includes('View more comments') || 
                                       span.textContent.includes('Previous comments');
                        return hasClass && hasText;
                    });
                    
                    // If we found target spans with the right class, try to click their parent buttons
                    if (targetSpans.length > 0) {
                        for (const span of targetSpans) {
                            const clickable = span.closest('div[role="button"]');
                            if (clickable) {
                                console.log("Found clickable with x193iq5w class");
                                clickable.scrollIntoView({behavior: "auto", block: "center"});
                                return humanClick(clickable);
                            }
                        }
                    }
                    
                    // Fallback: try all spans with the right text
                    for (const span of allSpans) {
                        if (span.textContent.includes('View more comments') || 
                            span.textContent.includes('Previous comments')) {
                            const clickable = span.closest('div[role="button"]');
                            if (clickable) {
                                console.log("Found clickable via text content search");
                                clickable.scrollIntoView({behavior: "auto", block: "center"});
                                return humanClick(clickable);
                            }
                        }
                    }
                    
                    // Try direct role buttons that contain the text
                    const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                    for (const button of buttons) {
                        if (button.textContent.includes('View more comments') || 
                            button.textContent.includes('Previous comments')) {
                            console.log("Found direct button");
                            button.scrollIntoView({behavior: "auto", block: "center"});
                            return humanClick(button);
                        }
                    }
                    
                    return false;
                }''')

                if click_happened:
                    print("Clicked on 'View more comments' button")
                    total_clicks += 1
                    await asyncio.sleep(3)  # Reduced from 4
                    await page.wait_for_load_state('networkidle')
                else:
                    print("No more 'View more comments' buttons found")
                    
                    if total_clicks == 0 or attempts > 5:  # Reduced from 10
                        # If we haven't clicked anything or tried many times, break the loop
                        break
                
                attempts += 1
                
                # Add a comment count limit to avoid resource exhaustion
                if current_comment_count > 50:  # Limit to 50 comments to save resources
                    print("Reached comment limit to save resources")
                    break
            
            print(f"Made {total_clicks} clicks to expand comments")
            
            # Step 4: Scrape the comments
            comments = await page.evaluate('''() => {
                const comments = [];
                const commentElements = Array.from(document.querySelectorAll('div[role="article"]'));
                
                console.log("Total comment elements found:", commentElements.length);
                
                // Skip the first element as it's likely the post itself
                const actualComments = commentElements.slice(1);
                
                // Limit to 100 comments to save resources
                const limitedComments = actualComments.slice(0, 100);
                
                limitedComments.forEach((comment, index) => {
                    try {
                        // Extract the comment content
                        const contentElements = comment.querySelectorAll('div[dir="auto"]:not([style*="display: none"])');
                        let content = '';
                        
                        // Take the longest text content as the comment
                        contentElements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > content.length) {
                                content = text;
                            }
                        });
                        
                        // Extract the author name using various selectors to catch different FB layouts
                        let author = '';
                        
                        // First try: Look for the author name in specific class patterns
                        const authorElements = [
                            // Common desktop FB pattern - strong tag with author name
                            ...comment.querySelectorAll('strong.x1heor9g, strong.html-strong'),
                            // Mobile FB pattern - span with author class
                            ...comment.querySelectorAll('span.f20'),
                            // Another common pattern - profile link with author name
                            ...comment.querySelectorAll('a[role="link"] span.xt0psk2, a[aria-label*="profile"] span'),
                            // Alternative pattern - any link within header area
                            ...comment.querySelectorAll('h3 a, h4 a, .x1heor9g a, .x11i5rnm a')
                        ];
                        
                        // Try to extract author from the found elements
                        for (const el of authorElements) {
                            const name = el.textContent.trim();
                            if (name && name.length > 0 && name.length < 50) {
                                author = name;
                                break;
                            }
                        }
                        
                        // If no author found with specific selectors, try more general approach
                        if (!author) {
                            // Look for typical author layout patterns
                            const topElements = Array.from(comment.querySelectorAll('div[dir="auto"]')).slice(0, 3);
                            for (const el of topElements) {
                                const text = el.textContent.trim();
                                // Author names are typically short and at the beginning of the comment
                                if (text && text.length > 0 && text.length < 40 && 
                                    !text.includes("Commented") && !text.includes("replied") && 
                                    !text.includes("http") && !text.includes("www.")) {
                                    author = text;
                                    break;
                                }
                            }
                        }
                        
                        if (content) {
                        comments.push({
                            'comment': content,
                                'author': author || 'Unknown User',
                                'index': index
                        });
                        }
                    } catch (e) {
                        console.error('Error processing comment:', e);
                    }
                });

                return comments;
            }''')

            # Skip screenshot on Render to save disk space and memory
            # await page.screenshot(path='facebook_post_screenshot.png')

            formatted_data = {
                'post': {
                    'content': post_data['post_content'],
                    'url': post_data['post_url']
                },
                'comments': comments,
                'metadata': {
                    'total_comments': len(comments),
                    'scraped_at': datetime.now().isoformat(),
                    'clicks_to_expand': total_clicks
                }
            }

            # Close the browser
            await browser.close()

            return formatted_data

        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=f"Error scraping post: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)